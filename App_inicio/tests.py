"""Pruebas del carrusel público controlado desde Administrador."""
from io import BytesIO
from tempfile import TemporaryDirectory

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.core.files.storage import FileSystemStorage
from unittest.mock import patch
from django.urls import reverse

from App_inicio.models import FotoCarrusel
from App_usuarios.models import Persona


def foto_de_prueba(nombre):
    buffer = BytesIO()
    Image.new('RGB', (110, 160), (180, 125, 100)).save(buffer, format='PNG')
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type='image/png')


class CarruselAdminTests(TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.patcher = patch.object(
            FotoCarrusel._meta.get_field('imagen'), 'storage',
            FileSystemStorage(location=self.temporal.name,
                              base_url='/media/servicios_publicos/'),
        )
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.admin = Persona.objects.create_user(
            username='test_admin_carrusel', password='ContraseñA_123!X',
            rol='administrador', is_staff=True,
        )
        self.client.force_login(self.admin)
        self.url = reverse('App_administracion:portada')

    def test_carga_multiple_y_presencia_en_ambas_paginas(self):
        respuesta = self.client.post(self.url, {
            'fotografias': [foto_de_prueba('uno.png'), foto_de_prueba('dos.png')],
            'mostrar_en_portada': 'on', 'mostrar_en_login': 'on',
        })
        self.assertRedirects(respuesta, self.url)
        self.assertEqual(FotoCarrusel.objects.count(), 2)
        self.assertContains(self.client.get('/?vista=publica'), 'data-maison-carousel')
        self.assertContains(self.client.get(reverse('App_usuarios:login') + '?vista=publica'), 'data-maison-carousel')
        self.client.logout()
        portada = self.client.get(reverse('home'))
        login = self.client.get(reverse('App_usuarios:login'))
        self.assertContains(portada, 'data-maison-carousel')
        self.assertContains(portada, 'carrusel/')
        self.assertContains(login, 'data-maison-carousel')
        self.assertContains(login, 'carrusel/')

    def test_carga_invalida_no_almacena_archivo(self):
        respuesta = self.client.post(self.url, {
            'fotografias': [SimpleUploadedFile('malo.png', b'no es imagen', content_type='image/png')],
            'mostrar_en_portada': 'on',
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(FotoCarrusel.objects.count(), 0)

    def test_sepuede_decidir_en_que_pagina_aparecer(self):
        foto = FotoCarrusel.objects.create(imagen=foto_de_prueba('inicial.png'))
        respuesta = self.client.post(reverse('App_administracion:portada_guardar', args=[foto.pk]), {
            'titulo': 'Trabajo destacado', 'orden': '3',
            'activa': 'on', 'mostrar_en_login': 'on',
        })
        self.assertRedirects(respuesta, self.url)
        foto.refresh_from_db()
        self.assertFalse(foto.mostrar_en_portada)
        self.assertTrue(foto.mostrar_en_login)
        self.assertEqual(foto.orden, 3)
        self.client.logout()
        self.assertNotContains(self.client.get(reverse('home')), foto.imagen.url)
        self.assertContains(self.client.get(reverse('App_usuarios:login')), foto.imagen.url)

    def test_eliminar_y_permisos(self):
        foto = FotoCarrusel.objects.create(imagen=foto_de_prueba('borrar.png'))
        self.client.post(reverse('App_administracion:portada_eliminar', args=[foto.pk]))
        self.assertFalse(FotoCarrusel.objects.filter(pk=foto.pk).exists())
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)
        cliente = Persona.objects.create_user(username='cliente_carrusel', password='ContraseñA_123!X', rol='cliente')
        self.client.force_login(cliente)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.post(self.url, {'fotografias': [foto_de_prueba('no.png')]}).status_code, 403)

    def test_limite_de_doce_imagenes_activas_por_pagina(self):
        for idx in range(12):
            FotoCarrusel.objects.create(imagen=foto_de_prueba(f'foto{idx}.png'))
        respuesta = self.client.post(self.url, {
            'fotografias': [foto_de_prueba('extra.png')],
            'mostrar_en_portada': 'on', 'mostrar_en_login': 'on',
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(FotoCarrusel.objects.count(), 12)

    def test_actualizar_no_acepta_orden_invalido(self):
        foto = FotoCarrusel.objects.create(imagen=foto_de_prueba('orden.png'))
        response = self.client.post(reverse('App_administracion:portada_guardar', args=[foto.pk]), {'orden': '-8'})
        self.assertRedirects(response, self.url)
        foto.refresh_from_db()
        self.assertEqual(foto.orden, 0)
