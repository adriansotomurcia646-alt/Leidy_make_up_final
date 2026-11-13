from django.db import models
from App_usuarios.models import Cliente
from App_agenda.models import Cita
from decimal import Decimal


class RegistroCobro(models.Model):
	"""Total, abonos y saldo de una cita; no equivale a facturación DIAN."""
	cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='registros_cobro')
	cita = models.OneToOneField(Cita, on_delete=models.PROTECT, related_name='registro_cobro')
	monto_total = models.DecimalField(max_digits=10, decimal_places=2)
	monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
	saldo_pendiente = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
	fecha = models.DateField(auto_now_add=True)

	def __str__(self):
		return f'Cobro {self.cliente} - {self.fecha}'


class Pago(models.Model):
    """Movimiento financiero con método, monto y persona que recibió el dinero."""
    METODOS = (('EFECTIVO', 'Efectivo'), ('TRANSFERENCIA', 'Transferencia bancaria'))
    registro_cobro = models.ForeignKey(RegistroCobro, on_delete=models.PROTECT, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo = models.CharField(max_length=20, choices=METODOS)
    referencia = models.CharField(max_length=100, blank=True)
    recibido_por = models.ForeignKey('App_usuarios.Persona', null=True, on_delete=models.SET_NULL)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-fecha',)

    def __str__(self):
        return f'Pago #{self.pk} - ${self.monto}'


class CierreCaja(models.Model):
    """Consolidado de los pagos por día y método, sin duplicar cierres."""
    fecha = models.DateField(unique=True)
    monto_efectivo = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    monto_transferencia = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    cerrado_por = models.ForeignKey('App_usuarios.Persona', on_delete=models.PROTECT)
    cerrado_en = models.DateTimeField(auto_now_add=True)

    @property
    def total(self):
        return self.monto_efectivo + self.monto_transferencia
