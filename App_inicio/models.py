"""Carrusel editable desde el área de administrador, sin mezclar archivos privados."""
import uuid
from pathlib import Path

from django.core.files.storage import storages
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from App_servicios.models import validar_foto_servicio


def guardar_en_galeria_publica():
    """Usa el mismo almacenamiento público persistente que las fotos de servicios."""
    return storages['servicios_publicos']


def ubicacion_foto(instance, nombre_archivo):
    extension = Path(nombre_archivo).suffix.lower()
    if extension not in ('.jpg', '.jpeg', '.png', '.webp'):
        extension = '.jpg'
    return f'carrusel/{uuid.uuid4().hex}{extension}'


class FotoCarrusel(models.Model):
    """Imágenes visibles en la portada y/o pantalla de acceso."""
    imagen = models.ImageField(
        'fotografía',
        upload_to=ubicacion_foto,
        storage=guardar_en_galeria_publica,
        validators=[validar_foto_servicio],
    )
    titulo = models.CharField('texto alternativo', max_length=140, blank=True)
    orden = models.PositiveSmallIntegerField('orden de aparición', default=0)
    activa = models.BooleanField('publicada', default=True)
    mostrar_en_portada = models.BooleanField('mostrar en portada', default=True)
    mostrar_en_login = models.BooleanField('mostrar en inicio de sesión', default=True)
    creada_en = models.DateTimeField('fecha de carga', auto_now_add=True)

    def clean(self):
        super().clean()
        if not self.activa:
            return
        for campo, destino in (
            ('mostrar_en_portada', 'portada'),
            ('mostrar_en_login', 'inicio de sesión'),
        ):
            if getattr(self, campo) and FotoCarrusel.objects.filter(
                activa=True, **{campo: True},
            ).exclude(pk=self.pk).count() >= 12:
                raise ValidationError({campo: f'Solo se permiten 12 fotos activas en {destino}.'})

    class Meta:
        verbose_name = 'fotografía del carrusel'
        verbose_name_plural = 'fotografías del carrusel'
        ordering = ('orden', 'pk')

    def __str__(self):
        return self.titulo or f'Fotografía {self.pk}'


@receiver(post_delete, sender=FotoCarrusel)
def limpiar_foto_borrada(sender, instance, **kwargs):
    """Evita mantener imágenes huérfanas al borrar, también en borrados masivos."""
    if instance.imagen and instance.imagen.name:
        storage = instance.imagen.storage
        nombre = instance.imagen.name
        transaction.on_commit(lambda: storage.delete(nombre))


@receiver(pre_save, sender=FotoCarrusel)
def limpiar_foto_reemplazada(sender, instance, **kwargs):
    if not instance.pk:
        return
    anterior = FotoCarrusel.objects.filter(pk=instance.pk).only('imagen').first()
    if anterior and anterior.imagen.name and anterior.imagen.name != instance.imagen.name:
        storage = anterior.imagen.storage
        nombre = anterior.imagen.name
        transaction.on_commit(lambda: storage.delete(nombre))
