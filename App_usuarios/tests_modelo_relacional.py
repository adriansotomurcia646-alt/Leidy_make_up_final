"""Pruebas de registro validado y la estructura Persona/Cliente/Estilista."""
import re
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from .models import Persona, Cliente, Estilista, HistorialAcceso

@override_settings(MAILERS={'default': {'BACKEND': 'django.core.mail.backends.locmem.EmailBackend'}})
class RegistroConVerificacionTests(TestCase):
    def setUp(self):
        cache.clear()
    def test_al_registrarse_el_cliente_esta_activo_y_puede_entrar(self):
        datos = {
            'nombre': 'Laura', 'apellido': 'Pérez', 'telefono': '3001234567',
            'email': 'LAURA@example.com', 'password': 'ClaveValida!2026-Citas',
        }
        respuesta = self.client.post(reverse('App_usuarios:registro'), datos)
        self.assertRedirects(respuesta, reverse('App_usuarios:confirmar_registro'))
        self.assertFalse(Persona.objects.filter(email='laura@example.com').exists())
        codigo = re.search(r'\b(\d{6})\b', mail.outbox[-1].body).group(1)
        self.assertRedirects(self.client.post(reverse('App_usuarios:confirmar_registro'), {'codigo':codigo}), reverse('App_usuarios:login'))
        persona = Persona.objects.get(email='laura@example.com')
        self.assertTrue(persona.is_active)
        self.assertTrue(persona.check_password(datos['password']))
        self.assertTrue(Cliente.objects.filter(persona=persona).exists())
        self.assertFalse(Estilista.objects.filter(persona=persona).exists())
        # Solo después del código válido es posible iniciar sesión.
        acceso = self.client.post(reverse('App_usuarios:login'), {
            'username': 'laura@example.com',
            'password': datos['password'], 'rol': 'cliente',
        })
        self.assertEqual(acceso.status_code, 302)
        self.assertTrue(HistorialAcceso.objects.filter(persona=persona,evento='LOGIN').exists())

    def test_apellido_y_telefono_son_obligatorios(self):
        datos = {'nombre':'Laura','apellido':'','telefono':'',
                 'email':'laura@example.com','password':'ClaveValida!2026-Citas'}
        r = self.client.post(reverse('App_usuarios:registro'),datos)
        self.assertEqual(r.status_code,200)
        self.assertEqual(Persona.objects.count(),0)
        self.assertIn('apellido',r.context['form'].errors)
        self.assertIn('telefono',r.context['form'].errors)
