import hashlib
import logging
import secrets

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.core.cache import cache
from django.core.mail import send_mail
from django.contrib.auth import (
    REDIRECT_FIELD_NAME,
    authenticate,
    login,
    logout,
    password_validation,
)
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from App_agenda.forms import DIAS_SEMANA, HorarioForm, BloqueoAgendaForm, PoliticaAgendaForm
from App_agenda.models import Horario, BloqueoAgenda, ConfiguracionAgenda, Cita

from .decorators import role_required, rol_real
from .forms import RegistroClienteForm, ConfirmarCodigoRegistroForm
from .models import Cliente, Estilista, Persona, HistorialAcceso


# Explicación: Define el panel inicial en función del rol autenticado almacenado en la base de datos.
def dashboard_url(usuario):
    """Escoge la portada según el rol real, nunca según un parámetro de formulario."""
    rol = rol_real(usuario)
    return {
        'administrador': 'App_administracion:inicio',
        'estilista': 'App_agenda:e_inicio',
        'cliente': 'App_agenda:c_inicio',
    }.get(rol, 'App_usuarios:login')


# Explicación: Muestra la portada pública o redirige a la portada interna del rol.
def home_view(request):
    """La portada pública no exige inicio de sesión; los usuarios van a su panel."""
    if request.user.is_authenticated and request.GET.get('vista') != 'publica':
        return redirect(dashboard_url(request.user))
    from App_servicios.models import Servicio
    from App_inicio.models import FotoCarrusel
    return render(request, 'App_usuarios/home.html', {
        'servicios': Servicio.objects.filter(activo=True).order_by('nombre')[:6],
        'fotos_carrusel_portada': FotoCarrusel.objects.filter(activa=True, mostrar_en_portada=True).order_by('orden', 'pk')[:12],
    })


# Explicación: Verifica credenciales, tipo de cuenta y destino permitido antes de iniciar sesión.
def login_view(request, rol=None):
    """Autentica y compara estrictamente el rol elegido con el almacenado en BD."""
    roles_validos = ('cliente', 'estilista', 'administrador')
    # Las URL dedicadas no pueden cambiar de rol con un POST malicioso.
    rol_seleccionado = rol if rol in roles_validos else (
        request.POST.get('rol') or request.GET.get('rol') or 'cliente'
    )
    if request.user.is_authenticated and not (
        request.method == 'GET' and request.GET.get('vista') == 'publica'
    ):
        return redirect(dashboard_url(request.user))

    if request.method == 'POST':
        identificador = request.POST.get('username', '').strip()
        username = identificador
        if not Persona.objects.filter(username=username).exists():
            username = Persona.objects.filter(
                email__iexact=identificador,
            ).values_list('username', flat=True).first() or identificador
        usuario = authenticate(
            request, username=username, password=request.POST.get('password', '')
        )
        if rol_seleccionado not in roles_validos:
            messages.error(request, 'Selecciona un tipo de cuenta válido.')
        elif usuario is None:
            messages.error(request, 'Credenciales incorrectas. Puedes recuperar tu contraseña.')
        elif rol_real(usuario) != rol_seleccionado:
            modulo = {'cliente':'clientes','estilista':'estilista','administrador':'administradores'}[rol_seleccionado]
            messages.error(request, f'Esta cuenta no pertenece al módulo de {modulo}.')
        else:
            login(request, usuario)
            HistorialAcceso.objects.create(
                persona=usuario, identificador=identificador,
                evento='LOGIN', rol_solicitado=rol_seleccionado,
            )
            next_url = request.POST.get(REDIRECT_FIELD_NAME) or request.GET.get(
                REDIRECT_FIELD_NAME
            )
            if next_url and url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect(dashboard_url(usuario))

        # Registrar fallos sin exponer la contraseña ni el motivo detallado.
        HistorialAcceso.objects.create(
            persona=usuario, identificador=identificador[:150],
            evento='FALLO', rol_solicitado=rol_seleccionado[:20],
        )

    from App_inicio.models import FotoCarrusel
    return render(request, 'App_usuarios/C_login.html', {
        'rol_seleccionado': rol_seleccionado,
        'rol_bloqueado': bool(rol),
        'fotos_carrusel_login': FotoCarrusel.objects.filter(
            activa=True, mostrar_en_login=True,
        ).order_by('orden', 'pk')[:12],
    })


