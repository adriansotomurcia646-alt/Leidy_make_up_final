from datetime import datetime, time, timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from App_servicios.models import Servicio
from App_usuarios.models import Estilista

from .models import Cita, Horario, BloqueoAgenda, ConfiguracionAgenda


DIAS_SEMANA = (
    (0, 'Lunes'),
    (1, 'Martes'),
    (2, 'Miércoles'),
    (3, 'Jueves'),
    (4, 'Viernes'),
    (5, 'Sábado'),
    (6, 'Domingo'),
)

INICIO_JORNADA = time(6, 0)
FIN_JORNADA = time(20, 0)
INTERVALO_INICIO_MINUTOS = 30
SEPARACION_ENTRE_CITAS = timedelta(hours=1)


def anticipacion_suficiente(fecha, hora_inicio, estilista=None):
    inicio = timezone.make_aware(datetime.combine(fecha, hora_inicio), timezone.get_current_timezone())
    politica = ConfiguracionAgenda.objects.filter(estilista=estilista).first() if estilista else None
    if not politica and not estilista:
        politica = ConfiguracionAgenda.objects.order_by('pk').first()
    minutos = politica.anticipacion_reserva_minutos if politica else 60
    return inicio > timezone.now() + timedelta(minutes=minutos)


def _estilista_cubre_horario(estilista, inicio, fin):
    horarios = Horario.objects.filter(
        estilista=estilista,
        activo=True,
        dia_semana=inicio.weekday(),
    )
    for horario in horarios:
        apertura = datetime.combine(inicio.date(), horario.hora_inicio)
        cierre = datetime.combine(inicio.date(), horario.hora_fin)
        if apertura <= inicio and fin <= cierre:
            return True
    return False


def _validacion_base(fecha, hora_inicio, servicio):
    if not servicio.activo or servicio.duracion <= 0:
        return 'unavailable', 'Este servicio no está disponible para reservar.'
    if hora_inicio.second or hora_inicio.microsecond or hora_inicio.minute not in (0, 30):
        return 'unavailable', 'Los inicios deben coincidir con intervalos de 30 minutos.'
    inicio = datetime.combine(fecha, hora_inicio)
    fin = inicio + timedelta(minutes=servicio.duracion)
    apertura = datetime.combine(fecha, INICIO_JORNADA)
    cierre = datetime.combine(fecha, FIN_JORNADA)
    if inicio < apertura:
        return 'unavailable', 'La jornada empieza a las 6:00 a. m.'
    if inicio >= cierre or fin > cierre:
        return 'unavailable', 'El servicio debe terminar antes o exactamente a las 8:00 p. m.'
    return None


def _motivo_anticipacion(fecha, hora_inicio, estilista):
    if anticipacion_suficiente(fecha, hora_inicio, estilista):
        return None
    if ConfiguracionAgenda.objects.filter(estilista=estilista).exists():
        return ('unavailable', 'La cita no cumple la anticipación mínima de reserva.')
    return ('unavailable', 'La cita debe solicitarse con más de una hora de anticipación.')


def _motivo_estilista(fecha, hora_inicio, servicio, estilista, excluir_cita_id=None):
    motivo = _motivo_anticipacion(fecha, hora_inicio, estilista)
    if motivo:
        return motivo
    if BloqueoAgenda.objects.filter(
        estilista=estilista,
        fecha_inicio__lte=fecha,
        fecha_fin__gte=fecha,
    ).exists():
        return 'unavailable', 'La estilista no atiende en esta fecha.'

    inicio_nuevo = datetime.combine(fecha, hora_inicio)
    fin_nuevo = inicio_nuevo + timedelta(minutes=servicio.duracion)
    if not _estilista_cubre_horario(estilista, inicio_nuevo, fin_nuevo):
        return 'unavailable', 'La franja queda fuera del horario configurado de la estilista.'

    ocupadas = Cita.objects.filter(
        estilista=estilista,
        fecha__gte=fecha - timedelta(days=1),
        fecha__lte=fecha,
        estado__in=('PENDIENTE', 'CONFIRMADA', 'EN_PROCESO'),
    )
    if excluir_cita_id is not None:
        ocupadas = ocupadas.exclude(pk=excluir_cita_id)
    for cita in ocupadas:
        inicio_existente = datetime.combine(cita.fecha, cita.hora_inicio)
        duracion_existente = (
            cita.duracion_aprobada
            if cita.duracion_aprobada is not None
            else cita.servicio.duracion
        )
        fin_existente = inicio_existente + timedelta(minutes=duracion_existente)
        if (
            inicio_nuevo < fin_existente + SEPARACION_ENTRE_CITAS
            and inicio_existente < fin_nuevo + SEPARACION_ENTRE_CITAS
        ):
            return 'occupied', 'Debe haber 60 minutos entre esta cita y otra cita activa.'
    return None


