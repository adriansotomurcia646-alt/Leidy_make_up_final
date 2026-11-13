from datetime import date, datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Q, Sum
from django.db.models.functions import Coalesce
from django.http import FileResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from App_usuarios.decorators import role_required, rol_real
from App_usuarios.models import Cliente, Estilista
from App_servicios.models import Servicio
from .forms import (
    ReservarCitaForm,
    estilistas_disponibles,
    franjas_horarias,
)
from .models import Cita, CitaArchivo, Mensaje, BloqueoAgenda, Notificacion, BitacoraCita
from .servicios import registrar_evento, registrar_cambio, notificar

ALLOWED_UPLOAD_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.pdf', '.mp4', '.webm'}
UPLOAD_MIME_TYPES_BY_EXTENSION = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.webp': 'image/webp',
    '.pdf': 'application/pdf',
    '.mp4': 'video/mp4',
    '.webm': 'video/webm',
}


# Explicación: Unifica nombres históricos de estados para no crear transiciones inconsistentes.
def _estado_normalizado(estado):
    mapping = {'ACEPTADA': 'CONFIRMADA', 'APROBADA': 'CONFIRMADA', 'FINALIZADA': 'FINALIZADA'}
    return mapping.get(str(estado).upper(), str(estado).upper())


# Explicación: Devuelve el estado persistido y evita finalizar una cita solo por el paso del tiempo.
def _estado_visual(cita):
    return cita.estado


# Explicación: Verifica extensión, peso, MIME y firma antes de aceptar referencias de citas.
def _validar_adjuntos(archivos):
    for archivo in archivos or []:
        if archivo is None or getattr(archivo, 'size', 0) == 0:
            continue
        nombre = archivo.name or 'adjunto'
        extension = f".{nombre.rsplit('.', 1)[-1].lower()}" if '.' in nombre else ''
        if extension not in ALLOWED_UPLOAD_EXTENSIONS:
            raise ValueError('Tipo de archivo no permitido.')
        if archivo.size > 5 * 1024 * 1024:
            raise ValueError('El archivo supera el tamaño máximo permitido (5 MB).')
        mime_type = archivo.content_type or ''
        if mime_type and mime_type != UPLOAD_MIME_TYPES_BY_EXTENSION[extension]:
            raise ValueError('El tipo de contenido no coincide con la extensión del archivo.')
        header = archivo.read(12)
        archivo.seek(0)
        firma_valida = {
            '.jpg': header.startswith(b'\xff\xd8\xff'),
            '.jpeg': header.startswith(b'\xff\xd8\xff'),
            '.png': header.startswith(b'\x89PNG\r\n\x1a\n'),
            '.webp': header.startswith(b'RIFF') and header[8:12] == b'WEBP',
            '.pdf': header.startswith(b'%PDF-'),
            '.mp4': len(header) >= 8 and header[4:8] == b'ftyp',
            '.webm': header.startswith(b'\x1a\x45\xdf\xa3'),
        }[extension]
        if not firma_valida:
            raise ValueError('El contenido del archivo no corresponde al tipo permitido.')


# Explicación: Almacena archivos vinculados a la cita, con nombres validados y formatos permitidos.
def _guardar_adjuntos(cita, archivos):
    for archivo in archivos or []:
        if archivo is None or getattr(archivo, 'size', 0) == 0:
            continue
        nombre = archivo.name or 'adjunto'
        safe_name = default_storage.get_valid_name(nombre)
        safe_name = default_storage.get_available_name(safe_name)
        registro = CitaArchivo(cita=cita, nombre_original=nombre,
                               tipo=(archivo.content_type or '').split('/')[-1]
                               or nombre.rsplit('.', 1)[-1].lower())
        if safe_name.lower().endswith(('.jpg','.jpeg','.png','.webp')):
            try:
                from PIL import Image, ImageOps
                from django.core.files.base import ContentFile
                from io import BytesIO
                archivo.seek(0)
                imagen = ImageOps.exif_transpose(Image.open(archivo))
                imagen.thumbnail((1600, 1600))
                formato = 'JPEG' if safe_name.lower().endswith(('.jpg','.jpeg')) else ('WEBP' if safe_name.lower().endswith('.webp') else 'PNG')
                if formato == 'JPEG': imagen = imagen.convert('RGB')
                salida = BytesIO()
                imagen.save(salida, format=formato, optimize=True, quality=84)
                if salida.tell() < archivo.size:
                    archivo = ContentFile(salida.getvalue(), name=safe_name)
                else:
                    archivo.seek(0)
            except (OSError, ValueError):
                # Archivos heredados: la validación de firma se hizo al subir.
                archivo.seek(0)
        if safe_name.lower().endswith(('.jpg','.jpeg','.png','.webp')):
            try:
                from PIL import Image, ImageOps
                from django.core.files.base import ContentFile
                from io import BytesIO
                archivo.seek(0)
                imagen = ImageOps.exif_transpose(Image.open(archivo))
                imagen.thumbnail((1600, 1600))
                formato = 'JPEG' if safe_name.lower().endswith(('.jpg','.jpeg')) else ('WEBP' if safe_name.lower().endswith('.webp') else 'PNG')
                if formato == 'JPEG': imagen = imagen.convert('RGB')
                salida = BytesIO()
                imagen.save(salida, format=formato, optimize=True, quality=84)
                if salida.tell() < archivo.size:
                    archivo = ContentFile(salida.getvalue(), name=safe_name)
                else:
                    archivo.seek(0)
            except (OSError, ValueError):
                # Archivos heredados: la validación de firma se hizo al subir.
                archivo.seek(0)
        registro.archivo.save(safe_name, archivo, save=True)

