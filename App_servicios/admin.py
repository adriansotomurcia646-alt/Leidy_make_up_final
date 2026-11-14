from django.contrib import admin
from .models import ImagenServicio, Servicio


class ImagenServicioInline(admin.TabularInline):
    model = ImagenServicio
    extra = 1
    max_num = 12


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'duracion', 'activo')
    list_filter = ('activo', 'categoria')
    search_fields = ('nombre', 'descripcion')
    inlines = (ImagenServicioInline,)


@admin.register(ImagenServicio)
class ImagenServicioAdmin(admin.ModelAdmin):
    list_display = ('servicio', 'orden', 'es_portada', 'creada_en')
    list_filter = ('es_portada',)
