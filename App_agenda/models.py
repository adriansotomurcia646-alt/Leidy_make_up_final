from datetime import datetime, timedelta

from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

from App_usuarios.models import Cliente, Estilista
from App_servicios.models import Servicio


class Horario(models.Model):
	"""Jornada semanal de la estilista: determina cuándo se pueden ofrecer citas."""
	estilista = models.ForeignKey(Estilista, on_delete=models.CASCADE, related_name='horarios')
	dia_semana = models.PositiveSmallIntegerField(help_text='0 lunes, 6 domingo')
	hora_inicio = models.TimeField()
	hora_fin = models.TimeField()
	activo = models.BooleanField(default=True)

	def __str__(self):
		return f'{self.estilista} - día {self.dia_semana}'


class Cita(models.Model):
	"""Reserva con estados del flujo y horas de inicio/fin para impedir cruces."""
	ESTADOS = (
		('PENDIENTE', 'En espera'),
		('CONFIRMADA', 'Confirmada'),
		('EN_PROCESO', 'En proceso'),
		('FINALIZADA', 'Finalizada'),
		('RECHAZADA', 'Rechazada'),
		('CANCELADA', 'Cancelada'),
	)

	cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='citas')
	estilista = models.ForeignKey(Estilista, on_delete=models.CASCADE, related_name='citas')
	servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT, related_name='citas')
	fecha = models.DateField()
	hora_inicio = models.TimeField()
	hora_fin = models.TimeField()
	estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
	metodo_pago_preferido = models.CharField(max_length=20, choices=(('EFECTIVO','Efectivo'),('TRANSFERENCIA','Transferencia bancaria')), blank=True)
	mensaje = models.TextField(blank=True)
	notas = models.TextField(blank=True)
	fecha_solicitud = models.DateTimeField(auto_now_add=True)
	fecha_aceptacion = models.DateTimeField(null=True, blank=True)
	fecha_finalizacion = models.DateTimeField(null=True, blank=True)
	fecha_solicitada = models.DateField(null=True, blank=True)
	hora_solicitada = models.TimeField(null=True, blank=True)
	duracion_aprobada = models.PositiveIntegerField(null=True, blank=True)

	@property
	def hora(self):
		return self.hora_inicio

	@hora.setter
	def hora(self, value):
		self.hora_inicio = value

	@property
	def nota(self):
		return self.mensaje or self.notas

	@property
	def es_historica(self):
		return self.estado == 'CONFIRMADA' and self.fecha < timezone.localdate()

	@property
	def estado_visual(self):
		# Una fecha pasada no demuestra que el servicio se prestó.
		return self.estado

	@property
	def inicio_local(self):
		return timezone.make_aware(datetime.combine(self.fecha, self.hora_inicio), timezone.get_current_timezone())

	@property
	def puede_cancelar(self):
		if self.estado not in ('PENDIENTE','CONFIRMADA'):
			return False
		politica = ConfiguracionAgenda.objects.filter(estilista=self.estilista).first()
		minutos = politica.anticipacion_cancelacion_minutos if politica else 120
		return self.inicio_local >= timezone.now() + timedelta(minutes=minutos)

	@property
	def puede_reprogramar(self):
		return self.estado == 'PENDIENTE' and self.puede_cancelar

	def save(self, *args, **kwargs):
		update_fields = kwargs.get('update_fields')
		recalcular_intervalo = self._state.adding or (
			update_fields is not None
			and {'fecha', 'hora_inicio', 'servicio', 'duracion_aprobada'}
			.intersection(update_fields)
		)
		if recalcular_intervalo and self.fecha and self.hora_inicio and self.servicio_id:
			if self.duracion_aprobada is None:
				self.duracion_aprobada = self.servicio.duracion
			inicio = datetime.combine(self.fecha, self.hora_inicio)
			self.hora_fin = (
				inicio + timedelta(minutes=self.duracion_aprobada)
			).time()
			if update_fields is not None:
				kwargs['update_fields'] = set(update_fields) | {
					'hora_fin',
					'duracion_aprobada',
				}
		if self.estado == 'CONFIRMADA' and not self.fecha_aceptacion:
			self.fecha_aceptacion = timezone.now()
		if self.estado == 'FINALIZADA' and not self.fecha_finalizacion:
			self.fecha_finalizacion = timezone.now()
		super().save(*args, **kwargs)

	def __str__(self):
		return f'{self.servicio} - {self.fecha} {self.hora_inicio}'