# Explicación: RF-CLI-008: valida disponibilidad dentro de una transacción y crea una solicitud en espera.
def reservar_cita_view(request):
    if request.user.is_authenticated and (
        request.user.rol != 'cliente'
        or request.user.is_staff
        or request.user.is_superuser
    ):
        return HttpResponseForbidden('No tienes permiso para solicitar citas como cliente.')
    if request.method == 'POST' and not request.user.is_authenticated:
        request.session['booking_draft'] = {
            'servicio_id': request.POST.get('servicio_id', '')[:20],
            'fecha': request.POST.get('fecha', '')[:10],
            'hora': request.POST.get('hora', '')[:20],
            **({'estilista_id': request.POST['estilista_id'][:15]} if request.POST.get('estilista_id') else {}),
        }
        messages.warning(
            request,
            'Inicia sesión como cliente para enviar la solicitud. '
            'Conservamos el servicio, la fecha y el horario seleccionados.',
        )
        return redirect_to_login(request.get_full_path())

    draft = {}
    if request.user.is_authenticated and request.method == 'GET':
        draft = request.session.pop('booking_draft', {})
    selected_service_id = (
        request.POST.get('servicio_id')
        or request.POST.get('servicio')
        or request.GET.get('servicio')
        or draft.get('servicio_id')
    )
    selected_date = request.POST.get('fecha') or draft.get('fecha', '')
    selected_time = request.POST.get('hora') or request.POST.get('hora_inicio') or draft.get('hora', '')
    selected_stylist_id = request.POST.get('estilista_id') or draft.get('estilista_id', '')
    form = ReservarCitaForm(
        request.POST or None,
        request.FILES or None,
        initial={
            'servicio': selected_service_id,
            'fecha': selected_date,
            'hora_inicio': selected_time,
        },
    )
    servicios = Servicio.objects.all().filter(activo=True).order_by('nombre')
    form.fields['servicio'].queryset = servicios
    if request.method == 'POST' and form.is_valid():
        cliente, _ = Cliente.objects.get_or_create(persona=request.user)
        fecha = form.cleaned_data['fecha']
        hora_inicio = form.cleaned_data['hora_inicio']
        servicio = form.cleaned_data['servicio']
        archivos = request.FILES.getlist('adjuntos')
        try:
            _validar_adjuntos(archivos)
        except ValueError as exc:
            form.add_error(None, str(exc))
        else:
            with transaction.atomic():
                estilistas = list(
                    Estilista.objects.select_for_update()
                    .filter(persona__rol='estilista', persona__is_active=True)
                    .order_by('pk')
                )
                servicio = Servicio.objects.filter(
                    pk=servicio.pk,
                    activo=True,
                ).first()
                # RF-CLI-008: una profesional preferida debe existir y estar disponible.
                if selected_stylist_id:
                    estilistas = [e for e in estilistas if str(e.pk) == str(selected_stylist_id)]
                disponibles = estilistas_disponibles(
                    fecha, hora_inicio, servicio, estilistas
                ) if servicio else []
                duplicada = Cita.objects.filter(
                    cliente=cliente,
                    servicio=servicio,
                    fecha=fecha,
                    hora_inicio=hora_inicio,
                    estado__in=('PENDIENTE', 'CONFIRMADA', 'EN_PROCESO'),
                ).exists()
                if duplicada:
                    form.add_error(
                        None,
                        'Ya existe una solicitud para ese servicio, fecha y horario.',
                    )
                elif not disponibles:
                    form.add_error(
                        'hora_inicio',
                        'Ese horario ya no está disponible. Elige otro horario.',
                    )
                else:
                    cita = form.save(commit=False)
                    cita.cliente = cliente
                    cita.estilista = disponibles[0]
                    cita.fecha_solicitada = form.cleaned_data.get('fecha_solicitada') or fecha
                    cita.hora_solicitada = form.cleaned_data.get('hora_solicitada') or hora_inicio
                    cita.estado = 'PENDIENTE'
                    cita.save()
                    _guardar_adjuntos(cita, archivos)
                    registrar_evento(cita, request.user, 'SOLICITUD', '', cita.estado)
                    notificar(cita.estilista.persona, 'Nueva solicitud de cita', f'{servicio.nombre}: {fecha:%d/%m/%Y} {hora_inicio:%H:%M}', cita)
                    messages.success(
                        request,
                        f'Tu solicitud para {servicio.nombre} el {fecha:%d/%m/%Y} '
                        f'a las {hora_inicio:%H:%M} se envió correctamente y está '
                        'pendiente de confirmación.',
                    )
                    return redirect('App_agenda:c_mis_citas')
    return render(
        request,
        'App_agenda/C_reservar_cita.html',
        {
            'servicios': servicios,
            'form': form,
            'hoy': timezone.localdate(),
            'cliente': (
                Cliente.objects.filter(persona=request.user).first()
                if request.user.is_authenticated
                else None
            ),
            'selected_service_id': selected_service_id or '',
            'selected_date': selected_date,
            'selected_time': selected_time,
            'selected_stylist_id': selected_stylist_id,
            'estilistas': Estilista.objects.filter(persona__rol='estilista',persona__is_active=True).select_related('persona').order_by('persona__first_name'),
            'mensaje_previo': request.POST.get('mensaje', ''),
            'booking_draft_restored': bool(draft),
        },
    )