# Verificación obligatoria previa a crear Persona y Cliente.
# Los datos pendientes viven en la sesión del servidor; no se guardan cuentas
# incompletas ni contraseñas en texto plano.
REGISTRO_PENDIENTE = 'registro_cliente_pendiente'
DURACION_CODIGO_SEGUNDOS = 10 * 60
DURACION_REGISTRO_SEGUNDOS = 30 * 60
ESPERA_REENVIO_SEGUNDOS = 60
MAXIMO_ENVIOS = 3
MAXIMO_INTENTOS = 5
logger = logging.getLogger(__name__)


def _registro_throttle_key(email):
    """Evita escribir correos en claro como claves de caché."""
    return 'registro_correo:' + hashlib.sha256(email.encode('utf-8')).hexdigest()


def _enviar_codigo_confirmacion(email, codigo):
    """El código se envía solo a la dirección declarada en el registro."""
    cantidad = send_mail(
        subject='Leidy Make Up | Verifica tu correo',
        message=(
            'Hola,\n\nTu código para confirmar el registro en Leidy Make Up es: '
            f'{codigo}\n\nEste código caduca en 10 minutos. '
            'Si tú no solicitaste una cuenta, ignora este correo.\n'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )
    if cantidad != 1:
        raise RuntimeError('El servicio de correo no confirmó el envío.')


def _registro_pendiente(request):
    pendiente = request.session.get(REGISTRO_PENDIENTE)
    if not isinstance(pendiente, dict):
        return None
    if timezone.now().timestamp() >= pendiente.get('creado_en', 0) + DURACION_REGISTRO_SEGUNDOS:
        request.session.pop(REGISTRO_PENDIENTE, None)
        return None
    return pendiente


# Explicación: valida datos, envía código y pospone la creación de la cuenta.
@never_cache
def registro_view(request):
    if request.user.is_authenticated:
        return redirect(dashboard_url(request.user))
    form = RegistroClienteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        datos = form.cleaned_data
        email = datos['email']
        key = _registro_throttle_key(email)
        if not cache.add(key, 'enviado', timeout=ESPERA_REENVIO_SEGUNDOS):
            form.add_error('email', 'Ya enviamos un código a este correo recientemente. Espera un minuto para solicitar otro.')
        else:
            codigo = f'{secrets.randbelow(1_000_000):06d}'
            try:
                _enviar_codigo_confirmacion(email, codigo)
            except Exception:
                cache.delete(key)
                logger.exception('Falló el envío del código de registro.')
                form.add_error(None, 'No fue posible enviar el código. Revisa la configuración del correo e inténtalo de nuevo.')
            else:
                ahora = timezone.now().timestamp()
                request.session[REGISTRO_PENDIENTE] = {
                    'nombre': datos['nombre'].strip(),
                    'apellido': datos['apellido'].strip(),
                    'telefono': datos['telefono'].strip(),
                    'email': email,
                    'password_hash': make_password(datos['password']),
                    'codigo_hash': make_password(codigo),
                    'creado_en': ahora,
                    'vence_en': ahora + DURACION_CODIGO_SEGUNDOS,
                    'enviado_en': ahora,
                    'envios': 1,
                    'intentos': 0,
                }
                messages.success(request, 'Enviamos un código de 6 dígitos a tu correo. Confírmalo para crear tu cuenta.')
                return redirect('App_usuarios:confirmar_registro')

    return render(request, 'App_usuarios/C_registro.html', {'form': form})


# Explicación: solo el código correcto y vigente permite crear la cuenta cliente.
@never_cache
def confirmar_registro_view(request):
    if request.user.is_authenticated:
        return redirect(dashboard_url(request.user))
    pendiente = _registro_pendiente(request)
    if pendiente is None:
        messages.info(request, 'Completa el formulario de registro para recibir tu código.')
        return redirect('App_usuarios:registro')

    form = ConfirmarCodigoRegistroForm(request.POST or None)
    ahora = timezone.now().timestamp()
    if request.method == 'POST' and form.is_valid():
        codigo = form.cleaned_data['codigo']
        if ahora >= pendiente['vence_en']:
            form.add_error('codigo', 'El código venció. Solicita uno nuevo con el botón Reenviar código.')
        elif pendiente['intentos'] >= MAXIMO_INTENTOS:
            form.add_error('codigo', 'Agotaste los intentos. Solicita un código nuevo.')
        elif not check_password(codigo, pendiente['codigo_hash']):
            pendiente['intentos'] += 1
            request.session[REGISTRO_PENDIENTE] = pendiente
            form.add_error('codigo', 'El código es incorrecto. Revisa el correo e inténtalo nuevamente.')
            if pendiente['intentos'] >= MAXIMO_INTENTOS:
                messages.error(request, 'Agotaste los intentos. Solicita un código nuevo.')
        else:
            email = pendiente['email']
            # Volver a comprobar la unicidad al confirmar, nunca crear un rol distinto de cliente.
            if Persona.objects.filter(email__iexact=email).exists() or Persona.objects.filter(username__iexact=email).exists():
                request.session.pop(REGISTRO_PENDIENTE, None)
                messages.error(request, 'Este correo ya está registrado. Inicia sesión.')
                return redirect('App_usuarios:login')
            try:
                with transaction.atomic():
                    persona = Persona(
                        username=email,
                        email=email,
                        first_name=pendiente['nombre'],
                        last_name=pendiente['apellido'],
                        rol='cliente',
                        password=pendiente['password_hash'],
                    )
                    persona.save()
                    Cliente.objects.create(persona=persona, telefono=pendiente['telefono'])
            except IntegrityError:
                form.add_error(None, 'No se pudo completar el registro. Es posible que ya exista una cuenta con este correo.')
            else:
                request.session.pop(REGISTRO_PENDIENTE, None)
                messages.success(request, 'Correo confirmado. Tu cuenta fue creada correctamente. Ya puedes iniciar sesión.')
                return redirect('App_usuarios:login')

    ahora = timezone.now().timestamp()
    return render(request, 'App_usuarios/C_confirmar_correo.html', {
        'form': form,
        'email': pendiente['email'],
        'codigo_vencido': ahora >= pendiente['vence_en'],
        'intentos_restantes': max(0, MAXIMO_INTENTOS - pendiente['intentos']),
        'segundos_reenvio': max(0, int(ESPERA_REENVIO_SEGUNDOS - (ahora - pendiente['enviado_en']))),
        'envios_restantes': max(0, MAXIMO_ENVIOS - pendiente['envios']),
    })


# Explicación: el reenvío exige POST, está limitado y anula el código anterior.
@require_POST
def reenviar_codigo_registro_view(request):
    if request.user.is_authenticated:
        return redirect(dashboard_url(request.user))
    pendiente = _registro_pendiente(request)
    if pendiente is None:
        messages.error(request, 'El registro pendiente venció. Vuelve a completar tus datos.')
        return redirect('App_usuarios:registro')

    if pendiente['envios'] >= MAXIMO_ENVIOS:
        messages.error(request, 'Alcanzaste el límite de reenvíos. Vuelve a registrarte pasados 30 minutos.')
        return redirect('App_usuarios:confirmar_registro')
    ahora = timezone.now().timestamp()
    if ahora - pendiente['enviado_en'] < ESPERA_REENVIO_SEGUNDOS:
        messages.error(request, 'Debes esperar al menos 60 segundos antes de reenviar otro código.')
        return redirect('App_usuarios:confirmar_registro')
    email = pendiente['email']
    if Persona.objects.filter(email__iexact=email).exists() or Persona.objects.filter(username__iexact=email).exists():
        request.session.pop(REGISTRO_PENDIENTE, None)
        messages.error(request, 'Este correo ya pertenece a una cuenta registrada.')
        return redirect('App_usuarios:login')

    key = _registro_throttle_key(email)
    if not cache.add(key, 'enviado', timeout=ESPERA_REENVIO_SEGUNDOS):
        messages.error(request, 'Hay un envío reciente para este correo. Espera un minuto.')
        return redirect('App_usuarios:confirmar_registro')

    codigo = f'{secrets.randbelow(1_000_000):06d}'
    # Impedir que el código nuevo coincida con el anterior.
    while check_password(codigo, pendiente['codigo_hash']):
        codigo = f'{secrets.randbelow(1_000_000):06d}'
    try:
        _enviar_codigo_confirmacion(email, codigo)
    except Exception:
        cache.delete(key)
        logger.exception('Falló el reenvío del código de registro.')
        messages.error(request, 'No se pudo reenviar el código. Inténtalo nuevamente.')
    else:
        pendiente.update({
            'codigo_hash': make_password(codigo),
            'vence_en': min(ahora + DURACION_CODIGO_SEGUNDOS, pendiente['creado_en'] + DURACION_REGISTRO_SEGUNDOS),
            'enviado_en': ahora,
            'envios': pendiente['envios'] + 1,
            'intentos': 0,
        })
        request.session[REGISTRO_PENDIENTE] = pendiente
        messages.success(request, 'Te enviamos un código nuevo. El anterior ya no funciona.')
    return redirect('App_usuarios:confirmar_registro')


# Explicación: Abre la guía de uso correspondiente a la cuenta actual.
def ayuda_view(request):
    if rol_real(request.user) == 'administrador':
        return redirect('App_administracion:ayuda')
    if rol_real(request.user) == 'estilista':
        return render(request, 'App_usuarios/E_ayuda.html')
    return render(request, 'App_usuarios/C_ayuda.html')


# Explicación: Actualiza únicamente la información personal y el teléfono del cliente autenticado.
CAMBIO_CORREO_PENDIENTE = 'cambio_correo_pendiente'


def _enviar_codigo_cambio(email, codigo):
    enviados = send_mail(
        'Leidy Make Up | Confirma tu nuevo correo',
        f'Tu código para cambiar el correo de tu perfil es: {codigo}\n'
        'Caduca en 10 minutos. Si no solicitaste este cambio, no compartas el código.',
        settings.DEFAULT_FROM_EMAIL, [email],
    )
    if enviados != 1:
        raise RuntimeError('No se confirmó el envío del código.')


@role_required('cliente')
def perfil_view(request):
    """Las modificaciones de dirección de correo necesitan segundo paso OTP."""
    cliente = Cliente.objects.filter(persona=request.user).first()
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        try:
            validate_email(email)
        except ValidationError as error:
            for texto in error.messages: messages.error(request, texto)
            return render(request, 'App_usuarios/C_perfil.html', {'cliente': cliente})

        cambio = email != (request.user.email or '').lower()
        if cambio:
            if Persona.objects.exclude(pk=request.user.pk).filter(email__iexact=email).exists() or Persona.objects.exclude(pk=request.user.pk).filter(username__iexact=email).exists():
                messages.error(request, 'Ese correo ya pertenece a una cuenta.')
                return render(request, 'App_usuarios/C_perfil.html', {'cliente': cliente})
            key = _registro_throttle_key(email)
            if not cache.add(key, 'cambio', timeout=ESPERA_REENVIO_SEGUNDOS):
                messages.error(request, 'Hay un envío reciente a esta dirección. Espera un minuto.')
                return render(request, 'App_usuarios/C_perfil.html', {'cliente': cliente})
            codigo = f'{secrets.randbelow(1_000_000):06d}'
            try:
                _enviar_codigo_cambio(email, codigo)
            except Exception:
                cache.delete(key)
                logger.exception('No se pudo enviar el código de cambio de correo.')
                messages.error(request, 'No fue posible enviar el código. Tu correo no se cambió.')
                return render(request, 'App_usuarios/C_perfil.html', {'cliente': cliente})
            request.session[CAMBIO_CORREO_PENDIENTE] = {
                'persona_pk': request.user.pk, 'email': email,
                'codigo_hash': make_password(codigo),
                'vence_en': timezone.now().timestamp() + DURACION_CODIGO_SEGUNDOS,
                'intentos': 0,
            }
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name = request.POST.get('last_name', '').strip()
        request.user.save(update_fields=['first_name', 'last_name'])
        if cliente:
            cliente.telefono = request.POST.get('telefono', '').strip()
            cliente.direccion = request.POST.get('direccion', '').strip()
            cliente.save(update_fields=['telefono', 'direccion'])
        if cambio:
            messages.info(request, 'Confirma el código enviado al nuevo correo para completar el cambio.')
            return redirect('App_usuarios:confirmar_cambio_correo')
        messages.success(request, 'Tu perfil fue actualizado.')
        return redirect('App_usuarios:perfil')
    return render(request, 'App_usuarios/C_perfil.html', {'cliente': cliente})


@role_required('cliente')
@never_cache
def confirmar_cambio_correo_view(request):
    pendiente = request.session.get(CAMBIO_CORREO_PENDIENTE)
    if not isinstance(pendiente, dict) or pendiente.get('persona_pk') != request.user.pk:
        messages.error(request, 'No hay un cambio de correo pendiente.')
        return redirect('App_usuarios:perfil')
    form = ConfirmarCodigoRegistroForm(request.POST or None)
    ahora = timezone.now().timestamp()
    expirado = ahora >= pendiente.get('vence_en', 0)
    if request.method == 'POST' and form.is_valid():
        if expirado:
            form.add_error('codigo', 'El código venció. Vuelve al perfil para solicitar otro.')
        elif pendiente.get('intentos', 0) >= MAXIMO_INTENTOS:
            form.add_error('codigo', 'Agotaste los intentos. Vuelve a solicitar otro código.')
        elif not check_password(form.cleaned_data['codigo'], pendiente.get('codigo_hash', '')):
            pendiente['intentos'] += 1
            request.session[CAMBIO_CORREO_PENDIENTE] = pendiente
            form.add_error('codigo', 'Código incorrecto.')
        else:
            correo_nuevo = pendiente['email']
            if Persona.objects.exclude(pk=request.user.pk).filter(email__iexact=correo_nuevo).exists():
                form.add_error(None, 'Esa dirección ya está en uso.')
            else:
                try:
                    with transaction.atomic():
                        antiguo = (request.user.email or '').lower()
                        request.user.email = correo_nuevo
                        campos = ['email']
                        if request.user.username.lower() == antiguo:
                            request.user.username = correo_nuevo
                            campos.append('username')
                        request.user.save(update_fields=campos)
                except IntegrityError:
                    form.add_error(None, 'No se pudo cambiar el correo porque ya se encuentra registrado.')
                else:
                    request.session.pop(CAMBIO_CORREO_PENDIENTE, None)
                    messages.success(request, 'Correo electrónico actualizado y verificado.')
                    return redirect('App_usuarios:perfil')
    return render(request, 'App_usuarios/C_confirmar_cambio_correo.html', {
        'form': form, 'email': pendiente['email'],
        'expirado': expirado,
        'bloqueado': pendiente.get('intentos', 0) >= MAXIMO_INTENTOS,
    })


# Explicación: Permite a la estilista editar especialidad, horario, descansos y políticas de agenda.
@role_required('estilista')
def configuracion_view(request):
    estilista, _ = Estilista.objects.get_or_create(persona=request.user)
    horario_form = HorarioForm(estilista=estilista)
    politica, _ = ConfiguracionAgenda.objects.get_or_create(estilista=estilista)
    politica_form = PoliticaAgendaForm(instance=politica)
    bloqueo_form = BloqueoAgendaForm()
    if request.method == 'POST':
        accion = request.POST.get('accion', 'guardar_perfil')
        if accion == 'guardar_horario':
            horario_id = request.POST.get('horario_id')
            horario = None
            if horario_id:
                horario = Horario.objects.filter(
                    pk=horario_id,
                    estilista=estilista,
                ).first()
                if horario is None:
                    messages.error(request, 'El horario seleccionado no existe.')
                    return redirect('App_usuarios:configuracion')
            horario_form = HorarioForm(
                request.POST,
                instance=horario,
                estilista=estilista,
            )
            if horario_form.is_valid():
                horario = horario_form.save(commit=False)
                horario.estilista = estilista
                horario.save()
                messages.success(request, 'El horario laboral fue guardado correctamente.')
                return redirect('App_usuarios:configuracion')
            for errors in horario_form.errors.values():
                for error in errors:
                    messages.error(request, error)
        elif accion == 'guardar_politicas':
            politica_form = PoliticaAgendaForm(request.POST, instance=politica)
            if politica_form.is_valid():
                politica_form.save()
                messages.success(request,'Políticas de anticipación actualizadas.')
                return redirect('App_usuarios:configuracion')
            for err in politica_form.errors.values():
                for msg in err: messages.error(request,msg)
        elif accion == 'guardar_bloqueo':
            bloqueo_form = BloqueoAgendaForm(request.POST)
            if bloqueo_form.is_valid():
                bloqueo = bloqueo_form.save(commit=False)
                bloqueo.estilista = estilista
                ocupadas = Cita.objects.filter(estilista=estilista,
                    fecha__gte=bloqueo.fecha_inicio, fecha__lte=bloqueo.fecha_fin,
                    estado__in=('CONFIRMADA','EN_PROCESO')).exists()
                if ocupadas:
                    messages.error(request,'Ya existen citas confirmadas en esas fechas. Revisa la agenda antes de bloquear.')
                else:
                    bloqueo.save()
                    messages.success(request,'Días bloqueados correctamente.')
                    return redirect('App_usuarios:configuracion')
            for err in bloqueo_form.errors.values():
                for msg in err: messages.error(request,msg)
        elif accion == 'eliminar_bloqueo':
            if BloqueoAgenda.objects.filter(pk=request.POST.get('bloqueo_id'),estilista=estilista).delete()[0]:
                messages.success(request,'Bloqueo eliminado.')
            return redirect('App_usuarios:configuracion')
        elif accion == 'guardar_perfil':
            estilista.especialidad = request.POST.get('especialidad', '').strip()
            estilista.save(update_fields=['especialidad'])
            messages.success(request, 'La configuración fue actualizada.')
            return redirect('App_usuarios:configuracion')

    return render(
        request,
        'App_usuarios/E_configuracion.html',
        {
            'estilista': estilista,
            'horarios': Horario.objects.filter(estilista=estilista).order_by(
                'dia_semana', 'hora_inicio'
            ),
            'horario_form': horario_form,
            'dias_semana': DIAS_SEMANA,
            'politica_form': politica_form,
            'bloqueo_form': bloqueo_form,
            'bloqueos': BloqueoAgenda.objects.filter(estilista=estilista).order_by('fecha_inicio'),
        },
    )


# Explicación: Guarda un evento de auditoría y elimina la sesión autenticada.
@login_required
@require_POST
def logout_view(request):
    HistorialAcceso.objects.create(persona=request.user, identificador=request.user.username, evento='LOGOUT', rol_solicitado=rol_real(request.user) or '')
    logout(request)
    return redirect('App_usuarios:login')


# Explicación: Fija el inicio de sesión como estilista para que nadie cambie el rol por POST.
def e_login(request):
    return login_view(request, rol='estilista')


# Explicación: Fija el inicio de sesión como administrador para impedir accesos cruzados.
def a_login(request):
    """Punto de entrada exclusivo del administrador."""
    return login_view(request, rol='administrador')


# Explicación: Envía mensajes de la clienta al soporte administrativo y muestra respuestas.
@role_required('cliente')
def soporte_view(request):
    """Buzón separado para preguntas que debe responder el Administrador."""
    from django.db.models import Q
    from App_agenda.models import Mensaje
    admins=Persona.objects.filter(rol='administrador',is_staff=True,is_active=True).order_by('pk')
    administrador=admins.first()
    if request.method=='POST':
        contenido=request.POST.get('contenido','').strip()
        if not administrador:
            messages.error(request,'No hay un administrador disponible.')
        elif not 1<=len(contenido)<=2000:
            messages.error(request,'El mensaje debe tener entre 1 y 2000 caracteres.')
        else:
            Mensaje.objects.create(remitente=request.user,destinatario=administrador,contenido=contenido)
            messages.success(request,'Consulta enviada a administración.')
            return redirect('App_usuarios:soporte')
    conversacion=(Mensaje.objects.filter(Q(remitente=request.user,destinatario=administrador)|Q(remitente=administrador,destinatario=request.user)).order_by('creado_en') if administrador else Mensaje.objects.none())
    return render(request,'App_usuarios/C_soporte.html',{'mensajes_soporte':conversacion,'administrador':administrador})
