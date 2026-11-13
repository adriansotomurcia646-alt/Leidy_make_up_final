from django.contrib import messages
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
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from App_agenda.forms import DIAS_SEMANA, HorarioForm, BloqueoAgendaForm, PoliticaAgendaForm
from App_agenda.models import Horario, BloqueoAgenda, ConfiguracionAgenda, Cita

from .decorators import role_required, rol_real
from .forms import RegistroClienteForm
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
    if request.user.is_authenticated:
        return redirect(dashboard_url(request.user))
    from App_servicios.models import Servicio
    return render(request, 'App_usuarios/home.html', {
        'servicios': Servicio.objects.filter(activo=True).order_by('nombre')[:6],
    })


# Explicación: Verifica credenciales, tipo de cuenta y destino permitido antes de iniciar sesión.
def login_view(request, rol=None):
    """Autentica y compara estrictamente el rol elegido con el almacenado en BD."""
    roles_validos = ('cliente', 'estilista', 'administrador')
    # Las URL dedicadas no pueden cambiar de rol con un POST malicioso.
    rol_seleccionado = rol if rol in roles_validos else (
        request.POST.get('rol') or request.GET.get('rol') or 'cliente'
    )
    if request.user.is_authenticated:
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

    return render(request, 'App_usuarios/C_login.html', {
        'rol_seleccionado': rol_seleccionado,
        'rol_bloqueado': bool(rol),
    })


# Explicación: Valida el formulario y crea una cuenta cliente con contraseña cifrada.
def registro_view(request):
    form = RegistroClienteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        # Solo se utilizan valores normalizados por el formulario validado.
        nombre = form.cleaned_data['nombre'].strip()
        apellido = form.cleaned_data['apellido'].strip()
        email = form.cleaned_data['email']
        telefono = form.cleaned_data['telefono'].strip()
        password = form.cleaned_data['password']

        if not nombre or not apellido or not telefono or not email or not password:
            messages.error(request, 'Completa nombre, apellidos, teléfono, correo y contraseña.')
        else:
            try:
                validate_email(email)
                password_validation.validate_password(password)
                if Persona.objects.filter(email__iexact=email).exists():
                    raise ValidationError(
                        'Correo ya registrado. Inicia sesión o usa otra dirección de correo.'
                    )

                with transaction.atomic():
                    persona = Persona.objects.create_user(
                        username=email,
                        email=email,
                        password=password,
                        first_name=nombre,
                        last_name=apellido,
                        rol='cliente',
                    )
                    Cliente.objects.create(persona=persona, telefono=telefono)
            except ValidationError as error:
                for error_message in error.messages:
                    messages.error(request, error_message)
            except IntegrityError:
                if Persona.objects.filter(email__iexact=email).exists():
                    form.add_error(
                        'email',
                        'Este correo electrónico ya está registrado.',
                    )
                else:
                    form.add_error(
                        None,
                        'No fue posible crear la cuenta con esos datos. '
                        'Revisa la información e inténtalo de nuevo.',
                    )
            else:
                messages.success(request, 'Registro exitoso. Ya puedes iniciar sesión.')
                return redirect('App_usuarios:login')

    return render(request, 'App_usuarios/C_registro.html', {'form': form})


# Explicación: Abre la guía de uso correspondiente a la cuenta actual.
def ayuda_view(request):
    if rol_real(request.user) == 'administrador':
        return redirect('App_administracion:ayuda')
    if rol_real(request.user) == 'estilista':
        return render(request, 'App_usuarios/E_ayuda.html')
    return render(request, 'App_usuarios/C_ayuda.html')


# Explicación: Actualiza únicamente la información personal y el teléfono del cliente autenticado.
@role_required('cliente')
def perfil_view(request):
    cliente = Cliente.objects.filter(persona=request.user).first()
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        try:
            validate_email(email)
        except ValidationError as error:
            for error_message in error.messages:
                messages.error(request, error_message)
            return render(request, 'App_usuarios/C_perfil.html', {'cliente': cliente})

        if Persona.objects.exclude(pk=request.user.pk).filter(email__iexact=email).exists():
            messages.error(request, 'Ese correo ya está asociado a otra cuenta.')
            return render(request, 'App_usuarios/C_perfil.html', {'cliente': cliente})

        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name = request.POST.get('last_name', '').strip()
        request.user.email = email
        request.user.save(update_fields=['first_name', 'last_name', 'email'])
        if cliente:
            cliente.telefono = request.POST.get('telefono', '').strip()
            cliente.direccion = request.POST.get('direccion', '').strip()
            cliente.save(update_fields=['telefono', 'direccion'])
        messages.success(request, 'Tu perfil fue actualizado.')
        return redirect('App_usuarios:perfil')

    return render(request, 'App_usuarios/C_perfil.html', {'cliente': cliente})


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
