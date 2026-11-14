from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Persona, Cliente, Estilista, HistorialAcceso

@admin.register(Persona)
class PersonaAdmin(UserAdmin):
    list_display = ('username', 'email', 'rol', 'is_active', 'is_staff')
    list_filter = ('rol', 'is_active', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (('Leidy Make Up', {'fields': ('rol',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Leidy Make Up', {'fields': ('rol',)}),)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('persona', 'telefono', 'direccion')
    search_fields = ('persona__email','persona__first_name','persona__last_name')

@admin.register(Estilista)
class EstilistaAdmin(admin.ModelAdmin):
    list_display = ('persona', 'especialidad')


@admin.register(HistorialAcceso)
class HistorialAccesoAdmin(admin.ModelAdmin):
    """Registro de solo lectura para proteger trazabilidad de intentos de acceso."""
    list_display=('fecha','identificador','evento','rol_solicitado')
    list_filter=('evento','rol_solicitado')
    readonly_fields=('persona','identificador','evento','rol_solicitado','fecha')
    def has_add_permission(self,request):return False
    def has_change_permission(self,request,obj=None):return False
    def has_delete_permission(self,request,obj=None):return False
