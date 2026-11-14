from django.contrib import admin
from django.utils.html import format_html
from .models import FotoCarrusel


@admin.register(FotoCarrusel)
class FotoCarruselAdmin(admin.ModelAdmin):
    """Control individual complementario a la carga múltiple del panel del salón."""
    list_display = ('miniatura', 'titulo', 'orden', 'activa', 'mostrar_en_portada', 'mostrar_en_login')
    list_display_links = ('miniatura', 'titulo')
    list_editable = ('orden', 'activa', 'mostrar_en_portada', 'mostrar_en_login')
    list_filter = ('activa', 'mostrar_en_portada', 'mostrar_en_login')
    search_fields = ('titulo',)
    ordering = ('orden', 'pk')
    readonly_fields = ('miniatura', 'creada_en')
    save_on_top = True

    @admin.display(description='Vista previa')
    def miniatura(self, obj):
        if not obj or not obj.imagen:
            return '—'
        return format_html(
            '<img src="{}" alt="Vista previa" style="height:70px;width:70px;object-fit:cover;border-radius:9px" />',
            obj.imagen.url,
        )
