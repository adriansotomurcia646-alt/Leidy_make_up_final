"""Galerías compartidas por el panel de estilista y el de administración."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import ImagenServicio, validar_foto_servicio

LIMITE_IMAGENES = 12


def guardar_fotos(servicio, archivos):
    """Valida el lote completo antes de escribir y limita cada galería a 12."""
    archivos = list(archivos)
    if not archivos:
        return 0
    cantidad = servicio.imagenes.count()
    if cantidad + len(archivos) > LIMITE_IMAGENES:
        raise ValidationError(
            f'Puedes subir hasta {LIMITE_IMAGENES} fotografías por servicio. '
            f'Este servicio ya tiene {cantidad}.'
        )
    for archivo in archivos:
        validar_foto_servicio(archivo)
    with transaction.atomic():
        for posicion, archivo in enumerate(archivos, start=cantidad):
            ImagenServicio.objects.create(
                servicio=servicio, imagen=archivo,
                orden=posicion, es_portada=(posicion == 0),
            )
    return len(archivos)


@receiver(post_delete, sender=ImagenServicio)
def eliminar_archivo_eliminar_registro(sender, instance, **kwargs):
    """Evita que queden fotos huérfanas incluso al eliminar un Servicio."""
    if instance.imagen:
        almacenamiento = instance.imagen.storage
        nombre = instance.imagen.name
        transaction.on_commit(lambda: almacenamiento.delete(nombre))
