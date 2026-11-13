"""Gestión administrativa de Leidy Make Up.

Cada vista usa el decorador RBAC; un cliente o estilista no obtiene facultades
administrativas por cambiar un campo oculto o alterar la URL.
"""
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
import sqlite3
import tempfile
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from App_usuarios.decorators import role_required
from App_usuarios.models import Persona, Cliente, Estilista, HistorialAcceso
from App_agenda.forms import BloqueoAgendaForm, PoliticaAgendaForm, estilistas_disponibles
from App_agenda.models import Cita, CitaArchivo, Horario, BloqueoAgenda, ConfiguracionAgenda, Mensaje, BitacoraCita
from App_agenda.servicios import registrar_cambio
from App_servicios.models import Servicio
from App_facturacion.models import RegistroCobro, Pago, CierreCaja
from .forms import CuentaForm, ServicioAdministrativoForm


def _plantilla(request, pantalla, **extra):
    """Añade indicadores globales para que las secciones compartan navegación."""
    extra.setdefault('seccion',pantalla)
    return render(request, f'App_administracion/{pantalla}.html', extra)


@role_required('administrador')
def inicio(request):
    """RF-AD-008: resumen global sin limitar los datos a una estilista."""
    hoy=timezone.localdate()
    pagos=Pago.objects.all()
    # RF-AD-008: ocupación aproximada de hoy, basada en jornadas laborales activas.
    jornadas=Horario.objects.filter(dia_semana=hoy.weekday(),activo=True,
         estilista__persona__rol='estilista',estilista__persona__is_active=True)
    capacidad=sum((datetime.combine(hoy,h.hora_fin)-datetime.combine(hoy,h.hora_inicio)).total_seconds()/60 for h in jornadas)
    citas_hoy=Cita.objects.filter(fecha=hoy,estado__in=('CONFIRMADA','EN_PROCESO','FINALIZADA'))
    minutos=sum((c.duracion_aprobada or c.servicio.duracion) for c in citas_hoy.select_related('servicio'))
    ocupacion=round(min(100,100*minutos/capacidad),1) if capacidad else 0
    return _plantilla(request,'inicio',ocupacion=ocupacion, total_clientes=Cliente.objects.count(),
        total_estilistas=Estilista.objects.filter(persona__rol='estilista',persona__is_active=True).count(),
        total_citas=Cita.objects.count(),
        pendientes=Cita.objects.filter(estado='PENDIENTE').count(),
        ingresos_dia=pagos.filter(fecha__date=hoy).aggregate(v=Sum('monto'))['v'] or 0,
        ingresos_mes=pagos.filter(fecha__year=hoy.year,fecha__month=hoy.month).aggregate(v=Sum('monto'))['v'] or 0,
        populares=Cita.objects.values('servicio__nombre').annotate(total=Count('pk')).order_by('-total')[:5],
        citas=Cita.objects.select_related('cliente__persona','estilista__persona','servicio').order_by('-fecha_solicitud')[:15])


@role_required('administrador')
def usuarios(request):
    """RF-AD-001: directorio de cuentas de los tres roles."""
    return _plantilla(request,'usuarios',usuarios=Persona.objects.order_by('rol','first_name','username'))


def _guardar_usuario(form, instancia=None):
    """Persiste persona + perfil en una transacción indivisible."""
    datos=form.cleaned_data
    creado=instancia is None
    if creado:
        instancia=Persona(username=datos['email'])
    for campo in ('first_name','last_name','email','rol'):
        setattr(instancia,campo,datos[campo])
    # Solo administradores pueden acceder al Django admin interno.
    instancia.is_staff=datos['rol']=='administrador'
    if datos.get('password'):
        instancia.set_password(datos['password'])
    instancia.save()
    if datos['rol']=='cliente':
        Cliente.objects.update_or_create(persona=instancia,defaults={
            'telefono':datos['telefono'],'direccion':datos['direccion']})
        if hasattr(instancia,'estilista'):
            instancia.estilista.delete()
    elif datos['rol']=='estilista':
        Estilista.objects.update_or_create(persona=instancia,defaults={'especialidad':datos['especialidad']})
        if hasattr(instancia,'cliente'):
            instancia.cliente.delete()
    else:
        if hasattr(instancia,'cliente'): instancia.cliente.delete()
        if hasattr(instancia,'estilista'): instancia.estilista.delete()
    return instancia


