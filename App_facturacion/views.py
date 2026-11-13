"""Consultas y movimientos reales de cobros; permisos por estilista y clienta."""
from datetime import date, datetime
from decimal import Decimal
from collections import defaultdict
from io import BytesIO

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Sum
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from App_agenda.models import Cita
from App_usuarios.decorators import role_required, rol_real
from .models import RegistroCobro, Pago, CierreCaja
from .servicios import obtener_cobro, registrar_pago


# Explicación: Consulta los cobros y saldos de la estilista autenticada.
@role_required('estilista')
def inventario_view(request):
    registros = RegistroCobro.objects.filter(
        cita__estilista__persona=request.user,
    ).select_related('cliente__persona','cita__servicio').prefetch_related('pagos').order_by('-fecha')
    return render(request, 'App_facturacion/E_inventario.html', {
        'registros': registros,
        'total_clientes': registros.values('cliente_id').distinct().count(),
        'total_pendiente': registros.exclude(cita__estado__in=['CANCELADA','RECHAZADA']).aggregate(
            total=Sum('saldo_pendiente'))['total'] or Decimal('0.00'),
    })


# Explicación: Valida los parámetros del intervalo usados en reportes.
def _filtrar_fechas(request):
    inicio_str = request.GET.get('fecha_inicio','').strip()
    fin_str = request.GET.get('fecha_fin','').strip()
    if not inicio_str and not fin_str:
        return inicio_str, fin_str, None, None, ''
    try:
        if not inicio_str or not fin_str:
            raise ValueError
        inicio = date.fromisoformat(inicio_str)
        fin = date.fromisoformat(fin_str)
        if inicio > fin:
            return inicio_str, fin_str, None, None, 'La fecha inicial no puede ser posterior a la final.'
        return inicio_str, fin_str, inicio, fin, ''
    except ValueError:
        return inicio_str, fin_str, None, None, 'Ingresa un rango válido con fecha inicial y fecha final.'


# Explicación: Integra pagos nuevos y pagos históricos para mantener los totales.
def _movimientos(registros):
    """Migración compatible: registros antiguos sin pagos se reportan por la fecha de cobro."""
    for r in registros:
        pagos = list(r.pagos.all())
        if not pagos and r.cita.estado in ('CANCELADA', 'RECHAZADA'):
            continue
        if pagos:
            for pago in pagos:
                yield timezone.localtime(pago.fecha).date(), pago.monto, r
            # Cobros antiguos con abonos previos a la incorporación de pagos.
            anterior = r.monto_pagado - sum((p.monto for p in pagos), Decimal('0.00'))
            if anterior > 0:
                yield r.fecha, anterior, r
        elif r.monto_pagado > 0:
            yield r.fecha, r.monto_pagado, r


# Explicación: RF-ES-013: ingresos, saldos y servicios más solicitados por la estilista.
@role_required('estilista')
def reportes_view(request):
    registros = RegistroCobro.objects.filter(cita__estilista__persona=request.user).select_related(
        'cliente__persona','cita__servicio').prefetch_related('pagos').order_by('-fecha')
    movimientos = list(_movimientos(registros))
    fecha_inicio, fecha_fin, inicio, fin, error_fechas = _filtrar_fechas(request)
    ingresos_mensuales = defaultdict(lambda: Decimal('0.00'))
    for fecha, monto, _ in movimientos:
        ingresos_mensuales[(fecha.year,fecha.month)] += monto
    meses = [{'mes': datetime(year, month, 1), 'ingresos': monto}
             for (year,month),monto in sorted(ingresos_mensuales.items())]
    periodo = None
    if inicio and fin:
        periodo = sum((monto for fecha,monto,_ in movimientos if inicio <= fecha <= fin), Decimal('0.00'))
    estados_validos = ('PENDIENTE','CONFIRMADA','EN_PROCESO','FINALIZADA')
    populares = Cita.objects.filter(estilista__persona=request.user, estado__in=estados_validos).values(
        'servicio__nombre').annotate(total=Count('pk')).order_by('-total','servicio__nombre')[:5]
    return render(request, 'App_facturacion/E_reportes.html', {
        'registros': registros,
        'total_ingresos': sum((monto for _,monto,_ in movimientos), Decimal('0.00')),
        'total_pendiente': registros.exclude(cita__estado__in=['CANCELADA','RECHAZADA']).aggregate(total=Sum('saldo_pendiente'))['total'] or Decimal('0.00'),
        'total_citas': Cita.objects.filter(estilista__persona=request.user,estado__in=estados_validos).count(),
        'servicios_populares': populares,
        'servicio_mas_popular': populares[0] if populares else None,
        'ingresos_mensuales': meses,
        'fecha_inicio': fecha_inicio, 'fecha_fin': fecha_fin,
        'error_fechas': error_fechas, 'total_periodo': periodo,
    })


# Explicación: RF-ES-012: registra un abono tras validar el monto y el método.
@role_required('estilista')
@require_POST
def registrar_pago_view(request, cita_id):
    cita = get_object_or_404(Cita, pk=cita_id, estilista__persona=request.user)
    try:
        registrar_pago(cita, request.POST.get('monto',''), request.POST.get('metodo',''),
                       request.user, request.POST.get('referencia',''))
    except ValidationError as exc:
        messages.error(request, ' '.join(exc.messages))
    else:
        messages.success(request, 'Pago registrado y saldo actualizado.')
    return redirect('App_facturacion:inventario')