# Explicación: RF-VI-003: responde franjas libres/ocupadas al visitante sin permitir reservas anónimas.
def disponibilidad_reserva_view(request):
    if request.user.is_authenticated and (
        request.user.rol != 'cliente'
        or request.user.is_staff
        or request.user.is_superuser
    ):
        return HttpResponseForbidden('No tienes permiso para consultar reservas de clientes.')
    try:
        fecha = date.fromisoformat(request.GET.get('fecha', ''))
        servicio_id = request.GET.get('servicio_id')
        servicio = Servicio.objects.get(pk=servicio_id, activo=True)
    except (TypeError, ValueError, Servicio.DoesNotExist):
        return JsonResponse({'error': 'Selecciona un servicio y una fecha válidos.'}, status=400)
    if fecha < timezone.localdate():
        return JsonResponse({'error': 'La fecha no puede estar en el pasado.'}, status=400)
    # La consulta pública puede filtrarse por estilista sin exponer información privada.
    estilista_id=request.GET.get('estilista_id','').strip()
    estilistas=None
    if estilista_id:
        estilistas=list(Estilista.objects.filter(pk=estilista_id,persona__rol='estilista',persona__is_active=True)) if estilista_id.isdecimal() else []
    slots = franjas_horarias(fecha, servicio, estilistas=estilistas)
    return JsonResponse({
        'slots': [
            {
                'value': slot['hora'].strftime('%H:%M'),
                'label': slot['hora'].strftime('%I:%M %p').lstrip('0'),
                'estado': slot['estado'],
                'disponible': slot['disponible'],
                'motivo': slot['motivo'],
            }
            for slot in slots
        ],
    })


# Explicación: RF-CLI-010: limita el historial a las citas del cliente autenticado.
@role_required('cliente')
def mis_citas_view(request):
    cliente, _ = Cliente.objects.get_or_create(persona=request.user)
    citas = Cita.objects.filter(cliente=cliente).select_related(
        'servicio', 'estilista__persona'
    ).order_by('-fecha', '-hora_inicio')
    return render(request, 'App_agenda/C_mis_citas.html', {'citas': citas})


# Explicación: RF-CLI-011: aplica la anticipación mínima y registra el cambio de estado.
@role_required('cliente')
@require_POST
def cancelar_cita_view(request, cita_id):
    cliente, _ = Cliente.objects.get_or_create(persona=request.user)
    with transaction.atomic():
        cita = get_object_or_404(Cita.objects.select_for_update(), pk=cita_id, cliente=cliente)
        if not cita.puede_cancelar:
            messages.error(request, 'Solo puedes cancelar citas pendientes o confirmadas con al menos 2 horas de anticipación (o el plazo configurado por el salón).')
            return redirect('App_agenda:c_mis_citas')
        anterior = cita.estado
        cita.estado = 'CANCELADA'
        cita.save(update_fields=['estado'])
        registrar_cambio(cita, request.user, 'CANCELACION', anterior, 'Cancelación solicitada por la clienta.')
        notificar(cita.estilista.persona, 'Cita cancelada', f'{cita.servicio.nombre}: {cita.fecha:%d/%m/%Y} {cita.hora_inicio:%H:%M}', cita)
    messages.success(request, f'La cita de {cita.servicio.nombre} del {cita.fecha:%d/%m/%Y} a las {cita.hora_inicio:%H:%M} fue cancelada.')
    return redirect('App_agenda:c_mis_citas')