@role_required('administrador')
def usuario_crear(request):
    """RF-AD-001: alta con email único, rol seguro y validación de contraseña."""
    form=CuentaForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            _guardar_usuario(form)
        messages.success(request,'Cuenta creada correctamente.')
        return redirect('App_administracion:usuarios')
    return _plantilla(request,'usuario_form',form=form,titulo='Crear cuenta')


@role_required('administrador')
def usuario_editar(request,pk):
    """RF-AD-001: la edición de cuentas antiguas conserva su identidad."""
    persona=get_object_or_404(Persona,pk=pk)
    form=CuentaForm(request.POST or None,instancia=persona)
    if request.method=='POST' and form.is_valid():
        if persona.pk==request.user.pk and form.cleaned_data['rol']!='administrador':
            form.add_error('rol','No puedes quitarte tu propio rol de administrador.')
        elif persona.is_superuser and form.cleaned_data['rol']!='administrador':
            form.add_error('rol','No puedes modificar el rol de un superusuario.')
        else:
            with transaction.atomic():
                _guardar_usuario(form,persona)
            messages.success(request,'Cuenta actualizada.')
            return redirect('App_administracion:usuarios')
    return _plantilla(request,'usuario_form',form=form,titulo='Editar cuenta',persona=persona)


@role_required('administrador')
@require_POST
def usuario_estado(request,pk):
    """Inhabilitar sin destruir historiales. Nunca bloquear la propia cuenta."""
    persona=get_object_or_404(Persona,pk=pk)
    if persona.pk==request.user.pk or persona.is_superuser:
        messages.error(request,'No puedes desactivar tu cuenta ni la de otro superusuario.')
    else:
        persona.is_active=not persona.is_active
        persona.save(update_fields=['is_active'])
        messages.success(request,'Estado de la cuenta actualizado.')
    return redirect('App_administracion:usuarios')


@role_required('administrador')
def servicios(request):
    """RF-AD-002/003: catálogo editable y desactivación lógica."""
    form=ServicioAdministrativoForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        form.save()
        messages.success(request,'Servicio creado.')
        return redirect('App_administracion:servicios')
    return _plantilla(request,'servicios',form=form,servicios=Servicio.objects.order_by('nombre'))


@role_required('administrador')
def servicio_editar(request,pk):
    """Actualizar el servicio manteniendo intactas sus citas relacionadas."""
    servicio=get_object_or_404(Servicio,pk=pk)
    form=ServicioAdministrativoForm(request.POST or None,instance=servicio)
    if request.method=='POST' and form.is_valid():
        form.save()
        messages.success(request,'Servicio actualizado.')
        return redirect('App_administracion:servicios')
    return _plantilla(request,'servicio_form',form=form,servicio=servicio)


@role_required('administrador')
@require_POST
def servicio_estado(request,pk):
    """RF-AD-003: nunca borrar citas al desactivar su servicio."""
    servicio=get_object_or_404(Servicio,pk=pk)
    servicio.activo=not servicio.activo
    servicio.save(update_fields=['activo'])
    return redirect('App_administracion:servicios')


@role_required('administrador')
def agenda(request):
    """RF-AD-004/005/007/013: agenda global, bloqueos y cambios de políticas."""
    citas=Cita.objects.select_related('servicio','cliente__persona','estilista__persona').order_by('-fecha','-hora_inicio')
    fecha=request.GET.get('fecha','').strip()
    if fecha:
        try:citas=citas.filter(fecha=date.fromisoformat(fecha))
        except ValueError:fecha=''
    return _plantilla(request,'agenda',citas=citas[:200],fecha=fecha,
        estilistas=Estilista.objects.filter(persona__rol='estilista',persona__is_active=True).select_related('persona'),
        bloqueos=BloqueoAgenda.objects.select_related('estilista__persona').order_by('-fecha_inicio')[:30],
        bloqueo_form=BloqueoAgendaForm(),
        politicas=ConfiguracionAgenda.objects.select_related('estilista__persona'))


