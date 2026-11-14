import re
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Cliente, Estilista, Persona


@override_settings(MAILERS={'default': {'BACKEND': 'django.core.mail.backends.locmem.EmailBackend'}})
class AccountWorkflowTests(TestCase):
	def setUp(self):
		cache.clear()

	def confirmar_ultimo_codigo(self):
		codigo = re.search(r'\b(\d{6})\b', mail.outbox[-1].body).group(1)
		return self.client.post(reverse('App_usuarios:confirmar_registro'), {'codigo': codigo})

	def test_online_user_manual_is_public_and_covers_the_existing_flows(self):
		response = self.client.get(reverse('App_usuarios:ayuda'))

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'App_usuarios/C_ayuda.html')
		for instruction in (
			'Registrarte',
			'Iniciar sesión',
			'Consultar los servicios',
			'Solicitar y agendar una cita',
			'Consultar el estado',
			'Cancelar una cita',
			'Pendiente',
			'Confirmada',
		):
			with self.subTest(instruction=instruction):
				self.assertContains(response, instruction)

	def test_duplicate_email_registration_shows_a_clear_error(self):
		Persona.objects.create_user(
			username='existing@example.com',
			email='existing@example.com',
			password='S3cure!LadyMakeup2026',
		)

		response = self.client.post(
			reverse('App_usuarios:registro'),
			{
				'nombre': 'Nueva',
				'apellido': 'Soto',
				'email': 'EXISTING@example.com',
				'telefono': '3001234567',
				'password': 'S3cure!LadyMakeup2026',
			},
			follow=True,
		)

		self.assertContains(response, 'Este correo electrónico ya está registrado.')
		self.assertContains(response, 'role="alert"')
		self.assertContains(response, 'id="email-error"')
		self.assertEqual(Persona.objects.count(), 1)

	def test_registration_stores_password_with_django_hash_and_creates_one_client_profile(self):
		password = 'S3cure!LadyMakeup2026'
		response = self.client.post(
			reverse('App_usuarios:registro'),
			{
				'nombre': '  Ana  ',
				'apellido': '  Ríos  ',
				'email': '  ANA@example.com ',
				'telefono': ' 3001234567 ',
				'password': password,
				'rol': 'estilista',
			},
			follow=True,
		)

		self.assertRedirects(response, reverse('App_usuarios:confirmar_registro'))
		self.assertFalse(Persona.objects.filter(email='ana@example.com').exists())
		self.assertRedirects(self.confirmar_ultimo_codigo(), reverse('App_usuarios:login'))
		persona = Persona.objects.get(email='ana@example.com')
		self.assertEqual(persona.rol, 'cliente')
		self.assertEqual(persona.first_name, 'Ana')
		self.assertEqual(persona.last_name, 'Ríos')
		self.assertTrue(persona.check_password(password))
		self.assertNotEqual(persona.password, password)
		self.assertEqual(Cliente.objects.filter(persona=persona).count(), 1)
		self.assertFalse(Estilista.objects.filter(persona=persona).exists())

	def test_registration_requires_all_client_fields_without_creating_records(self):
		valid_data = {
			'nombre': 'Ana',
			'apellido': 'Soto',
			'email': 'ana@example.com',
			'telefono': '3001234567',
			'password': 'S3cure!LadyMakeup2026',
		}
		for field, expected_error in (
			('nombre', 'Completa tu nombre.'),
			('apellido', 'Completa tus apellidos.'),
			('telefono', 'Completa tu teléfono.'),
			('email', 'Completa tu correo electrónico.'),
			('password', 'Completa tu contraseña.'),
		):
			with self.subTest(field=field):
				data = {**valid_data, field: ''}
				response = self.client.post(
					reverse('App_usuarios:registro'),
					data,
				)

				self.assertEqual(response.status_code, 200)
				self.assertContains(response, expected_error)
				if field != 'apellido':
					self.assertContains(response, 'value="Soto"')
				if field != 'telefono':
					self.assertContains(response, 'value="3001234567"')
				self.assertEqual(Persona.objects.count(), 0)
				self.assertEqual(Cliente.objects.count(), 0)

	def test_registration_rejects_invalid_email_and_preserves_other_values(self):
		response = self.client.post(
			reverse('App_usuarios:registro'),
			{
				'nombre': 'Lucía',
				'apellido': 'López',
				'email': 'correo-no-valido',
				'telefono': '3007654321',
				'password': 'S3cure!LadyMakeup2026',
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Introduce un correo electrónico válido.')
		self.assertContains(response, 'value="Lucía"')
		self.assertContains(response, 'value="López"')
		self.assertContains(response, 'value="3007654321"')
		self.assertNotContains(response, 'value="S3cure!LadyMakeup2026"')
		self.assertEqual(Persona.objects.count(), 0)
		self.assertEqual(Cliente.objects.count(), 0)

	def test_registration_rejects_password_that_fails_django_password_policy(self):
		response = self.client.post(
			reverse('App_usuarios:registro'),
			{
				'nombre': 'Ana',
				'apellido': 'Soto',
				'email': 'ana@example.com',
				'telefono': '3001234567',
				'password': 'password',
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.context['form'].has_error('password'))
		self.assertEqual(Persona.objects.count(), 0)
		self.assertEqual(Cliente.objects.count(), 0)

	def test_public_registration_creates_a_client_account_and_profile(self):
		response = self.client.post(
			reverse('App_usuarios:registro'),
			{
				'nombre': 'Adrián',
				'apellido': 'Soto',
				'email': 'adrian@example.com',
				'telefono': '3001234567',
				'password': 'S3cure!LadyMakeup2026',
			},
		)

		self.assertRedirects(response, reverse('App_usuarios:confirmar_registro'))
		self.assertEqual(Persona.objects.count(), 0)
		self.assertRedirects(self.confirmar_ultimo_codigo(), reverse('App_usuarios:login'))
		persona = Persona.objects.get(email='adrian@example.com')
		self.assertEqual(persona.rol, 'cliente')
		self.assertTrue(Cliente.objects.filter(persona=persona).exists())
		self.assertFalse(Estilista.objects.filter(persona=persona).exists())

	def test_public_registration_cannot_assign_the_stylist_role(self):
		response = self.client.post(
			reverse('App_usuarios:registro'),
			{
				'nombre': 'Cuenta',
				'apellido': 'Manipulada',
				'email': 'forged@example.com',
				'telefono': '3001234567',
				'password': 'S3cure!LadyMakeup2026',
				'rol': 'estilista',
			},
		)

		self.assertRedirects(response, reverse('App_usuarios:confirmar_registro'))
		self.assertRedirects(self.confirmar_ultimo_codigo(), reverse('App_usuarios:login'))
		persona = Persona.objects.get(email='forged@example.com')
		self.assertEqual(persona.rol, 'cliente')
		self.assertFalse(Estilista.objects.filter(persona=persona).exists())

	def test_registered_client_can_log_in(self):
		persona = Persona.objects.create_user(
			username='client@example.com',
			email='client@example.com',
			password='S3cure!LadyMakeup2026',
			rol='cliente',
		)
		Cliente.objects.create(persona=persona)

		response = self.client.post(
			reverse('App_usuarios:login'),
			{
				'username': 'client@example.com',
				'password': 'S3cure!LadyMakeup2026',
				'rol': 'cliente',
			},
		)

		self.assertRedirects(response, reverse('App_agenda:c_inicio'))
		self.assertEqual(int(self.client.session['_auth_user_id']), persona.pk)


@override_settings(MAILERS={'default': {'BACKEND': 'django.core.mail.backends.locmem.EmailBackend'}})
class VerificacionAdicionalTests(TestCase):
    def setUp(self):
        cache.clear()
        self.registro = {
            'nombre': 'Sara', 'apellido': 'Morales',
            'email': 'sara@example.com', 'telefono': '3111111111',
            'password': 'ClaveSegura!2026Abc',
        }

    def test_no_crea_cliente_antes_de_confirmar_codigo(self):
        response = self.client.post(reverse('App_usuarios:registro'), self.registro)
        self.assertRedirects(response, reverse('App_usuarios:confirmar_registro'))
        self.assertFalse(Persona.objects.filter(email='sara@example.com').exists())
        self.assertEqual(len(mail.outbox), 1)
        codigo = re.search(r'\b(\d{6})\b', mail.outbox[0].body).group(1)
        self.assertNotEqual(self.client.session['registro_cliente_pendiente']['codigo_hash'], codigo)
        response = self.client.post(reverse('App_usuarios:confirmar_registro'), {'codigo': codigo})
        self.assertRedirects(response, reverse('App_usuarios:login'))
        self.assertTrue(Cliente.objects.filter(persona__email='sara@example.com').exists())

    def test_codigo_equivocado_no_crea_cliente(self):
        self.client.post(reverse('App_usuarios:registro'), self.registro)
        codigo_real = re.search(r'\b(\d{6})\b', mail.outbox[-1].body).group(1)
        codigo_erroneo = '000001' if codigo_real == '000000' else '000000'
        for _ in range(5):
            response = self.client.post(reverse('App_usuarios:confirmar_registro'), {'codigo': codigo_erroneo})
            self.assertEqual(response.status_code, 200)
        self.assertFalse(Persona.objects.filter(email='sara@example.com').exists())
        self.assertIn('intentos', self.client.session['registro_cliente_pendiente'])

    def test_cambiar_email_del_perfil_exige_verificacion(self):
        persona = Persona.objects.create_user(
            username='sara@example.com', email='sara@example.com',
            password='ClaveSegura!2026Abc', rol='cliente',
        )
        Cliente.objects.create(persona=persona)
        self.client.force_login(persona)
        response = self.client.post(reverse('App_usuarios:perfil'), {
            'first_name': 'Sara', 'last_name': 'Morales', 'email': 'nuevo@example.com',
            'telefono': '3111111111',
        })
        self.assertRedirects(response, reverse('App_usuarios:confirmar_cambio_correo'))
        persona.refresh_from_db()
        self.assertEqual(persona.email, 'sara@example.com')
        codigo = re.search(r'\b(\d{6})\b', mail.outbox[-1].body).group(1)
        response = self.client.post(reverse('App_usuarios:confirmar_cambio_correo'), {'codigo': codigo})
        self.assertRedirects(response, reverse('App_usuarios:perfil'))
        persona.refresh_from_db()
        self.assertEqual(persona.email, 'nuevo@example.com')
        self.assertEqual(persona.username, 'nuevo@example.com')
