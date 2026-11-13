from django.test import TestCase
from django.urls import reverse

from .models import Cliente, Estilista, Persona


class AccountWorkflowTests(TestCase):
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

		self.assertRedirects(response, reverse('App_usuarios:login'))
		self.assertContains(response, 'Registro exitoso. Ya puedes iniciar sesión.')
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

		self.assertRedirects(response, reverse('App_usuarios:login'))
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

		self.assertRedirects(response, reverse('App_usuarios:login'))
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