@role_required('administrador')
@require_POST
def reasignar(request,pk):
    """RF-AD-005: reserva de plaza bajo bloqueo de transacción; jamás crear cruces."""
    with transaction.atomic():
        cita=get_object_or_404(Cita.objects.select_for_update(),pk=pk)
        nueva=get_object_or_404(Estilista.objects.select_for_update(),
            pk=request.POST.get('estilista_id'),persona__rol='estilista',persona__is_active=True)
        if cita.estado in ('FINALIZADA','CANCELADA','RECHAZADA'):
            messages.error(request,'No se puede reasignar una cita finalizada o cerrada.')
        elif cita.estilista_id==nueva.pk:
            messages.info(request,'La cita ya está asignada a esa estilista.')
        elif nueva not in estilistas_disponibles(cita.fecha,cita.hora_inicio,cita.servicio,
            estilistas=[nueva],excluir_cita_id=cita.pk):
            messages.error(request,'La estilista seleccionada no tiene disponibilidad.')
        else:
            previo=str(cita.estilista)
            cita.estilista=nueva
            cita.save(update_fields=['estilista'])
            registrar_cambio(cita,request.user,'REASIGNACION',cita.estado,detalle=f'De {previo} a {nueva}')
            messages.success(request,'Cita reasignada correctamente.')
    return redirect('App_administracion:agenda')


@role_required('administrador')
@require_POST
def bloquear(request):
    """RF-AD-007: permite bloquear una profesional o cerrar todas las agendas.

    La operación masiva es atómica: si una agenda tiene citas confirmadas en
    el rango, se rechaza el cierre completo antes de crear ningún bloqueo.
    """
    opcion = request.POST.get('estilista_id', '')
    form = BloqueoAgendaForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Revisa las fechas y el motivo del bloqueo.')
        return redirect('App_administracion:agenda')

    if opcion == 'todos':
        profesionales = list(Estilista.objects.filter(
            persona__rol='estilista', persona__is_active=True,
        ))
    else:
        profesionales = [get_object_or_404(
            Estilista, pk=opcion, persona__rol='estilista', persona__is_active=True,
        )]
    if not profesionales:
        messages.error(request, 'No hay estilistas activas para aplicar el cierre.')
        return redirect('App_administracion:agenda')

    inicio = form.cleaned_data['fecha_inicio']
    fin = form.cleaned_data['fecha_fin']
    if Cita.objects.filter(estilista__in=profesionales, fecha__range=(inicio, fin),
                           estado__in=('CONFIRMADA', 'EN_PROCESO')).exists():
        messages.error(request, 'No se puede bloquear: existen citas confirmadas o en proceso.')
        return redirect('App_administracion:agenda')

    # Todas las agendas se actualizan juntas o ninguna; la validación del
    # formulario impide rangos invertidos y guarda el mismo motivo en cada una.
    with transaction.atomic():
        for profesional in profesionales:
            BloqueoAgenda.objects.create(
                estilista=profesional, fecha_inicio=inicio, fecha_fin=fin,
                motivo=form.cleaned_data['motivo'],
            )
    messages.success(request, f'Bloqueo registrado en {len(profesionales)} agenda(s).')
    return redirect('App_administracion:agenda')


@role_required('administrador')
@require_POST
def politicas(request):
    """RF-AD-013: ajustes por estilista de anticipación y cancelación."""
    estilista=get_object_or_404(Estilista,pk=request.POST.get('estilista_id'))
    politica,_=ConfiguracionAgenda.objects.get_or_create(estilista=estilista)
    form=PoliticaAgendaForm(request.POST,instance=politica)
    if form.is_valid():
        form.save(); messages.success(request,'Políticas actualizadas.')
    else:
        messages.error(request,'Política inválida. Valores de 0 a 30 días.')
    return redirect('App_administracion:agenda')


@role_required('administrador')
def clientes(request):
    """RF-AD-006: directorio con historiales sin mostrar cuentas de otros roles."""
    registros=Cliente.objects.select_related('persona').annotate(
        numero_citas=Count('citas',distinct=True),canceladas=Count('citas',filter=Q(citas__estado='CANCELADA'))).order_by('persona__first_name')
    cliente_id=request.GET.get('cliente')
    detalle=get_object_or_404(registros,pk=cliente_id) if cliente_id else None
    citas=Cita.objects.filter(cliente=detalle).select_related('servicio','estilista__persona') if detalle else Cita.objects.none()
    return _plantilla(request,'clientes',clientes=registros,detalle=detalle,citas=citas)