# Explicación: Crea una liquidación solo para citas confirmadas o atendidas.
@role_required('estilista')
@require_POST
def crear_cobro_view(request, cita_id):
    cita = get_object_or_404(Cita, pk=cita_id, estilista__persona=request.user,
                             estado__in=('CONFIRMADA','EN_PROCESO','FINALIZADA'))
    obtener_cobro(cita)
    messages.success(request, 'Se creó o consultó el cobro de la cita.')
    return redirect('App_facturacion:inventario')


# Explicación: RF-CLI-017: presenta recibo únicamente al cliente, su estilista o administración.
def recibo_view(request, cita_id):
    if not request.user.is_authenticated:
        return redirect('App_usuarios:login')
    cita = get_object_or_404(Cita, pk=cita_id)
    if not (rol_real(request.user) == 'administrador' or
            (request.user.rol == 'cliente' and cita.cliente.persona_id == request.user.pk) or
            (request.user.rol == 'estilista' and cita.estilista.persona_id == request.user.pk)):
        raise Http404('Recibo no encontrado.')
    registro = RegistroCobro.objects.filter(cita=cita).prefetch_related('pagos').first()
    return render(request, 'App_facturacion/recibo.html', {'cita':cita,'registro':registro})


# Explicación: Consolida efectivo y transferencias recibidas, bloqueando pagos posteriores.
@role_required('estilista')
@require_POST
def cierre_caja_view(request):
    fecha = timezone.localdate()
    with transaction.atomic():
        if CierreCaja.objects.filter(fecha=fecha).exists():
            messages.info(request, 'La caja del día ya está cerrada.')
        else:
            pagos = Pago.objects.filter(recibido_por=request.user,fecha__date=fecha)
            efectivo = pagos.filter(metodo='EFECTIVO').aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
            transferencia = pagos.filter(metodo='TRANSFERENCIA').aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
            CierreCaja.objects.create(fecha=fecha,monto_efectivo=efectivo,
                                     monto_transferencia=transferencia,cerrado_por=request.user)
            messages.success(request, 'Cierre de caja registrado. No se permitirán más pagos hoy.')
    return redirect('App_facturacion:inventario')


# Explicación: Genera reportes de pago en Excel o PDF para la estilista dueña de los cobros.
@role_required('estilista')
def exportar_reporte_view(request, formato):
    if formato not in ('xlsx','pdf'):
        raise Http404
    regs = RegistroCobro.objects.filter(cita__estilista__persona=request.user).select_related(
        'cliente__persona','cita__servicio').order_by('fecha')
    inicio_str, fin_str, inicio, fin, error = _filtrar_fechas(request)
    if error:
        return HttpResponse(error,status=400)
    if inicio:
        regs = regs.filter(fecha__gte=inicio,fecha__lte=fin)
    columnas = ('Fecha', 'Clienta', 'Servicio', 'Estado', 'Total', 'Pagado', 'Saldo')
    filas = [(str(r.fecha), str(r.cliente), r.cita.servicio.nombre, r.cita.get_estado_display(),
              str(r.monto_total), str(r.monto_pagado), str(r.saldo_pendiente)) for r in regs]
    if formato == 'xlsx':
        import xlsxwriter
        salida = BytesIO()
        libro = xlsxwriter.Workbook(salida, {'in_memory':True})
        hoja = libro.add_worksheet('Cobros')
        encabezado = libro.add_format({'bold':True,'bg_color':'#800020','font_color':'white'})
        for i, titulo in enumerate(columnas):hoja.write(0,i,titulo,encabezado)
        moneda = libro.add_format({'num_format':'$#,##0.00'})
        for n,fila in enumerate(filas,1):
            for i,v in enumerate(fila):
                if i >= 4:
                    hoja.write_number(n,i,float(v),moneda)
                else:
                    hoja.write(n,i,v)
        hoja.set_column('A:A',15);hoja.set_column('B:D',26);hoja.set_column('E:G',15)
        hoja.freeze_panes(1,0)
        libro.close()
        contenido=salida.getvalue()
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    else:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from xml.sax.saxutils import escape
        salida=BytesIO()
        pdf=SimpleDocTemplate(salida, pagesize=landscape(A4), leftMargin=28,
                              rightMargin=28, topMargin=28, bottomMargin=28)
        estilos=getSampleStyleSheet()
        celda=estilos['BodyText']
        celda.fontSize=7
        celda.leading=9
        datos=[]
        for fila in (columnas,*filas):
            datos.append([Paragraph(escape(str(v)),celda) for v in fila])
        tabla=Table(datos, colWidths=[74,146,145,86,87,87,87], repeatRows=1, hAlign='LEFT')
        tabla.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#800020')),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('BOTTOMPADDING',(0,0),(-1,-1),6),
            ('TOPPADDING',(0,0),(-1,-1),6),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.whitesmoke,colors.white]),
            ('LINEBELOW',(0,0),(-1,0),1,colors.HexColor('#800020')),
        ]))
        pdf.build([Paragraph('Leidy Make Up - Reporte de cobros',estilos['Heading2']),
                   Spacer(1,12),tabla])
        contenido=salida.getvalue();content_type='application/pdf'
    resp=HttpResponse(contenido,content_type=content_type)
    resp['Content-Disposition']=f'attachment; filename="leidy-reporte.{formato}"'
    resp['Cache-Control']='private, no-store'
    return resp
