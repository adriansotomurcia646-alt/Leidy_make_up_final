from django.urls import path
from . import views
app_name = 'App_facturacion'
urlpatterns = [
    path('inventario/',views.inventario_view,name='inventario'),
    path('reportes/',views.reportes_view,name='reportes'),
    path('citas/<int:cita_id>/cobro/',views.crear_cobro_view,name='crear_cobro'),
    path('citas/<int:cita_id>/pago/',views.registrar_pago_view,name='registrar_pago'),
    path('citas/<int:cita_id>/recibo/',views.recibo_view,name='recibo'),
    path('cierre-caja/',views.cierre_caja_view,name='cierre_caja'),
    path('reportes/exportar/<str:formato>/',views.exportar_reporte_view,name='exportar_reporte'),
]
