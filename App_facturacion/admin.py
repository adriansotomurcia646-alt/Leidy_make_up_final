from django.contrib import admin
from .models import RegistroCobro, Pago, CierreCaja

class SoloConsultaAdmin(admin.ModelAdmin):
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
    def has_view_permission(self, request, obj=None): return request.user.is_staff

@admin.register(RegistroCobro)
class RegistroCobroAdmin(SoloConsultaAdmin):
    list_display = ('cita','monto_total','monto_pagado','saldo_pendiente','fecha')

@admin.register(Pago)
class PagoAdmin(SoloConsultaAdmin):
    list_display = ('registro_cobro','monto','metodo','fecha','recibido_por')

@admin.register(CierreCaja)
class CierreCajaAdmin(SoloConsultaAdmin):
    list_display = ('fecha','monto_efectivo','monto_transferencia','cerrado_por')
