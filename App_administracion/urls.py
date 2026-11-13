"""Rutas exclusivas del administrador (nunca compartidas con la estilista)."""
from django.urls import path
from . import views
app_name = 'App_administracion'
urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('usuarios/', views.usuarios, name='usuarios'),
    path('usuarios/nuevo/', views.usuario_crear, name='usuario_crear'),
    path('usuarios/<int:pk>/editar/', views.usuario_editar, name='usuario_editar'),
    path('usuarios/<int:pk>/estado/', views.usuario_estado, name='usuario_estado'),
    path('servicios/', views.servicios, name='servicios'),
    path('servicios/<int:pk>/editar/', views.servicio_editar, name='servicio_editar'),
    path('servicios/<int:pk>/estado/', views.servicio_estado, name='servicio_estado'),
    path('agenda/', views.agenda, name='agenda'),
    path('agenda/<int:pk>/reasignar/', views.reasignar, name='reasignar'),
    path('agenda/bloquear/', views.bloquear, name='bloquear'),
    path('agenda/politicas/', views.politicas, name='politicas'),
    path('clientes/', views.clientes, name='clientes'),
    path('reportes/', views.reportes, name='reportes'),
    path('reportes/exportar/<str:formato>/', views.exportar, name='exportar'),
    path('auditoria/', views.auditoria, name='auditoria'),
    path('mensajes/', views.mensajes_admin, name='mensajes'),
    path('archivos/', views.archivos, name='archivos'),
    path('caja/', views.caja, name='caja'),
    path('caja/cerrar/', views.cerrar_caja, name='cerrar_caja'),
    path('respaldo/', views.respaldar, name='respaldar'),
    path('ayuda/', views.ayuda, name='ayuda'),
]