# Explicación: RF-CLI-012: acepta reprogramación solo de pendientes y comprueba conflictos.
@role_required('cliente')
@require_POST
def reprogramar_cita_view(request, cita_id):
    """Solo citas pendientes: recalcula duración y vuelve a validar el horario."""
    from datetime import date as fecha_cls, time as hora_cls
    cliente, _ = Cliente.objects.get_or_create(persona=request.user)
    try:
        fecha = fecha_cls.fromisoformat(request.POST.get('fecha', ''))
        hora = hora_cls.fromisoformat(request.POST.get('hora_inicio', ''))
    except (TypeError, ValueError):
        messages.error(request, 'Indica una fecha y una hora válidas.')
        return redirect('App_agenda:c_mis_citas')
    with transaction.atomic():
        cita = get_object_or_404(Cita.objects.select_for_update(), pk=cita_id, cliente=cliente)
        if not cita.puede_reprogramar:
            messages.error(request, 'Solo puedes reprogramar solicitudes pendientes que cumplan la anticipación de cancelación.')
            return redirect('App_agenda:c_mis_citas')
        estilista = Estilista.objects.select_for_update().get(pk=cita.estilista_id)
        if estilista not in estilistas_disponibles(fecha, hora, cita.servicio, [estilista], excluir_cita_id=cita.pk):
            messages.error(request, 'La fecha y hora seleccionadas no están disponibles.')
            return redirect('App_agenda:c_mis_citas')
        anterior = f'{cita.fecha.isoformat()} {cita.hora_inicio.isoformat()}'
        cita.fecha, cita.hora_inicio = fecha, hora
        cita.fecha_solicitada, cita.hora_solicitada = fecha, hora
        cita.duracion_aprobada = cita.servicio.duracion
        cita.save(update_fields=['fecha','hora_inicio','fecha_solicitada','hora_solicitada','duracion_aprobada'])
        registrar_evento(cita, request.user, 'REPROGRAMACION', 'PENDIENTE', 'PENDIENTE',
                         f'{anterior} -> {fecha.isoformat()} {hora.isoformat()}')
        notificar(estilista.persona, 'Solicitud reprogramada', f'{cita.servicio.nombre}: {fecha:%d/%m/%Y} {hora:%H:%M}', cita)
    messages.success(request, 'La solicitud fue reprogramada y sigue en espera de confirmación.')
    return redirect('App_agenda:c_mis_citas')


# Explicación: Sirve adjuntos de manera privada según propiedad de cliente, estilista o administrador.
def descargar_adjunto_view(request, archivo_id):
    if not request.user.is_authenticated:
        return redirect('App_usuarios:login')
    archivos = CitaArchivo.objects.select_related(
        'cita__cliente__persona', 'cita__estilista__persona'
    )
    if rol_real(request.user) == 'estilista':
        estilista, _ = Estilista.objects.get_or_create(persona=request.user)
        archivos = archivos.filter(cita__estilista=estilista)
    elif rol_real(request.user) == 'cliente':
        archivos = archivos.filter(cita__cliente__persona=request.user)
    elif rol_real(request.user) == 'administrador':
        pass  # RF-AD-016: administra los adjuntos sin ser propietario de una cita.
    else:
        archivos = archivos.none()
    adjunto = get_object_or_404(archivos, pk=archivo_id)
    response = FileResponse(
        adjunto.archivo.open('rb'),
        as_attachment=True,
        filename=adjunto.nombre_original or adjunto.archivo.name.rsplit('/', 1)[-1],
    )
    response['X-Content-Type-Options'] = 'nosniff'
    return response


# Explicación: RF-CLI-014: conversación de la clienta con su estilista asignada.
@role_required('cliente')
def mensajes_cliente_view(request):
    cliente = Cliente.objects.filter(persona=request.user).first()
    estilistas_asociadas = Estilista.objects.none()
    if cliente:
        estilistas_asociadas = Estilista.objects.filter(
            citas__cliente=cliente
        ).distinct()

    conversacion = Mensaje.objects.filter(
        Q(remitente=request.user, destinatario__rol='estilista')
        | Q(remitente=request.user, destinatario__is_staff=True)
        | Q(remitente=request.user, destinatario__is_superuser=True)
        | Q(destinatario=request.user, remitente__rol='estilista')
        | Q(destinatario=request.user, remitente__is_staff=True)
        | Q(destinatario=request.user, remitente__is_superuser=True)
    ).order_by('-creado_en').first()
    contacto = None
    if conversacion:
        destinatario_id = (
            conversacion.destinatario_id
            if conversacion.remitente_id == request.user.pk
            else conversacion.remitente_id
        )
        contacto = Estilista.objects.filter(persona_id=destinatario_id).select_related(
            'persona'
        ).first()
    elif estilistas_asociadas.count() == 1:
        contacto = estilistas_asociadas.select_related('persona').first()
    else:
        estilistas = Estilista.objects.filter(
            persona__rol='estilista'
        ).select_related('persona')
        if estilistas.count() == 1:
            contacto = estilistas.first()

    if request.method == 'POST' and contacto:
        contenido = request.POST.get('contenido', '').strip()
        if not contenido or len(contenido) > 2000:
            messages.error(request, 'El mensaje debe tener entre 1 y 2000 caracteres.')
        else:
            Mensaje.objects.create(
                remitente=request.user,
                destinatario=contacto.persona,
                contenido=contenido,
                cita=Cita.objects.filter(
                    cliente=cliente, estilista=contacto,
                ).order_by('-fecha', '-hora_inicio').first(),
            )
            messages.success(request, 'Tu mensaje se envió correctamente.')
            return redirect('App_agenda:c_mensajes')
    elif request.method == 'POST':
        messages.error(
            request,
            'No se pudo determinar una estilista destinataria para tu mensaje.',
        )

    mensajes = Mensaje.objects.none()
    if contacto:
        respuesta_posterior = Mensaje.objects.filter(
            remitente=contacto.persona,
            destinatario=request.user,
            creado_en__gt=OuterRef('creado_en'),
        )
        mensajes = Mensaje.objects.filter(
            Q(remitente=request.user, destinatario=contacto.persona)
            | Q(remitente=contacto.persona, destinatario=request.user)
        ).annotate(
            tiene_respuesta=Exists(respuesta_posterior),
        ).select_related('remitente', 'destinatario')
        mensajes.filter(destinatario=request.user, leido=False).update(leido=True)
    return render(
        request,
        'App_agenda/C_mensajes.html',
        {'contacto': contacto, 'mensajes': mensajes},
    )


