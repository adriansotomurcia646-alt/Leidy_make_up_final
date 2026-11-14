"""Operaciones de negocio compartidas por las vistas de agenda."""
from django.db import transaction
from django.utils import timezone
from .models import BitacoraCita, Notificacion


def registrar_evento(cita, usuario, accion, anterior='', nuevo='', detalle=''):
    BitacoraCita.objects.create(
        cita=cita, persona=usuario, accion=accion,
        estado_anterior=anterior, estado_nuevo=nuevo, detalle=detalle,
    )


def notificar(usuario, titulo, contenido, cita=None):
    if usuario and usuario.is_active:
        return Notificacion.objects.create(
            persona=usuario, cita=cita, titulo=titulo, contenido=contenido,
        )


def registrar_cambio(cita, usuario, accion, anterior, detalle=''):
    registrar_evento(cita, usuario, accion, anterior, cita.estado, detalle)
    notificar(cita.cliente.persona, f'Cita {cita.get_estado_display().lower()}',
             f'{cita.servicio.nombre}: {cita.fecha:%d/%m/%Y} a las {cita.hora_inicio:%H:%M}.', cita)