def evaluar_disponibilidad(fecha, hora_inicio, servicio, estilistas=None, excluir_cita_id=None):
    motivo = _validacion_base(fecha, hora_inicio, servicio)
    if motivo:
        return [], motivo
    if estilistas is None:
        estilistas = Estilista.objects.filter(
            persona__rol='estilista', persona__is_active=True
        ).select_related('persona').order_by('pk')
    estilistas = list(estilistas)
    if not estilistas:
        return [], ('unavailable', 'No hay una estilista habilitada para reservar.')

    disponibles = []
    motivos = []
    for estilista in estilistas:
        motivo = _motivo_estilista(
            fecha, hora_inicio, servicio, estilista, excluir_cita_id
        )
        if motivo is None:
            disponibles.append(estilista)
        else:
            motivos.append(motivo)
    return disponibles, (motivos[0] if motivos else None)


def estilistas_disponibles(fecha, hora_inicio, servicio, estilistas=None, excluir_cita_id=None):
    disponibles, _ = evaluar_disponibilidad(
        fecha, hora_inicio, servicio, estilistas, excluir_cita_id
    )
    return disponibles


def _inicios_jornada(fecha):
    inicio = datetime.combine(fecha, INICIO_JORNADA)
    cierre = datetime.combine(fecha, FIN_JORNADA)
    while inicio <= cierre:
        yield inicio.time()
        inicio += timedelta(minutes=INTERVALO_INICIO_MINUTOS)


def franjas_horarias(fecha, servicio, estilistas=None):
    if estilistas is None:
        estilistas = Estilista.objects.filter(
            persona__rol='estilista', persona__is_active=True
        ).select_related('persona').order_by('pk')
    estilistas = list(estilistas)
    franjas = []
    for hora_inicio in _inicios_jornada(fecha):
        disponibles, motivo = evaluar_disponibilidad(
            fecha, hora_inicio, servicio, estilistas
        )
        if disponibles:
            estado, texto = 'available', ''
        elif motivo:
            estado, texto = motivo
        else:
            estado, texto = 'unavailable', 'La franja no está disponible.'
        franjas.append({
            'hora': hora_inicio,
            'estado': estado,
            'disponible': bool(disponibles),
            'motivo': texto,
        })
    return franjas


def horarios_disponibles(fecha, servicio, estilistas=None):
    return [franja['hora'] for franja in franjas_horarias(fecha, servicio, estilistas) if franja['disponible']]


