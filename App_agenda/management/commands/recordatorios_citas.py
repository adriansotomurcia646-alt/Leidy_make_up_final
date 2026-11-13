"""Ejecutar por cron cada hora para crear avisos locales idempotentes."""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from App_agenda.models import Cita, Notificacion
from App_agenda.servicios import notificar

class Command(BaseCommand):
    help='Crea recordatorios internos 24 horas antes. Ejecutar desde un scheduler.'

    def handle(self,*args,**kwargs):
        desde = timezone.now() + timedelta(hours=23)
        hasta = timezone.now() + timedelta(hours=25)
        creados=0
        for cita in Cita.objects.filter(estado='CONFIRMADA').select_related('cliente__persona','servicio'):
            if desde <= cita.inicio_local <= hasta:
                titulo=f'Recordatorio de cita #{cita.pk}'
                if not Notificacion.objects.filter(persona=cita.cliente.persona,cita=cita,titulo=titulo).exists():
                    notificar(cita.cliente.persona,titulo,
                             f'{cita.servicio.nombre}: {cita.fecha:%d/%m/%Y} {cita.hora_inicio:%H:%M}',cita)
                    creados+=1
        self.stdout.write(f'Recordatorios internos creados: {creados}')
