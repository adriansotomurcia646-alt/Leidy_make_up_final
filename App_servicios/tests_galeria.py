"""Pruebas de integridad, privacidad y disponibilidad de la galería."""
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from App_usuarios.models import Persona, Cliente, Estilista
from .models import Servicio, ImagenServicio


def foto_prueba(nombre='foto.png'):
    buffer = BytesIO()
    Image.new('RGB', (60, 40), (203, 158, 177)).save(buffer, 'PNG')
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type='image/png')


class GaleriaTests(TestCase):
    def setUp(self):
        self.stylist = Persona.objects.create_user(username='artista', password='Prueba!2026B', rol='estilista')
        Estilista.objects.create(persona=self.stylist)
        self.cliente = Persona.objects.create_user(username='clienta', password='Prueba!2026B', rol='cliente')
        Cliente.objects.create(persona=self.cliente)
        self.servicio = Servicio.objects.create(nombre='Maquillaje de noche', categoria='Maquillaje', precio='100000', duracion=60)

    def tearDown(self):
        # Los hooks on_commit del TestCase no ejecutan borrado físico.
        for foto in ImagenServicio.objects.all():
            if foto.imagen: foto.imagen.storage.delete(foto.imagen.name)

    def test_estilista_puede_cargar_varias_fotos_y_cliente_verlas(self):
        self.client.force_login(self.stylist)
        response = self.client.post(reverse('App_servicios:editar', args=[self.servicio.pk]), {
            'nombre': self.servicio.nombre, 'categoria': self.servicio.categoria,
            'descripcion': 'Maquillaje artístico', 'precio': '100000', 'duracion': 60,
            'fotografias': [foto_prueba('primera.png'), foto_prueba('segunda.png')],
        })
        self.assertRedirects(response, reverse('App_servicios:lista'))
        self.assertEqual(self.servicio.imagenes.count(), 2)
        portada = self.servicio.imagenes.first()
        self.assertTrue(portada.es_portada)
        self.client.force_login(self.cliente)
        detalle = self.client.get(reverse('App_servicios:detalle', args=[self.servicio.pk]))
        self.assertEqual(detalle.status_code, 200)
        self.assertContains(detalle, 'imagen-principal')
        self.assertContains(detalle, 'data-image-url=', count=2)
        listado = self.client.get(reverse('App_servicios:lista'))
        self.assertContains(listado, portada.imagen.url)

    def test_cliente_no_puede_eliminar_ni_cambiar_portadas(self):
        foto = ImagenServicio.objects.create(servicio=self.servicio, imagen=foto_prueba(), es_portada=True)
        self.client.force_login(self.cliente)
        for url in ('App_servicios:eliminar_imagen', 'App_servicios:portada_imagen'):
            self.assertEqual(self.client.post(reverse(url, args=[foto.pk])).status_code, 403)
        self.assertTrue(ImagenServicio.objects.filter(pk=foto.pk).exists())

    def test_no_permite_archivos_que_no_son_imagen(self):
        self.client.force_login(self.stylist)
        respuesta = self.client.post(reverse('App_servicios:editar', args=[self.servicio.pk]), {
            'nombre': self.servicio.nombre, 'categoria': self.servicio.categoria,
            'descripcion': '', 'precio': '100000', 'duracion': 60,
            'fotografias': [SimpleUploadedFile('falso.png', b'<script>malicious</script>', content_type='image/png')],
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'El archivo no es una imagen válida')
        self.assertEqual(self.servicio.imagenes.count(), 0)

    def test_fotos_no_expone_archivos_privados_de_citas(self):
        # En DEBUG solo se publica el prefijo /media/servicios_publicos/.
        response = self.client.get('/media/citas/archivo-privado.pdf')
        self.assertEqual(response.status_code, 404)