class HorarioForm(forms.ModelForm):
    dia_semana = forms.TypedChoiceField(
        choices=DIAS_SEMANA,
        coerce=int,
        widget=forms.Select(attrs={'class': 'w-full rounded-xl border border-rose-100 px-3 py-2 text-sm'}),
    )
    hora_inicio = forms.TimeField(
        widget=forms.TimeInput(
            format='%H:%M',
            attrs={'type': 'time', 'class': 'w-full rounded-xl border border-rose-100 px-3 py-2 text-sm'},
        ),
    )
    hora_fin = forms.TimeField(
        widget=forms.TimeInput(
            format='%H:%M',
            attrs={'type': 'time', 'class': 'w-full rounded-xl border border-rose-100 px-3 py-2 text-sm'},
        ),
    )
    activo = forms.BooleanField(required=False)

    class Meta:
        model = Horario
        fields = ('dia_semana', 'hora_inicio', 'hora_fin', 'activo')

    def __init__(self, *args, **kwargs):
        self.estilista = kwargs.pop('estilista', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        dia = cleaned_data.get('dia_semana')
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')
        if hora_inicio and hora_fin and hora_fin <= hora_inicio:
            self.add_error(
                'hora_fin',
                'La hora de cierre debe ser posterior a la hora de apertura.',
            )
        if (
            self.estilista
            and cleaned_data.get('activo')
            and dia is not None
            and hora_inicio
            and hora_fin
            and hora_fin > hora_inicio
        ):
            horarios_solapados = Horario.objects.filter(
                estilista=self.estilista,
                activo=True,
                dia_semana=dia,
                hora_inicio__lt=hora_fin,
                hora_fin__gt=hora_inicio,
            )
            if self.instance.pk:
                horarios_solapados = horarios_solapados.exclude(
                    pk=self.instance.pk
                )
            if horarios_solapados.exists():
                self.add_error(
                    'hora_inicio',
                    'Este horario se cruza con otro horario activo de ese día.',
                )
        return cleaned_data


class ReservarCitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = (
            'servicio',
            'fecha',
            'hora_inicio',
            'mensaje',
            'metodo_pago_preferido',
            'fecha_solicitada',
            'hora_solicitada',
        )
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'fecha_solicitada': forms.DateInput(attrs={'type': 'date'}),
            'hora_solicitada': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        data = kwargs.get('data', args[0] if args else None)
        if data is not None:
            data = data.copy()
            for source, target in (
                ('servicio_id', 'servicio'),
                ('hora', 'hora_inicio'),
                ('fecha_solicitada', 'fecha_solicitada'),
                ('hora_solicitada', 'hora_solicitada'),
            ):
                if target not in data and source in data:
                    data[target] = data[source]
            if 'data' in kwargs:
                kwargs['data'] = data
            else:
                args = (data, *args[1:])
        super().__init__(*args, **kwargs)
        self.fields['servicio'].queryset = Servicio.objects.filter(activo=True).order_by(
            'nombre'
        )
        self.fields['hora_inicio'].input_formats = [
            '%H:%M', '%H:%M:%S', '%I:%M %p'
        ]
        self.fields['hora_solicitada'].input_formats = self.fields['hora_inicio'].input_formats
        self.fields['fecha_solicitada'].required = False
        self.fields['hora_solicitada'].required = False
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                'class',
                'w-full px-4 py-2.5 rounded-xl border border-rose-100 bg-white text-sm',
            )

    def clean_fecha(self):
        fecha = self.cleaned_data['fecha']
        if fecha < timezone.localdate():
            raise ValidationError('La fecha de la cita no puede estar en el pasado.')
        return fecha

    def clean(self):
        cleaned_data = super().clean()
        servicio = cleaned_data.get('servicio')
        fecha = cleaned_data.get('fecha')
        hora_inicio = cleaned_data.get('hora_inicio')
        if servicio and fecha and hora_inicio:
            disponibles, motivo = evaluar_disponibilidad(fecha, hora_inicio, servicio)
            if not disponibles:
                self.add_error(
                    'hora_inicio',
                    ValidationError(motivo[1] if motivo else 'Ese horario no está disponible. Elige otro horario.'),
                )
        if not cleaned_data.get('fecha_solicitada'):
            cleaned_data['fecha_solicitada'] = cleaned_data.get('fecha')
        if not cleaned_data.get('hora_solicitada'):
            cleaned_data['hora_solicitada'] = cleaned_data.get('hora_inicio')
        return cleaned_data


class BloqueoAgendaForm(forms.ModelForm):
    class Meta:
        model = BloqueoAgenda
        fields = ('fecha_inicio', 'fecha_fin', 'motivo')
        widgets = {'fecha_inicio': forms.DateInput(attrs={'type':'date'}),
                   'fecha_fin': forms.DateInput(attrs={'type':'date'})}

    def clean(self):
        datos = super().clean()
        if datos.get('fecha_inicio') and datos.get('fecha_fin') and datos['fecha_fin'] < datos['fecha_inicio']:
            self.add_error('fecha_fin', 'La fecha final debe ser posterior o igual a la inicial.')
        return datos


class PoliticaAgendaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionAgenda
        fields = ('anticipacion_reserva_minutos', 'anticipacion_cancelacion_minutos')

    def clean(self):
        datos = super().clean()
        for key in self.fields:
            if datos.get(key) is not None and datos[key] > 43200:
                self.add_error(key, 'No puede superar 30 días.')
        return datos