# Explicación: Muestra indicadores y datos permitidos para el panel de la estilista.
@role_required('estilista')
def inicio_estilista_view(request):
    estilista, _ = Estilista.objects.get_or_create(persona=request.user)
    citas = Cita.objects.filter(estilista=estilista)
    citas_hoy = citas.filter(
        fecha=timezone.localdate(),
        estado='CONFIRMADA',
    ).select_related(
        'cliente__persona', 'servicio'
    ).order_by('hora_inicio')
    duracion_minutos = citas_hoy.aggregate(
        total=Sum(Coalesce('duracion_aprobada', 'servicio__duracion')),
    )['total'] or 0
    horas, minutos = divmod(duracion_minutos, 60)
    context = {
        'total_pendientes': citas.filter(estado='PENDIENTE').count(),
        'total_confirmadas': citas.filter(estado='CONFIRMADA').count(),
        'citas_hoy': citas_hoy,
        'citas_hoy_count': citas_hoy.count(),
        'horarios_ocupados': f'{horas} h {minutos} min',
    }
    return render(request, 'App_agenda/E_inicio.html', context)


# Explicación: RF-ES-005: lista las solicitudes de citas de la estilista autenticada.
@role_required('estilista')
def solicitudes_view(request):
    estilista, _ = Estilista.objects.get_or_create(persona=request.user)
    estado = request.GET.get('estado', 'PENDIENTE').upper()
    solicitudes = Cita.objects.filter(estilista=estilista)
    if estado in dict(Cita.ESTADOS):
        solicitudes = solicitudes.filter(estado=estado)
    elif estado != 'TODAS':
        estado = 'PENDIENTE'
        solicitudes = solicitudes.filter(estado=estado)
    solicitudes = solicitudes.select_related(
        'cliente__persona', 'servicio'
    ).order_by('fecha', 'hora_inicio')
    return render(
        request,
        'App_agenda/E_solicitudes.html',
        {'citas': solicitudes, 'solicitudes': solicitudes, 'estado_seleccionado': estado},
    )


