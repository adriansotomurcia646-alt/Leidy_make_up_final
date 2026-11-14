from django.contrib import admin
from .models import Cita, CitaArchivo, Horario, Mensaje, ConfiguracionAgenda, BloqueoAgenda, BitacoraCita, Notificacion

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'estilista', 'servicio', 'fecha', 'hora_inicio', 'estado')
    list_filter = ('estado','fecha')
    search_fields = ('cliente__persona__email','servicio__nombre')

admin.site.register((CitaArchivo,Horario,Mensaje,ConfiguracionAgenda,BloqueoAgenda,BitacoraCita,Notificacion))
