"""Cobros del salón. Los pagos son registros de dinero recibido, no pasarelas."""
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from App_agenda.servicios import notificar
from .models import RegistroCobro, Pago, CierreCaja


def obtener_cobro(cita):
    cobro, _ = RegistroCobro.objects.get_or_create(
        cita=cita,
        defaults={
            'cliente': cita.cliente,
            'monto_total': cita.servicio.precio,
            'monto_pagado': Decimal('0.00'),
            'saldo_pendiente': cita.servicio.precio,
        },
    )
    return cobro


@transaction.atomic
def registrar_pago(cita, monto, metodo, usuario, referencia=''):
    if cita.estado not in ('CONFIRMADA', 'EN_PROCESO', 'FINALIZADA'):
        raise ValidationError('Solo se pueden registrar pagos de citas confirmadas, en proceso o finalizadas.')
    if metodo not in ('EFECTIVO','TRANSFERENCIA'):
        raise ValidationError('Selecciona efectivo o transferencia bancaria.')
    try:
        monto = Decimal(str(monto))
    except Exception as exc:
        raise ValidationError('Monto de pago inválido.') from exc
    if not monto.is_finite() or monto <= 0 or monto.as_tuple().exponent < -2:
        raise ValidationError('Ingresa un monto positivo de máximo dos decimales.')
    if monto > Decimal('99999999.99'):
        raise ValidationError('El importe excede el valor máximo permitido.')
    if CierreCaja.objects.filter(fecha=timezone.localdate()).exists():
        raise ValidationError('La caja de hoy está cerrada. No se pueden registrar más pagos.')
    cobro = obtener_cobro(cita)
    cobro = RegistroCobro.objects.select_for_update().get(pk=cobro.pk)
    if monto > cobro.saldo_pendiente:
        raise ValidationError('El abono no puede exceder el saldo pendiente.')
    pago = Pago.objects.create(registro_cobro=cobro, monto=monto, metodo=metodo,
                              referencia=referencia[:100], recibido_por=usuario)
    cobro.monto_pagado = (cobro.monto_pagado + monto).quantize(Decimal('.01'))
    cobro.saldo_pendiente = (cobro.monto_total - cobro.monto_pagado).quantize(Decimal('.01'))
    cobro.save(update_fields=['monto_pagado', 'saldo_pendiente'])
    notificar(cita.cliente.persona, 'Pago registrado',
             f'Se registró un abono de ${monto} para {cita.servicio.nombre}.', cita)
    return pago