# Explicación: RF-ES-006/007: confirma o rechaza solicitudes, audita y notifica al cliente.
@role_required('estilista')
@require_POST
def actualizar_solicitud_view(request, cita_id, estado):
    estado = _estado_normalizado(estado)
    if estado not in ('CONFIRMADA', 'RECHAZADA'):
        messages.error(request, 'El estado solicitado no es válido.')
        return redirect('App_agenda:e_solicitudes')

    estilista, _ = Estilista.objects.get_or_create(persona=request.user)
    with transaction.atomic():
        cita = get_object_or_404(
            Cita.objects.select_for_update(),
            pk=cita_id,
            estilista=estilista,
            estado='PENDIENTE',
        )
        if estado == 'CONFIRMADA':
            if cita.inicio_local <= timezone.now() or BloqueoAgenda.objects.filter(estilista=estilista, fecha_inicio__lte=cita.fecha, fecha_fin__gte=cita.fecha).exists():
                messages.error(request, 'No se puede confirmar una cita vencida o en un día bloqueado.')
                return redirect('App_agenda:e_solicitudes')
            overlap = Cita.objects.filter(
                estilista=estilista,
                fecha=cita.fecha,
                estado__in=('PENDIENTE', 'CONFIRMADA', 'EN_PROCESO'),
                hora_inicio__lt=cita.hora_fin,
                hora_fin__gt=cita.hora_inicio,
            ).exclude(pk=cita.pk).exists()
            if overlap:
                messages.error(
                    request,
                    'Ese horario ya fue ocupado por otra solicitud. Elige otro horario.',
                )
                return redirect('App_agenda:e_solicitudes')
        anterior = cita.estado
        cita.estado = estado
        if cita.duracion_aprobada is None:
            duracion_guardada = (
                datetime.combine(cita.fecha, cita.hora_fin)
                - datetime.combine(cita.fecha, cita.hora_inicio)
            )
            cita.duracion_aprobada = max(
                1,
                int(duracion_guardada.total_seconds() // 60),
            )
        if estado == 'CONFIRMADA':
            cita.fecha_aceptacion = timezone.now()
            if cita.fecha_solicitada is None:
                cita.fecha_solicitada = cita.fecha
            if cita.hora_solicitada is None:
                cita.hora_solicitada = cita.hora_inicio
        cita.save(update_fields=['estado', 'duracion_aprobada', 'fecha_aceptacion', 'fecha_solicitada', 'hora_solicitada'])
        registrar_cambio(cita, request.user, 'GESTION_SOLICITUD', anterior, request.POST.get('motivo','')[:500])
        if estado == 'CONFIRMADA':
            from App_facturacion.servicios import obtener_cobro
            obtener_cobro(cita)
    if estado == 'CONFIRMADA':
        messages.success(
            request,
            f'Cita confirmada: {cita.servicio.nombre} el {cita.fecha:%d/%m/%Y} '
            f'a las {cita.hora_inicio:%H:%M}.',
        )
    else:
        messages.success(
            request,
            f'La solicitud de {cita.servicio.nombre} para el '
            f'{cita.fecha:%d/%m/%Y} a las {cita.hora_inicio:%H:%M} fue rechazada.',
        )
    return redirect('App_agenda:e_solicitudes')


# Explicación: Valida la fecha consultada y define un valor alternativo si falla.
def _calendar_date(value, fallback):
    if not value:
        return fallback, ''
    try:
        return date.fromisoformat(value), ''
    except (TypeError, ValueError):
        return fallback, 'La fecha indicada no es válida.'


# Explicación: Calcula el intervalo diario, semanal o mensual para el calendario.
def _calendar_range(fecha, vista):
    if vista == 'dia':
        return fecha, fecha
    if vista == 'semana':
        inicio = fecha - timedelta(days=fecha.weekday())
        return inicio, inicio + timedelta(days=6)
    inicio = fecha.replace(day=1)
    siguiente_mes = (
        date(inicio.year + 1, 1, 1)
        if inicio.month == 12
        else date(inicio.year, inicio.month + 1, 1)
    )
    return inicio, siguiente_mes - timedelta(days=1)


# Explicación: Genera los eventos de calendario según el rol y sus permisos.
def _calendar_payload(request, stylist):
    hoy = timezone.localdate()
    fecha, error = _calendar_date(request.GET.get('fecha'), hoy)
    vista = request.GET.get('vista', 'mes')
    if vista not in ('mes', 'semana', 'dia'):
        vista = 'mes'
        error = error or 'La vista solicitada no es válida.'

    citas = Cita.objects.all()
    if stylist:
        citas = citas.filter(estilista=stylist)
    else:
        citas = citas.filter(cliente__persona=request.user)

    query = request.GET.get('q', '').strip()[:100]
    if query:
        citas = citas.filter(
            Q(cliente__persona__first_name__icontains=query)
            | Q(cliente__persona__last_name__icontains=query)
            | Q(cliente__persona__username__icontains=query)
            | Q(servicio__nombre__icontains=query)
        )

    estado = request.GET.get('estado', '').upper()
    estados_validos = dict(Cita.ESTADOS)
    if estado and estado not in estados_validos:
        error = error or 'El estado seleccionado no es válido.'
        citas = citas.none()
    elif estado:
        citas = citas.filter(estado=estado)

    fecha_inicio_raw = request.GET.get('desde', '').strip()
    fecha_fin_raw = request.GET.get('hasta', '').strip()
    fecha_inicio = fecha_fin = None
    if fecha_inicio_raw or fecha_fin_raw:
        fecha_inicio, error_inicio = _calendar_date(fecha_inicio_raw, None)
        fecha_fin, error_fin = _calendar_date(fecha_fin_raw, None)
        if error_inicio or error_fin or not fecha_inicio or not fecha_fin:
            error = error or 'El rango de fechas debe incluir dos fechas válidas.'
            citas = citas.none()
        elif fecha_inicio > fecha_fin:
            error = error or 'La fecha inicial no puede ser posterior a la final.'
            citas = citas.none()
        else:
            citas = citas.filter(fecha__gte=fecha_inicio, fecha__lte=fecha_fin)

    hora_inicio_raw = request.GET.get('hora_desde', '').strip()
    hora_fin_raw = request.GET.get('hora_hasta', '').strip()
    if hora_inicio_raw or hora_fin_raw:
        try:
            hora_inicio = time.fromisoformat(hora_inicio_raw) if hora_inicio_raw else None
            hora_fin = time.fromisoformat(hora_fin_raw) if hora_fin_raw else None
            if hora_inicio and hora_fin and hora_inicio > hora_fin:
                raise ValueError
        except ValueError:
            error = error or 'El rango horario no es válido.'
            citas = citas.none()
        else:
            if hora_inicio:
                citas = citas.filter(hora_inicio__gte=hora_inicio)
            if hora_fin:
                citas = citas.filter(hora_inicio__lte=hora_fin)

    inicio, fin = _calendar_range(fecha, vista)
    citas_periodo = citas.filter(
        fecha__gte=inicio,
        fecha__lte=fin,
    ).select_related('cliente__persona', 'servicio').order_by('fecha', 'hora_inicio')
    citas_dia = citas.filter(fecha=fecha).select_related(
        'cliente__persona', 'servicio'
    ).order_by('hora_inicio')
    estados = citas_dia.values('estado').annotate(total=Count('pk'))
    resumen = {estado: 0 for estado in estados_validos}
    resumen.update({fila['estado']: fila['total'] for fila in estados})
    duracion = citas_dia.exclude(
        estado__in=('RECHAZADA', 'CANCELADA')
    ).aggregate(
        total=Sum(Coalesce('duracion_aprobada', 'servicio__duracion'))
    )['total'] or 0
    proximas = citas.filter(
        Q(fecha__gt=hoy)
        | Q(fecha=hoy, hora_inicio__gte=timezone.localtime().time()),
        estado__in=('PENDIENTE', 'CONFIRMADA', 'EN_PROCESO'),
    ).count()

    def serialize(cita):
        estado_visual = _estado_visual(cita)
        return {
            'id': cita.pk,
            'cliente': cita.cliente.get_full_name() or cita.cliente.username,
            'servicio': cita.servicio.nombre,
            'categoria': cita.servicio.categoria,
            'precio': str(cita.servicio.precio),
            'fecha': cita.fecha.isoformat(),
            'inicio': cita.hora_inicio.strftime('%H:%M'),
            'fin': cita.hora_fin.strftime('%H:%M'),
            'duracion': cita.duracion_aprobada or cita.servicio.duracion,
            'estado': cita.estado,
            'estado_visual': estado_visual,
            'mensaje': cita.mensaje or cita.notas,
        }

    dias_con_citas = list(
        citas_periodo.values_list('fecha', flat=True).distinct().order_by('fecha')
    )
    payload = {
        'fecha': fecha,
        'hoy': hoy,
        'vista': vista,
        'inicio_periodo': inicio,
        'fin_periodo': fin,
        'citas': [serialize(cita) for cita in citas_periodo],
        'citas_dia': [serialize(cita) for cita in citas_dia],
        'resumen': resumen,
        'proximas': proximas,
        'duracion_total': duracion,
        'dias_con_citas': [dia.isoformat() for dia in dias_con_citas],
        'error': error,
        'rol_calendario': 'estilista' if stylist else 'cliente',
    }
    return payload


# Explicación: Renderiza la agenda sin exponer las citas de otras personas.
def _calendar_view(request, stylist):
    payload = _calendar_payload(request, stylist)
    if request.GET.get('formato') == 'json' or request.GET.get('format') == 'json':
        return JsonResponse({
            key: value.isoformat() if isinstance(value, date) else value
            for key, value in payload.items()
            if key != 'calendar_json'
        })
    template = (
        'App_agenda/E_calendario.html'
        if stylist
        else 'App_agenda/C_calendario.html'
    )
    payload['estados_choices'] = Cita.ESTADOS
    payload['calendar_json'] = {
        key: value
        for key, value in payload.items()
        if key != 'estados_choices'
    }
    return render(request, template, payload)


# Explicación: RF-ES-002: presenta agenda privada de la profesional.
@role_required('estilista')
def calendario_view(request):
    estilista, _ = Estilista.objects.get_or_create(persona=request.user)
    return _calendar_view(request, estilista)


# Explicación: RF-CLI-006: presenta el calendario de citas propias de la clienta.
@role_required('cliente')
def calendario_cliente_view(request):
    return _calendar_view(request, None)


# Explicación: RF-ES-009: cierra una atención y fija la fecha real de finalización.
@role_required('estilista')
@require_POST
def completar_cita_view(request, cita_id):
    estilista, _ = Estilista.objects.get_or_create(persona=request.user)
    cita = get_object_or_404(
        Cita,
        pk=cita_id,
        estilista=estilista,
        estado__in=('CONFIRMADA', 'EN_PROCESO'),
    )
    if cita.inicio_local > timezone.now():
        messages.error(request, 'No puedes finalizar un servicio que todavía no comienza.')
        return redirect('App_agenda:e_calendario')
    anterior = cita.estado
    cita.estado = 'FINALIZADA'
    cita.fecha_finalizacion = timezone.now()
    cita.save(update_fields=['estado', 'fecha_finalizacion'])
    registrar_cambio(cita, request.user, 'FINALIZACION', anterior)
    messages.success(request, 'La cita se marcó como finalizada.')
    return redirect(f'{reverse("App_agenda:e_calendario")}?fecha={cita.fecha.isoformat()}')


# Explicación: Muestra el directorio de clientas que tienen citas con la estilista.
@role_required('estilista')
def clientes_view(request):
    estilista, _ = Estilista.objects.get_or_create(persona=request.user)
    clientes = Cliente.objects.filter(citas__estilista=estilista).annotate(
        total_citas=Count('citas', filter=Q(citas__estilista=estilista), distinct=True),
        citas_pendientes=Count(
            'citas',
            filter=Q(citas__estilista=estilista, citas__estado='PENDIENTE'),
            distinct=True,
        ),
        citas_confirmadas=Count(
            'citas',
            filter=Q(citas__estilista=estilista, citas__estado='CONFIRMADA'),
            distinct=True,
        ),
    ).select_related('persona').distinct().order_by(
        'persona__last_name', 'persona__first_name'
    )
    return render(request, 'App_agenda/E_clientes.html', {'clientes': clientes})


# Explicación: RF-ES-011: chat de la estilista con sus clientas registradas.
@role_required('estilista')
def mensajes_estilista_view(request):
    estilista, _ = Estilista.objects.get_or_create(persona=request.user)
    contactos = Cliente.objects.filter(citas__estilista=estilista).distinct(
    ).select_related('persona').order_by('persona__last_name', 'persona__first_name')
    contacto = None
    contacto_id = request.POST.get('destinatario_id') or request.GET.get('con')
    if contacto_id:
        contacto = contactos.filter(pk=contacto_id).first()
        if contacto is None:
            messages.error(request, 'La clienta seleccionada no está en tu directorio.')

    if request.method == 'POST' and contacto:
        contenido = request.POST.get('contenido', '').strip()
        if not contenido or len(contenido) > 2000:
            messages.error(request, 'El mensaje debe tener entre 1 y 2000 caracteres.')
        else:
            Mensaje.objects.create(
                remitente=request.user,
                destinatario=contacto.persona,
                contenido=contenido,
                cita=Cita.objects.filter(
                    cliente=contacto, estilista=estilista,
                ).order_by('-fecha', '-hora_inicio').first(),
            )
            messages.success(request, 'Tu mensaje se envió correctamente.')
            return redirect(f'{reverse("App_agenda:e_mensajes")}?con={contacto.pk}')

    mensajes = Mensaje.objects.none()
    if contacto:
        mensajes = Mensaje.objects.filter(
            Q(remitente=request.user, destinatario=contacto.persona)
            | Q(remitente=contacto.persona, destinatario=request.user)
        ).select_related('remitente', 'destinatario')
        mensajes.filter(destinatario=request.user, leido=False).update(leido=True)
    return render(
        request,
        'App_agenda/E_mensajes.html',
        {'contactos': contactos, 'contacto': contacto, 'mensajes': mensajes},
    )


# Explicación: Panel principal de la clienta con sus avisos personales.
@role_required('cliente')
def c_inicio_view(request):
    notificaciones_mensajes = Mensaje.objects.filter(
        destinatario=request.user,
        leido=False,
    ).filter(
        Q(remitente__rol='estilista')
        | Q(remitente__is_staff=True)
        | Q(remitente__is_superuser=True)
    ).count()
    return render(
        request,
        'App_agenda/C_inicio.html',
        {'notificaciones_mensajes': notificaciones_mensajes},
    )

# Explicación: RF-ES-008: cambia Confirmada a En proceso si ya llegó su hora.
@role_required('estilista')
@require_POST
def iniciar_cita_view(request, cita_id):
    estilista, _ = Estilista.objects.get_or_create(persona=request.user)
    with transaction.atomic():
        cita = get_object_or_404(Cita.objects.select_for_update(), pk=cita_id, estilista=estilista, estado='CONFIRMADA')
        if cita.inicio_local > timezone.now():
            messages.error(request, 'No puede iniciar un servicio antes de su horario reservado.')
            return redirect('App_agenda:e_calendario')
        cita.estado = 'EN_PROCESO'
        cita.save(update_fields=['estado'])
        registrar_cambio(cita, request.user, 'INICIO', 'CONFIRMADA')
    messages.success(request, 'Servicio marcado como en proceso.')
    return redirect('App_agenda:e_calendario')


# Explicación: Consulta la trazabilidad de una cita sin revelar datos de otras estilistas.
@role_required('estilista')
def bitacora_cita_view(request, cita_id):
    estilista, _ = Estilista.objects.get_or_create(persona=request.user)
    cita = get_object_or_404(Cita, pk=cita_id, estilista=estilista)
    return render(request, 'App_agenda/E_bitacora.html', {'cita':cita, 'eventos':cita.bitacora.select_related('persona')})


# Explicación: Lista avisos privados y marca como leídos solo los del propietario.
@login_required
def notificaciones_view(request):
    if request.method == 'POST':
        Notificacion.objects.filter(persona=request.user, leida=False).update(leida=True)
        return redirect('App_agenda:notificaciones')
    template = 'App_agenda/E_notificaciones.html' if rol_real(request.user) in ('estilista', 'administrador') else 'App_agenda/C_notificaciones.html'
    return render(request, template,
                  {'notificaciones':Notificacion.objects.filter(persona=request.user)[:100]})
