import uuid
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.db import models


def almacenamiento_fotos_publicas():
    """Aísla las fotos públicas de los adjuntos privados de las citas."""
    return storages['servicios_publicos']


def ruta_foto_servicio(instance, filename):
    extension = Path(filename).suffix.lower()
    if extension not in ('.jpg', '.jpeg', '.png', '.webp'):
        extension = '.jpg'
    return f'{instance.servicio_id}/{uuid.uuid4().hex}{extension}'


def validar_foto_servicio(upload):
    """Comprueba el contenido de la imagen, no solo su extensión."""
    if not upload:
        raise ValidationError('Selecciona una fotografía.')
    if upload.size > 5 * 1024 * 1024:
        raise ValidationError('Cada imagen debe pesar como máximo 5 MB.')
    try:
        archivo = getattr(upload, 'file', upload)
        posicion = archivo.tell()
        with Image.open(archivo) as foto:
            if foto.format not in ('JPEG', 'PNG', 'WEBP'):
                raise ValidationError('Solo se permiten fotografías JPG, PNG o WebP.')
            if foto.width * foto.height > 24_000_000:
                raise ValidationError('La imagen supera el tamaño máximo de 24 megapíxeles.')
            foto.verify()
        archivo.seek(posicion)
    except ValidationError:
        try: archivo.seek(0)
        except (AttributeError, ValueError): pass
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, AttributeError):
        try: archivo.seek(0)
        except (AttributeError, ValueError): pass
        raise ValidationError('El archivo no es una imagen válida.')



class Servicio(models.Model):
    """Catálogo con desactivación lógica; el historial nunca se borra en cascada."""
    nombre = models.CharField(max_length=150)
    categoria = models.CharField(max_length=100, blank=True, default='General')
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(decimal_places=2, max_digits=10)
    duracion = models.PositiveIntegerField(help_text='Duración en minutos')
    es_demo = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    @property
    def foto_portada(self):
        """La primera imagen es portada, o la seleccionada como tal."""
        return self.imagenes.first()

    def __str__(self):
        return f"{self.nombre} - ${self.precio}"


class ImagenServicio(models.Model):
    """Galería pública de cada servicio: una relación uno a muchos."""
    servicio = models.ForeignKey(
        Servicio, on_delete=models.CASCADE, related_name='imagenes',
    )
    imagen = models.ImageField(
        upload_to=ruta_foto_servicio, storage=almacenamiento_fotos_publicas,
        validators=[validar_foto_servicio],
    )
    descripcion = models.CharField(max_length=150, blank=True)
    es_portada = models.BooleanField(default=False)
    orden = models.PositiveSmallIntegerField(default=0)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-es_portada', 'orden', 'pk')

    def __str__(self):
        return f'Foto de {self.servicio.nombre} ({self.pk})'
