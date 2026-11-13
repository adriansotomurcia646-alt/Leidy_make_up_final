from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Q
from django.db.models.functions import Lower


class Persona(AbstractUser):
	"""Cuenta base del sistema. AbstractUser ya contiene usuario y contraseña cifrada."""
	ROLES = (
		('cliente', 'Cliente'),
		('estilista', 'Estilista'),
		('administrador', 'Administrador'),
	)

	rol = models.CharField(max_length=20, choices=ROLES, default='cliente')

	class Meta:
		# Correo único sin distinguir mayúsculas, salvo cuentas internas sin email.
		constraints = [
			models.UniqueConstraint(
				Lower('email'),
				condition=~Q(email=''),
				name='persona_email_unico_ci',
			),
		]

	@property
	def rol_efectivo(self):
		"""El privilegio de administrador requiere un perfil real y activo de personal."""
		if self.is_superuser:
			return 'administrador'
		if self.rol == 'administrador' and self.is_staff:
			return 'administrador'
		return self.rol

	def save(self, *args, **kwargs):
		# Un superusuario del panel Django siempre debe verse como Administrador.
		if self.is_superuser:
			self.rol = 'administrador'
			self.is_staff = True
			if kwargs.get('update_fields') is not None:
				kwargs['update_fields'] = set(kwargs['update_fields']) | {'rol', 'is_staff'}
		super().save(*args, **kwargs)

	def __str__(self):
		return self.get_full_name() or self.username

	def es_cliente(self):
		return hasattr(self, 'cliente')

	def es_estilista(self):
		return hasattr(self, 'estilista')


class Estilista(models.Model):
	"""Información profesional específica, vinculada a una sola cuenta Persona."""
	persona = models.OneToOneField(Persona, on_delete=models.CASCADE, related_name='estilista')
	especialidad = models.CharField(max_length=120, blank=True)

	def __str__(self):
		return str(self.persona)


class Cliente(models.Model):
	"""Datos de contacto adicionales del cliente sin duplicar sus credenciales."""
	persona = models.OneToOneField(Persona, on_delete=models.CASCADE, related_name='cliente')
	telefono = models.CharField(max_length=30, blank=True)
	direccion = models.CharField(max_length=255, blank=True)

	@property
	def username(self):
		return self.persona.username

	def get_full_name(self):
		return self.persona.get_full_name()

	@property
	def profile(self):
		return self

	def __str__(self):
		return str(self.persona)


class HistorialAcceso(models.Model):
    """Auditoría de acceso: registra resultados sin almacenar contraseñas."""
    persona = models.ForeignKey(Persona, on_delete=models.SET_NULL, null=True, blank=True)
    identificador = models.CharField(max_length=150, blank=True)
    evento = models.CharField(max_length=30, choices=(('LOGIN', 'Inicio de sesión'), ('FALLO', 'Acceso rechazado'), ('LOGOUT', 'Cierre de sesión')))
    rol_solicitado = models.CharField(max_length=20, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-fecha',)

    def __str__(self):
        return f'{self.evento} · {self.identificador} · {self.fecha}'
