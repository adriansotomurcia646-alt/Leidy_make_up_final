"""Pruebas del registro directo y la estructura Persona/Cliente/Estilista."""
from django.test import TestCase
from django.urls import reverse
from .models import Persona, Cliente, Estilista, HistorialAcceso

class RegistroSinVerificacionTests(TestCase):
    def test_al_registrarse_el_cliente_esta_activo_y_puede_entrar(self):
        datos = {
            'nombre': 'Laura', 'apellido': 'Pérez', 'telefono': '3001234567',
            'email': 'LAURA@example.com', 'password': 'ClaveValida!2026-Citas',
        }
        respuesta = self.client.post(reverse('App_usuarios:registro'), datos)
        self.assertRedirects(respuesta, reverse('App_usuarios:login'))
        persona = Persona.objects.get(email='laura@example.com')
        self.assertTrue(persona.is_active)
        self.assertTrue(persona.check_password(datos['password']))
        self.assertTrue(Cliente.objects.filter(persona=persona).exists())
        self.assertFalse(Estilista.objects.filter(persona=persona).exists())
        # No se requiere clic en ningún enlace de verificación de correo.
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
