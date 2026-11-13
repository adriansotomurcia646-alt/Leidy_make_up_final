from django.conf import settings
from django.contrib import admin
from django.urls import path, include

from App_inicio import views as inicio_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('administracion/', include('App_administracion.urls')),
    path('', inicio_views.home, name='home'),
    path('usuarios/', include('App_usuarios.urls')),
    path('agenda/', include('App_agenda.urls')),
    path('servicios/', include('App_servicios.urls')),
    path('facturacion/', include('App_facturacion.urls')),
]

# No publicar MEDIA_ROOT: los adjuntos de citas solo se sirven con
# App_agenda:descargar_adjunto, que exige permisos de la clienta/estilista.