def _reporte_base(request):
    """Filtra ingresos por periodo y profesional; devuelve error para fechas inválidas."""
    inicio=request.GET.get('desde','').strip()
    fin=request.GET.get('hasta','').strip()
    try:
        desde=date.fromisoformat(inicio) if inicio else None
        hasta=date.fromisoformat(fin) if fin else None
        if desde and hasta and desde>hasta: raise ValueError
    except ValueError:
        raise ValidationError('El rango de fechas no es válido.')
    registros=RegistroCobro.objects.select_related('cita__estilista__persona','cita__servicio','cliente__persona')
    if desde: registros=registros.filter(cita__fecha__gte=desde)
    if hasta: registros=registros.filter(cita__fecha__lte=hasta)
    estilista=request.GET.get('estilista','').strip()
    if estilista:
        if not estilista.isdigit(): raise ValidationError('Estilista inválida.')
        registros=registros.filter(cita__estilista_id=int(estilista))
    return registros, {'desde':inicio,'hasta':fin,'estilista':estilista}


@role_required('administrador')
def reportes(request):
    """RF-AD-009/011: ingresos, pagos y saldo, sin omitir registros de otras profesionales."""
    try:registros,filtros=_reporte_base(request)
    except ValidationError as err:
        return HttpResponseBadRequest(' '.join(err.messages))
    resumen=registros.aggregate(total=Sum('monto_total'),cobrado=Sum('monto_pagado'),saldo=Sum('saldo_pendiente'))
    return _plantilla(request,'reportes',registros=registros.order_by('-fecha')[:200],resumen=resumen,
        estilistas=Estilista.objects.select_related('persona'),**filtros)


@role_required('administrador')
def exportar(request,formato):
    """RF-AD-010: exportaciones reales Excel y PDF de los movimientos filtrados."""
    if formato not in ('xlsx','pdf'):raise Http404
    try:registros,_=_reporte_base(request)
    except ValidationError as err:return HttpResponseBadRequest(' '.join(err.messages))
    cabeceras=('Cita','Fecha','Cliente','Estilista','Servicio','Total','Abonado','Saldo')
    rows=[(r.cita_id,str(r.cita.fecha),str(r.cliente),str(r.cita.estilista),
           r.cita.servicio.nombre,str(r.monto_total),str(r.monto_pagado),str(r.saldo_pendiente)) for r in registros]
    out=BytesIO()
    if formato=='xlsx':
        import xlsxwriter
        libro=xlsxwriter.Workbook(out,{'in_memory':True});hoja=libro.add_worksheet('Ingresos')
        h=libro.add_format({'bold':True,'bg_color':'#9d174d','font_color':'white'})
        for c,v in enumerate(cabeceras):hoja.write(0,c,v,h)
        for r,linea in enumerate(rows,1):
            for c,val in enumerate(linea):
                hoja.write_number(r,c,float(val)) if c in (0,5,6,7) else hoja.write(r,c,val)
        hoja.set_column('A:H',23);hoja.freeze_panes(1,0);libro.close()
        tipo='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    else:
        from reportlab.lib.pagesizes import landscape,A4
        from reportlab.platypus import SimpleDocTemplate,Table,TableStyle
        from reportlab.lib import colors
        doc=SimpleDocTemplate(out,pagesize=landscape(A4));data=[cabeceras]+rows
        tabla=Table([[str(v)[:50] for v in linea] for linea in data],repeatRows=1)
        tabla.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.pink),('GRID',(0,0),(-1,-1),0.3,colors.grey),('FONTSIZE',(0,0),(-1,-1),7)]))
        doc.build([tabla]);tipo='application/pdf'
    res=HttpResponse(out.getvalue(),content_type=tipo)
    res['Content-Disposition']=f'attachment; filename="leidy_administracion.{formato}"'
    res['Cache-Control']='private, no-store'
    return res


@role_required('administrador')
def auditoria(request):
    """RF-AD-012: bitácora de cambios de cita e historial de inicio de sesión."""
    return _plantilla(request,'auditoria',eventos=BitacoraCita.objects.select_related('persona','cita')[:200],
                      accesos=HistorialAcceso.objects.select_related('persona')[:200])