class CitaArchivo(models.Model):
	"""Adjunto privado de una cita; su acceso se controla en la vista."""
	cita = models.ForeignKey(Cita, on_delete=models.CASCADE, related_name='archivos')
	archivo = models.FileField(upload_to='citas/archivos/%Y/%m/%d/', max_length=500)
	nombre_original = models.CharField(max_length=255, blank=True)
	tipo = models.CharField(max_length=30, blank=True)
	creado_en = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ('creado_en',)

	def __str__(self):
		return self.nombre_original or self.archivo.name


class Mensaje(models.Model):
	"""Chat interno entre cuentas autenticadas; no permite direcciones externas."""
	remitente = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='mensajes_enviados',
	)
	destinatario = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='mensajes_recibidos',
	)
	# FK opcional: mensajes de soporte general no siempre pertenecen a una cita.
	cita = models.ForeignKey(
		Cita, on_delete=models.SET_NULL, related_name='mensajes',
		blank=True, null=True,
	)
	contenido = models.CharField(max_length=2000)
	creado_en = models.DateTimeField(auto_now_add=True)
	leido = models.BooleanField(default=False)

	class Meta:
		ordering = ('creado_en',)

	def __str__(self):
		return f'Mensaje de {self.remitente} para {self.destinatario}'


class ConfiguracionAgenda(models.Model):
    """Anticipación de reserva y cancelación parametrizada por profesional."""
    """Políticas del salón; por defecto: reservar con 1 h, cancelar con 2 h."""
    estilista = models.OneToOneField(Estilista, on_delete=models.CASCADE, related_name='configuracion_agenda')
    anticipacion_reserva_minutos = models.PositiveIntegerField(default=60)
    anticipacion_cancelacion_minutos = models.PositiveIntegerField(default=120)

    def clean(self):
        if self.anticipacion_reserva_minutos > 43200 or self.anticipacion_cancelacion_minutos > 43200:
            raise ValidationError('La anticipación no puede superar 30 días.')

    def __str__(self):
        return f'Políticas de {self.estilista}'


class BloqueoAgenda(models.Model):
    """Intervalo de fechas que deshabilita las reservas por descansos o festivos."""
    estilista = models.ForeignKey(Estilista, on_delete=models.CASCADE, related_name='bloqueos')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    motivo = models.CharField(max_length=200)
    creado_en = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.fecha_fin and self.fecha_inicio and self.fecha_fin < self.fecha_inicio:
            raise ValidationError('La fecha final debe ser igual o posterior a la inicial.')

    def __str__(self):
        return f'{self.fecha_inicio} a {self.fecha_fin}: {self.motivo}'


class BitacoraCita(models.Model):
    """Registro de cambios de estado y reprogramaciones para auditoría."""
    cita = models.ForeignKey(Cita, on_delete=models.CASCADE, related_name='bitacora')
    persona = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=40)
    estado_anterior = models.CharField(max_length=20, blank=True)
    estado_nuevo = models.CharField(max_length=20, blank=True)
    detalle = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-fecha',)


class Notificacion(models.Model):
    """Aviso privado asociado a una persona, opcionalmente a su cita."""
    persona = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notificaciones')
    cita = models.ForeignKey(Cita, on_delete=models.CASCADE, null=True, blank=True)
    titulo = models.CharField(max_length=120)
    contenido = models.CharField(max_length=500)
    leida = models.BooleanField(default=False)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-creada_en',)