@role_required('administrador')
def mensajes_admin(request):
    """RF-AD-015: mensajes de soporte con clientes; la estilista usa su módulo propio."""
    clientes=Cliente.objects.select_related('persona').order_by('persona__first_name')
    persona_id=request.POST.get('cliente_id') or request.GET.get('cliente')
    contacto=get_object_or_404(Persona,pk=persona_id,rol='cliente') if persona_id else None
    if request.method=='POST' and contacto:
        contenido=request.POST.get('contenido','').strip()
        if not 1<=len(contenido)<=2000:
            messages.error(request,'El mensaje debe tener entre 1 y 2000 caracteres.')
        else:
            Mensaje.objects.create(remitente=request.user,destinatario=contacto,contenido=contenido)
            return redirect('App_administracion:mensajes')
    msgs=Mensaje.objects.filter(Q(remitente=request.user,destinatario=contacto)|Q(remitente=contacto,destinatario=request.user)).order_by('creado_en') if contacto else Mensaje.objects.none()
    return _plantilla(request,'mensajes',clientes=clientes,contacto=contacto,mensajes=msgs)


@role_required('administrador')
def archivos(request):
    """RF-AD-016: ver adjuntos mediante la descarga autenticada, no servir MEDIA_ROOT."""
    return _plantilla(request,'archivos',archivos=CitaArchivo.objects.select_related('cita__cliente__persona','cita__servicio').order_by('-creado_en')[:150])


@role_required('administrador')
def caja(request):
    """RF-AD-017: saldos y cierres por día. Las estilistas solo registran pagos."""
    hoy=timezone.localdate()
    movimientos=Pago.objects.filter(fecha__date=hoy)
    total=movimientos.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    return _plantilla(request,'caja',pagos=movimientos[:100],total=total,
        cierre=CierreCaja.objects.filter(fecha=hoy).first(),cierres=CierreCaja.objects.order_by('-fecha')[:30])


@role_required('administrador')
@require_POST
def cerrar_caja(request):
    """Un único cierre consolidado; bloquea nuevos pagos si ya fue cerrado."""
    hoy=timezone.localdate()
    with transaction.atomic():
        if CierreCaja.objects.select_for_update().filter(fecha=hoy).exists():
            messages.error(request,'La caja del día ya está cerrada.')
        else:
            pagos=Pago.objects.filter(fecha__date=hoy)
            efectivo=pagos.filter(metodo='EFECTIVO').aggregate(v=Sum('monto'))['v'] or 0
            transferencia=pagos.filter(metodo='TRANSFERENCIA').aggregate(v=Sum('monto'))['v'] or 0
            CierreCaja.objects.create(fecha=hoy,monto_efectivo=efectivo,monto_transferencia=transferencia,cerrado_por=request.user)
            messages.success(request,'Cierre de caja consolidado.')
    return redirect('App_administracion:caja')


@role_required('administrador')
@require_POST
def respaldar(request):
    """RF-AD-018: descarga de copia consistente SQLite, solo para administradores."""
    db=settings.DATABASES['default']
    if db['ENGINE']!='django.db.backends.sqlite3':
        return HttpResponseBadRequest('Para PostgreSQL configure copias de seguridad en el servidor.')
    # Una base en memoria está controlada por la transacción de pruebas y no se descarga.
    if str(db['NAME']).startswith('file:memory') or str(db['NAME']) == ':memory:':
        return HttpResponseBadRequest('Respaldo disponible únicamente con una base SQLite persistente.')
    with tempfile.TemporaryDirectory() as td:
        destino=Path(td)/'leidy_respaldo.sqlite3'
        with sqlite3.connect(str(db['NAME'])) as origen, sqlite3.connect(str(destino)) as copia:
            origen.backup(copia)
        datos=destino.read_bytes()
    res=HttpResponse(datos,content_type='application/octet-stream')
    res['Content-Disposition']=f'attachment; filename="leidy_respaldo_{timezone.localdate()}.sqlite3"'
    res['Cache-Control']='no-store'
    return res


@role_required('administrador')
def ayuda(request):
    """RF-AD-014: manual operativo para el administrador, sin divulgar secretos."""
    return _plantilla(request,'ayuda')
