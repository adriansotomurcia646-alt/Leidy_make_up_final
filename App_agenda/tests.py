from datetime import date, datetime, time, timedelta
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

from App_servicios.models import Servicio
from App_usuarios.models import Cliente, Estilista, Persona

from .models import Cita, CitaArchivo, Horario, Mensaje


def valores_reservables(slots):
	return [slot['value'] for slot in slots if slot['disponible']]


class CitaWorkflowTests(TestCase):
	def setUp(self):
		self.cliente_persona = Persona.objects.create_user(
			username='client', password='MakeupTest2026!abc', rol='cliente'
		)
		self.cliente = Cliente.objects.create(persona=self.cliente_persona)
		self.estilista_persona = Persona.objects.create_user(
			username='stylist', password='MakeupTest2026!abc', rol='estilista'
		)
		self.estilista = Estilista.objects.create(persona=self.estilista_persona)
		self.servicio = Servicio.objects.create(
			nombre='Maquillaje social',
			categoria='Maquillaje',
			precio='65000.00',
			duracion=60,
		)
		for dia_semana in range(7):
			Horario.objects.create(
				estilista=self.estilista,
				dia_semana=dia_semana,
				hora_inicio=time(6, 0),
				hora_fin=time(20, 0),
			)

	def test_root_displays_public_home_for_visitors(self):
		response = self.client.get('/')
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'App_usuarios/home.html')

	def test_root_with_an_existing_client_session_redirects_to_client_home(self):
		self.client.force_login(self.cliente_persona)
		response = self.client.get('/', follow=True)

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'App_agenda/C_inicio.html')
		self.assertEqual(
			response.redirect_chain,
			[(reverse('App_agenda:c_inicio'), 302)],
		)

	def test_visitor_can_browse_services_and_select_a_booking_before_login(self):
		response = self.client.get(reverse('App_agenda:c_reservar'), {'servicio': self.servicio.pk})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Maquillaje social')
		self.assertContains(response, 'name="fecha"')
		self.assertContains(response, 'Login')

		fecha = timezone.localdate() + timedelta(days=2)
		disponibilidad = self.client.get(
			reverse('App_agenda:disponibilidad_reserva'),
			{'servicio_id': self.servicio.pk, 'fecha': fecha.isoformat()},
		)
		self.assertEqual(disponibilidad.status_code, 200)
		self.assertIn('08:00', valores_reservables(disponibilidad.json()['slots']))

		response = self.client.post(
			reverse('App_agenda:c_reservar'),
			{
				'servicio_id': str(self.servicio.pk),
				'fecha': fecha.isoformat(),
				'hora': '10:30',
			},
		)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(
			response['Location'],
			f'{reverse("App_usuarios:login")}?next={reverse("App_agenda:c_reservar")}',
		)
		login_page = self.client.get(response['Location'])
		self.assertContains(
			login_page,
			'Inicia sesión como cliente para enviar la solicitud.',
		)
		self.assertEqual(
			self.client.session.get('booking_draft'),
			{
				'servicio_id': str(self.servicio.pk),
				'fecha': fecha.isoformat(),
				'hora': '10:30',
			},
		)
		self.assertFalse(Cita.objects.exists())

		login_response = self.client.post(
			reverse('App_usuarios:login'),
			{
				'username': self.cliente_persona.username,
				'password': 'MakeupTest2026!abc',
				'rol': 'cliente',
				'next': reverse('App_agenda:c_reservar'),
			},
		)
		self.assertEqual(login_response.status_code, 302)
		self.assertEqual(login_response['Location'], reverse('App_agenda:c_reservar'))
		resumed = self.client.get(reverse('App_agenda:c_reservar'))
		self.assertContains(resumed, 'Conservamos el servicio, la fecha y el horario')
		self.assertContains(resumed, f'value="{self.servicio.pk}"')
		self.assertContains(resumed, f'value="{fecha.isoformat()}"')
		self.assertContains(resumed, 'value="10:30"')
		completed = self.client.post(
			reverse('App_agenda:c_reservar'),
			{
				'servicio_id': str(self.servicio.pk),
				'fecha': fecha.isoformat(),
				'hora': '10:30',
				'mensaje': '',
			},
		)
		self.assertRedirects(completed, reverse('App_agenda:c_mis_citas'))
		self.assertTrue(Cita.objects.filter(cliente=self.cliente).exists())

	def test_visitor_cannot_create_a_appointment_by_posting_directly(self):
		response = self.client.post(
			reverse('App_agenda:c_reservar'),
			{
				'servicio': self.servicio.pk,
				'fecha': (timezone.localdate() + timedelta(days=2)).isoformat(),
				'hora_inicio': '10:30',
			},
		)

		self.assertEqual(response.status_code, 302)
		self.assertFalse(Cita.objects.exists())

		self.client.force_login(self.estilista_persona)
		stylist_response = self.client.post(
			reverse('App_agenda:c_reservar'),
			{
				'servicio': self.servicio.pk,
				'fecha': (timezone.localdate() + timedelta(days=2)).isoformat(),
				'hora_inicio': '10:30',
			},
		)
		self.assertEqual(stylist_response.status_code, 403)
		self.assertFalse(Cita.objects.exists())

	def test_client_and_stylist_login_modules_enforce_the_real_role(self):
		for persona, password, selected_role, message in (
			(
				self.estilista_persona,
				'MakeupTest2026!abc',
				'cliente',
				'Esta cuenta no pertenece al módulo de clientes.',
			),
			(
				self.cliente_persona,
				'MakeupTest2026!abc',
				'estilista',
				'Esta cuenta no pertenece al módulo de estilista.',
			),
		):
			with self.subTest(role=selected_role):
				self.client.logout()
				response = self.client.post(
					reverse('App_usuarios:login'),
					{
						'username': persona.username,
						'password': password,
						'rol': selected_role,
					},
				)
				self.assertEqual(response.status_code, 200)
				self.assertContains(response, message)
				self.assertNotIn('_auth_user_id', self.client.session)

	def test_public_service_catalog_reflects_database_changes(self):
		response = self.client.get(reverse('App_servicios:lista'))
		self.assertContains(response, 'Maquillaje social')

		self.servicio.nombre = 'Maquillaje actualizado'
		self.servicio.save(update_fields=['nombre'])
		response = self.client.get(reverse('App_servicios:lista'))
		self.assertContains(response, 'Maquillaje actualizado')

		self.servicio.activo = False
		self.servicio.save(update_fields=['activo'])
		response = self.client.get(reverse('App_servicios:lista'))
		self.assertNotContains(response, 'Maquillaje actualizado')

	def test_client_login_redirects_to_client_home(self):
		response = self.client.post(
			reverse('App_usuarios:login'),
			{
				'username': self.cliente_persona.username,
				'password': 'MakeupTest2026!abc',
				'rol': 'cliente',
			},
		)
		self.assertRedirects(response, reverse('App_agenda:c_inicio'))

	def test_stylist_login_redirects_to_stylist_home(self):
		response = self.client.post(
			reverse('App_usuarios:login'),
			{
				'username': self.estilista_persona.username,
				'password': 'MakeupTest2026!abc',
				'rol': 'estilista',
			},
		)

		self.assertRedirects(response, reverse('App_agenda:e_inicio'))

	def test_client_can_navigate_to_other_authorized_pages(self):
		self.client.force_login(self.cliente_persona)
		for route_name, template in (
			('App_agenda:c_mis_citas', 'App_agenda/C_mis_citas.html'),
			('App_agenda:c_reservar', 'App_agenda/C_reservar_cita.html'),
			('App_agenda:c_mensajes', 'App_agenda/C_mensajes.html'),
			('App_usuarios:perfil', 'App_usuarios/C_perfil.html'),
			('App_servicios:lista', 'App_servicios/C_servicios.html'),
		):
			with self.subTest(route=route_name):
				response = self.client.get(reverse(route_name))
				self.assertEqual(response.status_code, 200)
				self.assertTemplateUsed(response, template)

	def test_unauthenticated_user_is_redirected_to_login_and_then_to_requested_page(self):
		protected_url = reverse('App_agenda:c_mis_citas')
		response = self.client.get(protected_url)
		self.assertRedirects(
			response,
			f'{reverse("App_usuarios:login")}?next={protected_url}',
		)

		login_page = self.client.get(response['Location'])
		self.assertContains(login_page, f'name="next" value="{protected_url}"')
		response = self.client.post(
			reverse('App_usuarios:login'),
			{
				'username': self.cliente_persona.username,
				'password': 'MakeupTest2026!abc',
				'rol': 'cliente',
				'next': protected_url,
			},
		)
		self.assertRedirects(response, protected_url)

	def test_authenticated_user_without_required_role_gets_forbidden_without_redirect_loop(self):
		self.client.force_login(self.cliente_persona)
		response = self.client.get(reverse('App_agenda:e_inicio'), follow=True)

		self.assertEqual(response.status_code, 403)
		self.assertEqual(response.redirect_chain, [])

	def test_unknown_route_returns_404_without_redirecting(self):
		response = self.client.get('/not-a-real-route/', follow=True)

		self.assertEqual(response.status_code, 404)
		self.assertEqual(response.redirect_chain, [])

	def test_stylist_sees_stylist_service_management_page(self):
		self.client.force_login(self.estilista_persona)

		response = self.client.get(reverse('App_servicios:lista'))

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'App_servicios/E_servicios.html')

	def test_staff_flag_does_not_grant_stylist_role(self):
		administrador = Persona.objects.create_user(
			username='admin',
			password='MakeupTest2026!abc',
			is_staff=True,
		)
		response = self.client.post(
			reverse('App_usuarios:login'),
			{
				'username': administrador.username,
				'password': 'MakeupTest2026!abc',
				'rol': 'cliente',
			},
		)
		self.assertRedirects(response, reverse('App_agenda:c_inicio'))
		self.assertEqual(self.client.get(reverse('App_agenda:e_inicio')).status_code, 403)

	def test_logout_clears_session_and_redirects_to_login(self):
		self.client.force_login(self.cliente_persona)
		session = self.client.session
		session['rol'] = 'cliente'
		session['custom_value'] = 'temporary'
		session.save()

		response = self.client.post(reverse('App_usuarios:logout'))

		self.assertRedirects(response, reverse('App_usuarios:login'))
		self.assertNotIn('_auth_user_id', self.client.session)
		self.assertNotIn('custom_value', self.client.session)

	def test_booking_shows_services_from_the_database(self):
		self.client.force_login(self.cliente_persona)
		response = self.client.get(reverse('App_agenda:c_reservar'))

		self.assertEqual(response.status_code, 200)
		self.assertIn(self.servicio, response.context['servicios'])
		self.assertEqual(
			str(response.context['servicios'].get(pk=self.servicio.pk).precio),
			self.servicio.precio,
		)
		self.assertContains(response, 'Maquillaje social')
		self.assertContains(response, 'Maquillaje')
		self.assertContains(response, '60 min')
		self.assertNotContains(response, 'Peinado para eventos')

	def test_booking_shows_empty_state_when_there_are_no_active_services(self):
		self.servicio.activo = False
		self.servicio.save(update_fields=['activo'])
		self.client.force_login(self.cliente_persona)

		response = self.client.get(reverse('App_agenda:c_reservar'))

		self.assertContains(
			response,
			'No hay servicios disponibles para reservar en este momento.',
		)
		self.assertNotContains(response, 'Keratina')

	def test_booking_accepts_the_existing_template_payload(self):
		self.client.force_login(self.cliente_persona)
		fecha = timezone.localdate() + timedelta(days=2)
		response = self.client.post(
			reverse('App_agenda:c_reservar'),
			{
				'servicio_id': str(self.servicio.pk),
				'fecha': fecha.isoformat(),
				'hora': '10:30 AM',
				'mensaje': 'Referencia de prueba',
			},
		)
		self.assertRedirects(response, reverse('App_agenda:c_mis_citas'))
		cita = Cita.objects.get(cliente=self.cliente)
		self.assertEqual(cita.estilista, self.estilista)
		self.assertEqual(cita.hora_inicio.strftime('%H:%M'), '10:30')
		self.assertEqual(cita.hora_fin.strftime('%H:%M'), '11:30')
		self.assertEqual(cita.mensaje, 'Referencia de prueba')
		self.assertEqual(cita.estado, 'PENDIENTE')

	def test_booking_success_message_includes_the_appointment_date_and_time(self):
		self.client.force_login(self.cliente_persona)
		fecha = timezone.localdate() + timedelta(days=2)

		response = self.client.post(
			reverse('App_agenda:c_reservar'),
			{
				'servicio_id': str(self.servicio.pk),
				'fecha': fecha.isoformat(),
				'hora': '10:30',
				'mensaje': '',
			},
			follow=True,
		)

		self.assertContains(
			response,
			f'Tu solicitud para {self.servicio.nombre} el {fecha:%d/%m/%Y} '
			'a las 10:30 se envió correctamente y está pendiente de confirmación.',
		)
		self.assertContains(response, 'Éxito:')
		self.assertContains(response, 'border-emerald-200')

	def test_cancellation_success_message_includes_the_appointment_date_and_time(self):
		fecha = timezone.localdate() + timedelta(days=2)
		cita = Cita.objects.create(
			cliente=self.cliente,
			estilista=self.estilista,
			servicio=self.servicio,
			fecha=fecha,
			hora_inicio=time(9, 0),
		)
		self.client.force_login(self.cliente_persona)

		response = self.client.post(
			reverse('App_agenda:cancelar_cita', args=[cita.pk]),
			follow=True,
		)

		self.assertContains(
			response,
			f'La cita de {self.servicio.nombre} del {fecha:%d/%m/%Y} '
			'a las 09:00 fue cancelada.',
		)
		self.assertContains(response, 'Éxito:')
		cita.refresh_from_db()
		self.assertEqual(cita.estado, 'CANCELADA')

	def test_booking_rejects_overlapping_times(self):
		fecha = timezone.localdate() + timedelta(days=2)
		Cita.objects.create(
			cliente=self.cliente,
			estilista=self.estilista,
			servicio=self.servicio,
			fecha=fecha,
			hora_inicio=time(11, 0),
		)
		self.client.force_login(self.cliente_persona)
		response = self.client.post(
			reverse('App_agenda:c_reservar'),
			{
				'servicio_id': str(self.servicio.pk),
				'fecha': fecha.isoformat(),
				'hora': '11:30 AM',
				'mensaje': '',
			},
		)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(Cita.objects.count(), 1)
		self.assertFormError(
			response.context['form'],
			'hora_inicio',
			'Debe haber 60 minutos entre esta cita y otra cita activa.',
		)

	def test_booking_rejects_duplicate_submission_with_a_visible_error(self):
		self.client.force_login(self.cliente_persona)
		fecha = timezone.localdate() + timedelta(days=2)
		payload = {
			'servicio_id': str(self.servicio.pk),
			'fecha': fecha.isoformat(),
			'hora': '10:30',
			'mensaje': 'Prueba de doble envío',
		}
		first_response = self.client.post(reverse('App_agenda:c_reservar'), payload)
		self.assertRedirects(first_response, reverse('App_agenda:c_mis_citas'))

		second_response = self.client.post(reverse('App_agenda:c_reservar'), payload)

		self.assertEqual(second_response.status_code, 200)
		self.assertEqual(Cita.objects.filter(cliente=self.cliente).count(), 1)
		self.assertContains(second_response, 'Debe haber 60 minutos entre esta cita y otra cita activa.')

	def test_booking_availability_uses_configured_working_hours(self):
		fecha = timezone.localdate() + timedelta(days=2)
		Horario.objects.filter(
			estilista=self.estilista,
			dia_semana=fecha.weekday(),
		).delete()
		Horario.objects.create(
			estilista=self.estilista,
			dia_semana=fecha.weekday(),
			hora_inicio=time(9, 0),
			hora_fin=time(11, 0),
		)
		self.client.force_login(self.cliente_persona)

		disponibilidad = self.client.get(
			reverse('App_agenda:disponibilidad_reserva'),
			{'servicio_id': self.servicio.pk, 'fecha': fecha.isoformat()},
		)
		self.assertEqual(
			valores_reservables(disponibilidad.json()['slots']),
			['09:00', '09:30', '10:00'],
		)
		response = self.client.post(
			reverse('App_agenda:c_reservar'),
			{
				'servicio_id': str(self.servicio.pk),
				'fecha': fecha.isoformat(),
				'hora': '08:30',
				'mensaje': '',
			},
		)
		self.assertEqual(response.status_code, 200)
		self.assertFalse(Cita.objects.exists())
		self.assertFormError(
			response.context['form'],
			'hora_inicio',
			'La franja queda fuera del horario configurado de la estilista.',
		)

	def test_availability_generates_unique_half_hour_slots_within_the_workday(self):
		fecha = timezone.localdate() + timedelta(days=2)

		response = self.client.get(
			reverse('App_agenda:disponibilidad_reserva'),
			{'servicio_id': self.servicio.pk, 'fecha': fecha.isoformat()},
		)

		slots = response.json()['slots']
		valores = [slot['value'] for slot in slots]
		self.assertEqual(valores[:3], ['06:00', '06:30', '07:00'])
		self.assertEqual(len(valores), 29)
		self.assertEqual(len(valores), len(set(valores)))
		self.assertIn('19:00', valores_reservables(slots))
		self.assertNotIn('19:30', valores_reservables(slots))
		self.assertIn('17:00', valores_reservables(slots))
		self.assertIn('17:30', valores_reservables(slots))

	def test_availability_requires_a_configured_work_schedule(self):
		Horario.objects.filter(estilista=self.estilista).delete()
		fecha = timezone.localdate() + timedelta(days=2)

		response = self.client.get(
			reverse('App_agenda:disponibilidad_reserva'),
			{'servicio_id': self.servicio.pk, 'fecha': fecha.isoformat()},
		)

		slots = response.json()['slots']
		self.assertEqual(len(slots), 29)
		self.assertTrue(all(not slot['disponible'] for slot in slots))

	def test_backend_rejects_a_start_time_outside_the_half_hour_grid(self):
		self.client.force_login(self.cliente_persona)
		fecha = timezone.localdate() + timedelta(days=2)

		response = self.client.post(
			reverse('App_agenda:c_reservar'),
			{
				'servicio_id': str(self.servicio.pk),
				'fecha': fecha.isoformat(),
				'hora': '10:15',
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertFalse(Cita.objects.exists())
		self.assertFormError(
			response.context['form'],
			'hora_inicio',
			'Los inicios deben coincidir con intervalos de 30 minutos.',
		)

	def test_availability_requires_strictly_more_than_one_hour_notice(self):
		fecha = timezone.localdate()
		now = datetime.combine(
			fecha,
			time(13, 0),
			tzinfo=ZoneInfo('America/Bogota'),
		)
		with patch('django.utils.timezone.now', return_value=now):
			response = self.client.get(
				reverse('App_agenda:disponibilidad_reserva'),
				{'servicio_id': self.servicio.pk, 'fecha': fecha.isoformat()},
			)
			slots = valores_reservables(response.json()['slots'])
			self.assertNotIn('14:00', slots)
			self.assertIn('14:30', slots)

			self.client.force_login(self.cliente_persona)
			too_soon = self.client.post(
				reverse('App_agenda:c_reservar'),
				{
					'servicio_id': str(self.servicio.pk),
					'fecha': fecha.isoformat(),
					'hora': '14:00',
				},
			)
			self.assertEqual(too_soon.status_code, 200)
			self.assertFormError(
				too_soon.context['form'],
				'hora_inicio',
				'La cita debe solicitarse con más de una hora de anticipación.',
			)
			self.assertFalse(Cita.objects.exists())

	def test_long_services_block_overlapping_intervals_but_cancellation_releases_them(self):
		fecha = timezone.localdate() + timedelta(days=2)
		servicio_largo = Servicio.objects.create(
			nombre='Servicio de noventa minutos',
			precio='90000.00',
			duracion=90,
		)
		cita = Cita.objects.create(
			cliente=self.cliente,
			estilista=self.estilista,
			servicio=servicio_largo,
			fecha=fecha,
			hora_inicio=time(10, 30),
		)
		self.assertEqual(cita.hora_fin, time(12, 0))
		self.client.force_login(self.cliente_persona)

		ocupados = self.client.get(
			reverse('App_agenda:disponibilidad_reserva'),
			{'servicio_id': self.servicio.pk, 'fecha': fecha.isoformat()},
		)
		horas_ocupadas = valores_reservables(ocupados.json()['slots'])
		franjas_por_hora = {
			slot['value']: slot for slot in ocupados.json()['slots']
		}
		self.assertNotIn('10:00', horas_ocupadas)
		self.assertNotIn('10:30', horas_ocupadas)
		self.assertNotIn('11:00', horas_ocupadas)
		self.assertNotIn('11:30', horas_ocupadas)
		self.assertNotIn('12:00', horas_ocupadas)
		self.assertEqual(franjas_por_hora['12:00']['estado'], 'occupied')
		self.assertIn('60 minutos', franjas_por_hora['12:00']['motivo'])
		self.assertIn('13:00', horas_ocupadas)

		cita.estado = 'CANCELADA'
		cita.save(update_fields=['estado'])
		liberados = self.client.get(
			reverse('App_agenda:disponibilidad_reserva'),
			{'servicio_id': self.servicio.pk, 'fecha': fecha.isoformat()},
		)
		self.assertIn('10:30', valores_reservables(liberados.json()['slots']))

	def test_thirty_minute_service_observes_the_full_separation_period(self):
		fecha = timezone.localdate() + timedelta(days=2)
		servicio_corto = Servicio.objects.create(
			nombre='Servicio de treinta minutos',
			precio='30000.00',
			duracion=30,
		)
		Cita.objects.create(
			cliente=self.cliente,
			estilista=self.estilista,
			servicio=servicio_corto,
			fecha=fecha,
			hora_inicio=time(10, 30),
		)
		self.client.force_login(self.cliente_persona)

		response = self.client.get(
			reverse('App_agenda:disponibilidad_reserva'),
			{'servicio_id': servicio_corto.pk, 'fecha': fecha.isoformat()},
		)

		slots = valores_reservables(response.json()['slots'])
		self.assertNotIn('10:00', slots)
		self.assertNotIn('10:30', slots)
		self.assertNotIn('11:00', slots)
		self.assertIn('12:00', slots)

	def test_pending_confirmed_and_in_progress_appointments_remain_occupied(self):
		fecha = timezone.localdate() + timedelta(days=2)
		for estado in ('PENDIENTE', 'CONFIRMADA', 'EN_PROCESO'):
			with self.subTest(estado=estado):
				cita = Cita.objects.create(
					cliente=self.cliente,
					estilista=self.estilista,
					servicio=self.servicio,
					fecha=fecha,
					hora_inicio=time(10, 0),
					estado=estado,
				)
				response = self.client.get(
					reverse('App_agenda:disponibilidad_reserva'),
					{'servicio_id': self.servicio.pk, 'fecha': fecha.isoformat()},
				)
				franjas = {slot['value']: slot for slot in response.json()['slots']}
				self.assertEqual(franjas['11:30']['estado'], 'occupied')
				self.assertTrue(franjas['12:00']['disponible'])
				cita.estado = 'CANCELADA'
				cita.save(update_fields=['estado'])
				liberadas = self.client.get(
					reverse('App_agenda:disponibilidad_reserva'),
					{'servicio_id': self.servicio.pk, 'fecha': fecha.isoformat()},
				)
				self.assertTrue(
					next(slot for slot in liberadas.json()['slots'] if slot['value'] == '10:00')['disponible']
				)

	def test_previous_day_appointment_crossing_midnight_blocks_until_one_hour_after_end(self):
		fecha = timezone.localdate() + timedelta(days=2)
		servicio_nocturno = Servicio.objects.create(
			nombre='Servicio heredado nocturno',
			precio='120000.00',
			duracion=480,
		)
		cita = Cita.objects.create(
			cliente=self.cliente,
			estilista=self.estilista,
			servicio=servicio_nocturno,
			fecha=fecha - timedelta(days=1),
			hora_inicio=time(23, 0),
		)
		self.assertEqual(cita.hora_fin, time(7, 0))

		response = self.client.get(
			reverse('App_agenda:disponibilidad_reserva'),
			{'servicio_id': self.servicio.pk, 'fecha': fecha.isoformat()},
		)
		franjas = {slot['value']: slot for slot in response.json()['slots']}
		self.assertEqual(franjas['06:00']['estado'], 'occupied')
		self.assertEqual(franjas['07:00']['estado'], 'occupied')
		self.assertTrue(franjas['08:00']['disponible'])

	def test_full_day_grid_is_visible_and_the_closing_time_is_not_reservable(self):
		fecha = timezone.localdate() + timedelta(days=2)
		response = self.client.get(
			reverse('App_agenda:disponibilidad_reserva'),
			{'servicio_id': self.servicio.pk, 'fecha': fecha.isoformat()},
		)

		slots = response.json()['slots']
		self.assertEqual(
			[slot['value'] for slot in slots],
			[
				f'{minutes // 60:02d}:{minutes % 60:02d}'
				for minutes in range(6 * 60, 20 * 60 + 1, 30)
			],
		)
		self.assertEqual(len(slots), 29)
		self.assertEqual(slots[-1]['value'], '20:00')
		self.assertFalse(slots[-1]['disponible'])
		self.assertIn('8:00 p. m.', slots[-1]['motivo'])

	def test_database_schedule_covers_all_weekdays_from_six_to_eight(self):
		horarios = Horario.objects.filter(estilista=self.estilista, activo=True)
		self.assertEqual(set(horarios.values_list('dia_semana', flat=True)), set(range(7)))
		self.assertEqual(set(horarios.values_list('hora_inicio', flat=True)), {time(6, 0)})
		self.assertEqual(set(horarios.values_list('hora_fin', flat=True)), {time(20, 0)})

	def test_services_can_finish_at_close_but_not_after_it(self):
		fecha = timezone.localdate() + timedelta(days=2)
		keratina = Servicio.objects.create(
			nombre='Keratina', precio='200000.00', duracion=480,
		)
		for servicio, permitida, prohibida in (
			(self.servicio, '19:00', '19:30'),
			(keratina, '12:00', '12:30'),
		):
			with self.subTest(duracion=servicio.duracion):
				franjas = {
					slot['value']: slot
					for slot in self.client.get(
						reverse('App_agenda:disponibilidad_reserva'),
						{'servicio_id': servicio.pk, 'fecha': fecha.isoformat()},
					).json()['slots']
				}
				self.assertTrue(franjas[permitida]['disponible'])
				self.assertFalse(franjas[prohibida]['disponible'])
				self.assertIn('terminar', franjas[prohibida]['motivo'])
				self.assertFalse(franjas['20:00']['disponible'])

	def test_sixty_minute_separation_blocks_before_and_after_services_of_each_duration(self):
		fecha = timezone.localdate() + timedelta(days=2)
		servicio_siguiente = self.servicio
		for duracion in (30, 60, 120, 480):
			with self.subTest(duracion=duracion):
				servicio_existente = Servicio.objects.create(
					nombre=f'Servicio existente {duracion}',
					precio='50000.00',
					duracion=duracion,
				)
				Cita.objects.create(
					cliente=self.cliente,
					estilista=self.estilista,
					servicio=servicio_existente,
					fecha=fecha,
					hora_inicio=time(8, 0),
				)
				response = self.client.get(
					reverse('App_agenda:disponibilidad_reserva'),
					{'servicio_id': servicio_siguiente.pk, 'fecha': fecha.isoformat()},
				)
				franjas = {
					slot['value']: slot for slot in response.json()['slots']
				}
				fin = datetime.combine(fecha, time(8, 0)) + timedelta(minutes=duracion)
				antes_de_separacion = (fin + timedelta(minutes=30)).strftime('%H:%M')
				fin_separacion = (fin + timedelta(hours=1)).strftime('%H:%M')
				self.assertFalse(franjas['07:00']['disponible'])
				self.assertTrue(franjas['06:00']['disponible'])
				self.assertFalse(franjas[antes_de_separacion]['disponible'])
				self.assertTrue(franjas[fin_separacion]['disponible'])
				Cita.objects.filter(servicio=servicio_existente).delete()

	def test_rescheduling_rejects_a_gap_shorter_than_sixty_minutes(self):
		fecha = timezone.localdate() + timedelta(days=2)
		cita = Cita.objects.create(
			cliente=self.cliente,
			estilista=self.estilista,
			servicio=self.servicio,
			fecha=fecha,
			hora_inicio=time(10, 0),
		)
		Cita.objects.create(
			cliente=self.cliente,
			estilista=self.estilista,
			servicio=self.servicio,
			fecha=fecha,
			hora_inicio=time(14, 0),
		)
		self.client.force_login(self.cliente_persona)

		response = self.client.post(
			reverse('App_agenda:reprogramar_cita', args=[cita.pk]),
			{'fecha': fecha.isoformat(), 'hora_inicio': '13:30'},
		)
		self.assertEqual(response.status_code, 302)
		cita.refresh_from_db()
		self.assertEqual(cita.hora_inicio, time(10, 0))

	def test_service_duration_is_snapshotted_when_a_booking_is_created(self):
		fecha = timezone.localdate() + timedelta(days=2)
		cita = Cita.objects.create(
			cliente=self.cliente,
			estilista=self.estilista,
			servicio=self.servicio,
			fecha=fecha,
			hora_inicio=time(10, 0),
		)
		self.assertEqual(cita.duracion_aprobada, 60)
		self.assertEqual(cita.hora_fin, time(11, 0))

		self.servicio.duracion = 120
		self.servicio.save(update_fields=['duracion'])
		cita.estado = 'CONFIRMADA'
		cita.save(update_fields=['estado'])
		cita.refresh_from_db()
		self.assertEqual(cita.duracion_aprobada, 60)
		self.assertEqual(cita.hora_fin, time(11, 0))

	def test_stylist_can_manage_schedules_but_clients_cannot(self):
		self.client.force_login(self.cliente_persona)
		self.assertEqual(
			self.client.get(reverse('App_usuarios:configuracion')).status_code,
			403,
		)

		self.client.force_login(self.estilista_persona)
		Horario.objects.filter(estilista=self.estilista, dia_semana=0).delete()
		response = self.client.post(
			reverse('App_usuarios:configuracion'),
			{
				'accion': 'guardar_horario',
				'dia_semana': '0',
				'hora_inicio': '07:00',
				'hora_fin': '08:00',
				'activo': 'on',
			},
			follow=True,
		)
		self.assertContains(response, 'El horario laboral fue guardado correctamente.')
		horario = Horario.objects.get(
			estilista=self.estilista,
			dia_semana=0,
			hora_inicio=time(7, 0),
		)

		self.client.post(
			reverse('App_usuarios:configuracion'),
			{
				'accion': 'guardar_horario',
				'horario_id': horario.pk,
				'dia_semana': '0',
				'hora_inicio': '07:00',
				'hora_fin': '08:00',
			},
		)
		horario.refresh_from_db()
		self.assertFalse(horario.activo)

	def test_client_history_and_cancellation_are_scoped_to_the_authenticated_client(self):
		fecha = timezone.localdate() + timedelta(days=2)
		propia = Cita.objects.create(
			cliente=self.cliente,
			estilista=self.estilista,
			servicio=self.servicio,
			fecha=fecha,
			hora_inicio=time(9, 0),
		)
		otra_persona = Persona.objects.create_user(
			username='separate-client',
			password='MakeupTest2026!abc',
			rol='cliente',
		)
		otro_cliente = Cliente.objects.create(persona=otra_persona)
		ajena = Cita.objects.create(
			cliente=otro_cliente,
			estilista=self.estilista,
			servicio=self.servicio,
			fecha=fecha,
			hora_inicio=time(11, 0),
		)
		self.client.force_login(self.cliente_persona)

		response = self.client.get(reverse('App_agenda:c_mis_citas'))
		self.assertEqual(list(response.context['citas']), [propia])
		self.assertEqual(
			self.client.post(
				reverse('App_agenda:cancelar_cita', args=[ajena.pk])
			).status_code,
			404,
		)
		ajena.refresh_from_db()
		self.assertEqual(ajena.estado, 'PENDIENTE')

	def test_invalid_attachment_is_reported_without_saving_a_appointment(self):
		self.client.force_login(self.cliente_persona)

		response = self.client.post(
			reverse('App_agenda:c_reservar'),
			{
				'servicio_id': str(self.servicio.pk),
				'fecha': (timezone.localdate() + timedelta(days=2)).isoformat(),
				'hora': '10:30',
				'adjuntos': SimpleUploadedFile(
					'malware.exe',
					b'not-allowed',
					content_type='application/octet-stream',
				),
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertFalse(Cita.objects.exists())
		self.assertContains(response, 'Tipo de archivo no permitido.')

	def test_booking_rejects_a_past_date_without_saving(self):
		self.client.force_login(self.cliente_persona)

		response = self.client.post(
			reverse('App_agenda:c_reservar'),
			{
				'servicio_id': str(self.servicio.pk),
				'fecha': (timezone.localdate() - timedelta(days=1)).isoformat(),
				'hora': '10:30',
				'mensaje': 'La fecha ya pasó',
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertFalse(Cita.objects.exists())
		self.assertFormError(
			response.context['form'],
			'fecha',
			'La fecha de la cita no puede estar en el pasado.',
		)

	def test_attachments_are_saved_and_downloads_are_owner_or_stylist_only(self):
		with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
			self.client.force_login(self.cliente_persona)
			response = self.client.post(
				reverse('App_agenda:c_reservar'),
				{
					'servicio_id': str(self.servicio.pk),
					'fecha': (timezone.localdate() + timedelta(days=2)).isoformat(),
					'hora': '10:30',
					'mensaje': 'Adjunto de referencia',
					'adjuntos': SimpleUploadedFile(
						'referencia.jpg',
						b'\xff\xd8\xffjpeg-content',
						content_type='image/jpeg',
					),
				},
			)
			self.assertRedirects(response, reverse('App_agenda:c_mis_citas'))
			adjunto = CitaArchivo.objects.get()
			self.assertEqual(adjunto.cita.cliente, self.cliente)

			download_url = reverse('App_agenda:descargar_adjunto', args=[adjunto.pk])
			descarga_cliente = self.client.get(download_url)
			self.assertEqual(descarga_cliente.status_code, 200)
			self.assertEqual(
				b''.join(descarga_cliente.streaming_content),
				b'\xff\xd8\xffjpeg-content',
			)

			otra_persona = Persona.objects.create_user(
				username='private-file-client',
				password='MakeupTest2026!abc',
				rol='cliente',
			)
			Cliente.objects.create(persona=otra_persona)
			self.client.force_login(otra_persona)
			self.assertEqual(self.client.get(download_url).status_code, 404)

			self.client.force_login(self.estilista_persona)
			self.assertEqual(self.client.get(download_url).status_code, 200)

	def test_stylist_dashboard_and_client_breakdown_are_scoped(self):
		fecha_hoy = timezone.localdate()
		Cita.objects.create(
			cliente=self.cliente,
			estilista=self.estilista,
			servicio=self.servicio,
			fecha=fecha_hoy,
			hora_inicio=time(9, 0),
			estado='PENDIENTE',
		)
		Cita.objects.create(
			cliente=self.cliente,
			estilista=self.estilista,
			servicio=self.servicio,
			fecha=fecha_hoy,
			hora_inicio=time(11, 0),
			estado='CONFIRMADA',
		)
		self.client.force_login(self.estilista_persona)

		dashboard = self.client.get(reverse('App_agenda:e_inicio'))
		self.assertEqual(dashboard.context['total_pendientes'], 1)
		self.assertEqual(dashboard.context['total_confirmadas'], 1)
		self.assertEqual(dashboard.context['citas_hoy_count'], 1)
		self.assertEqual(dashboard.context['citas_hoy'].count(), 1)
		self.assertEqual(dashboard.context['horarios_ocupados'], '1 h 0 min')
		self.assertContains(dashboard, '$65000,00')

		clientes = self.client.get(reverse('App_agenda:e_clientes'))
		cliente_contexto = clientes.context['clientes'].get(pk=self.cliente.pk)
		self.assertEqual(cliente_contexto.total_citas, 2)
		self.assertEqual(cliente_contexto.citas_pendientes, 1)
		self.assertEqual(cliente_contexto.citas_confirmadas, 1)

	def test_dashboard_sums_confirmed_service_duration_and_all_time_confirmations(self):
		fecha_hoy = timezone.localdate()
		servicio_largo = Servicio.objects.create(
			nombre='Maquillaje de evento',
			precio='90000.00',
			duracion=90,
		)
		for servicio, fecha, estado, hora in (
			(self.servicio, fecha_hoy, 'CONFIRMADA', time(9, 0)),
			(servicio_largo, fecha_hoy, 'CONFIRMADA', time(11, 0)),
			(self.servicio, fecha_hoy, 'PENDIENTE', time(14, 0)),
			(self.servicio, fecha_hoy - timedelta(days=1), 'CONFIRMADA', time(9, 0)),
		):
			Cita.objects.create(
				cliente=self.cliente,
				estilista=self.estilista,
				servicio=servicio,
				fecha=fecha,
				hora_inicio=hora,
				estado=estado,
			)
		self.client.force_login(self.estilista_persona)

		response = self.client.get(reverse('App_agenda:e_inicio'))

		self.assertEqual(response.context['total_pendientes'], 1)
		self.assertEqual(response.context['citas_hoy_count'], 2)
		self.assertEqual(response.context['total_confirmadas'], 3)
		self.assertEqual(response.context['horarios_ocupados'], '2 h 30 min')
		self.assertEqual(
			[cita.servicio.nombre for cita in response.context['citas_hoy']],
			['Maquillaje social', 'Maquillaje de evento'],
		)

	def test_requests_and_calendar_are_scoped_to_the_logged_in_stylist(self):
		fecha = timezone.localdate() + timedelta(days=2)
		propia = Cita.objects.create(
			cliente=self.cliente,
			estilista=self.estilista,
			servicio=self.servicio,
			fecha=fecha,
			hora_inicio=time(10, 0),
			estado='PENDIENTE',
		)

		otra_persona = Persona.objects.create_user(
			username='other-stylist', password='MakeupTest2026!abc', rol='estilista'
		)

		otra_estilista = Estilista.objects.create(persona=otra_persona)
		Cita.objects.create(
			cliente=self.cliente,
			estilista=otra_estilista,
			servicio=self.servicio,
			fecha=fecha,
			hora_inicio=time(12, 0),
			estado='PENDIENTE',
		)
		self.client.force_login(self.estilista_persona)

		solicitudes = self.client.get(
			reverse('App_agenda:e_solicitudes'),
			{'estado': 'PENDIENTE'},
		)
		self.assertEqual(list(solicitudes.context['citas']), [propia])

		calendario = self.client.get(
			reverse('App_agenda:e_calendario'),
			{'fecha': fecha.isoformat()},
		)
		self.assertEqual(calendario.status_code, 200)
		self.assertEqual(
			[item['id'] for item in calendario.context['citas_dia']],
			[propia.pk],
		)

	def test_calendar_api_navigates_month_week_day_and_includes_leap_day(self):
		for fecha, hora in (
			(date(2024, 2, 29), time(10, 0)),
			(date(2024, 3, 1), time(11, 0)),
		):
			Cita.objects.create(
				cliente=self.cliente,
				estilista=self.estilista,
				servicio=self.servicio,
				fecha=fecha,
				hora_inicio=hora,
				estado='CONFIRMADA',
			)
		self.client.force_login(self.estilista_persona)
		url = reverse('App_agenda:e_calendario')

		mes = self.client.get(
			url,
			{'formato': 'json', 'fecha': '2024-02-29', 'vista': 'mes'},
		).json()
		self.assertEqual(mes['inicio_periodo'], '2024-02-01')
		self.assertEqual(mes['fin_periodo'], '2024-02-29')
		self.assertEqual([cita['fecha'] for cita in mes['citas']], ['2024-02-29'])
		self.assertEqual(mes['citas_dia'][0]['categoria'], 'Maquillaje')
		self.assertEqual(mes['citas_dia'][0]['precio'], '65000.00')
		self.assertEqual(mes['citas_dia'][0]['fin'], '11:00')
		self.assertEqual(mes['resumen']['CONFIRMADA'], 1)

		semana = self.client.get(
			url,
			{'formato': 'json', 'fecha': '2024-02-29', 'vista': 'semana'},
		).json()
		self.assertEqual(semana['inicio_periodo'], '2024-02-26')
		self.assertEqual(semana['fin_periodo'], '2024-03-03')
		self.assertEqual(len(semana['citas']), 2)

		dia = self.client.get(
			url,
			{'formato': 'json', 'fecha': '2024-02-29', 'vista': 'dia'},
		).json()
		self.assertEqual(dia['inicio_periodo'], '2024-02-29')
		self.assertEqual(dia['fin_periodo'], '2024-02-29')

	def test_calendar_search_status_and_date_filters_use_real_appointments(self):
		servicio2 = Servicio.objects.create(
			nombre='Peinado de fiesta',
			categoria='Cabello',
			precio='50000.00',
			duracion=45,
		)
		cita = Cita.objects.create(
			cliente=self.cliente,
			estilista=self.estilista,
			servicio=servicio2,
			fecha=date(2026, 10, 12),
			hora_inicio=time(10, 0),
			estado='PENDIENTE',
		)
		self.cliente_persona.first_name = 'María'
		self.cliente_persona.last_name = 'Rodríguez'
		self.cliente_persona.save(update_fields=['first_name', 'last_name'])
		self.client.force_login(self.estilista_persona)
		url = reverse('App_agenda:e_calendario')
		self.assertEqual(
			Cita.objects.filter(
				estilista=self.estilista,
				cliente__persona__last_name__icontains='rodr',
			).count(),
			1,
		)
		parameters = {
			'formato': 'json',
			'fecha': '2026-10-12',
			'vista': 'mes',
			'desde': '2026-10-01',
			'hasta': '2026-10-31',
			'estado': 'PENDIENTE',
		}

		por_nombre = self.client.get(url, {**parameters, 'q': 'rodr'}).json()
		self.assertEqual(
			[item['id'] for item in por_nombre['citas']],
			[cita.pk],
			por_nombre,
		)
		por_servicio = self.client.get(url, {**parameters, 'q': 'fiesta'}).json()
		self.assertEqual([item['id'] for item in por_servicio['citas']], [cita.pk])
		self.assertEqual(por_servicio['resumen']['PENDIENTE'], 1)
		por_horario = self.client.get(
			url,
			{**parameters, 'hora_desde': '09:30', 'hora_hasta': '10:30'},
		).json()
		self.assertEqual([item['id'] for item in por_horario['citas']], [cita.pk])
		hora_invalida = self.client.get(
			url,
			{**parameters, 'hora_desde': '11:00', 'hora_hasta': '09:00'},
		).json()
		self.assertIn('horario no es válido', hora_invalida['error'])
		self.assertEqual(hora_invalida['citas'], [])
		sin_resultados = self.client.get(
			url,
			{**parameters, 'q': 'inexistente'},
		).json()
		self.assertEqual(sin_resultados['citas'], [])
		invalido = self.client.get(
			url,
			{**parameters, 'desde': '2026-11-01', 'hasta': '2026-10-01'},
		).json()
		self.assertIn('posterior', invalido['error'])
		self.assertEqual(invalido['citas'], [])
		fecha_invalida = self.client.get(
			url,
			{'formato': 'json', 'fecha': 'no-es-fecha', 'vista': 'mes'},
		).json()
		self.assertIn('no es válida', fecha_invalida['error'])

	def test_client_calendar_only_exposes_the_logged_in_clients_appointments(self):
		propia = Cita.objects.create(
			cliente=self.cliente,
			estilista=self.estilista,
			servicio=self.servicio,
			fecha=date(2026, 10, 15),
			hora_inicio=time(10, 0),
			estado='FINALIZADA',
		)
		otra_persona = Persona.objects.create_user(
			username='calendar-other',
			password='MakeupTest2026!abc',
			first_name='Otra',
			last_name='Clienta',
			rol='cliente',
		)
		otro_cliente = Cliente.objects.create(persona=otra_persona)
		Cita.objects.create(
			cliente=otro_cliente,
			estilista=self.estilista,
			servicio=self.servicio,
			fecha=date(2026, 10, 15),
			hora_inicio=time(12, 0),
			estado='CONFIRMADA',
		)
		self.client.force_login(self.cliente_persona)

		response = self.client.get(
			reverse('App_agenda:c_calendario'),
			{'formato': 'json', 'fecha': '2026-10-15', 'vista': 'dia'},
		)

		self.assertEqual([item['id'] for item in response.json()['citas']], [propia.pk])
		self.assertNotContains(
			self.client.get(reverse('App_agenda:c_calendario')),
			'Otra Clienta',
		)

	def test_only_stylist_can_complete_confirmed_appointments(self):
		cita = Cita.objects.create(
			cliente=self.cliente,
			estilista=self.estilista,
			servicio=self.servicio,
			fecha=timezone.localdate() - timedelta(days=1),
			hora_inicio=time(10, 0),
			estado='CONFIRMADA',
		)
		url = reverse('App_agenda:completar_cita', args=[cita.pk])
		self.client.force_login(self.estilista_persona)
		self.assertEqual(self.client.get(url).status_code, 405)
		response = self.client.post(url)
		self.assertRedirects(
			response,
			f'{reverse("App_agenda:e_calendario")}?fecha={cita.fecha.isoformat()}',
		)
		cita.refresh_from_db()
		self.assertEqual(cita.estado, 'FINALIZADA')
		calendar_response = self.client.get(
			reverse('App_agenda:e_calendario'),
			{'fecha': cita.fecha.isoformat(), 'vista': 'dia'},
		)
		self.assertContains(calendar_response, 'line-through')
		self.assertContains(calendar_response, 'Hecho')
		self.assertContains(calendar_response, "cita.estado === 'CONFIRMADA'")
		self.assertContains(calendar_response, 'Marcar Hecho')

		otra_persona = Persona.objects.create_user(
			username='unrelated-stylist',
			password='MakeupTest2026!abc',
			rol='estilista',
		)
		Estilista.objects.create(persona=otra_persona)
		otra_cita = Cita.objects.create(
			cliente=self.cliente,
			estilista=self.estilista,
			servicio=self.servicio,
			fecha=timezone.localdate(),
			hora_inicio=time(12, 0),
			estado='CONFIRMADA',
		)
		self.client.force_login(otra_persona)
		self.assertEqual(
			self.client.post(
				reverse('App_agenda:completar_cita', args=[otra_cita.pk])
			).status_code,
			404,
		)
		self.client.force_login(self.cliente_persona)
		self.assertEqual(self.client.post(url).status_code, 403)

	def test_solicitud_changes_require_post_and_are_scoped_to_stylist(self):
		cita = Cita.objects.create(
			cliente=self.cliente,
			estilista=self.estilista,
			servicio=self.servicio,
			fecha=timezone.localdate() + timedelta(days=1),
			hora_inicio=time(10, 0),
		)
		url = reverse(
			'App_agenda:actualizar_solicitud',
			args=[cita.pk, 'CONFIRMADA'],
		)
		self.client.force_login(self.estilista_persona)

		self.assertEqual(self.client.get(url).status_code, 405)
		response = self.client.post(url, follow=True)
		self.assertEqual(
			response.redirect_chain,
			[(reverse('App_agenda:e_solicitudes'), 302)],
		)
		self.assertContains(
			response,
			f'Cita confirmada: {self.servicio.nombre} el '
			f'{cita.fecha:%d/%m/%Y} a las 10:00.',
		)
		self.assertContains(response, 'Éxito:')
		cita.refresh_from_db()
		self.assertEqual(cita.estado, 'CONFIRMADA')

		cita_rechazada = Cita.objects.create(
			cliente=self.cliente,
			estilista=self.estilista,
			servicio=self.servicio,
			fecha=timezone.localdate() + timedelta(days=3),
			hora_inicio=time(11, 0),
		)
		rechazo = self.client.post(
			reverse(
				'App_agenda:actualizar_solicitud',
				args=[cita_rechazada.pk, 'RECHAZADA'],
			),
			follow=True,
		)
		self.assertContains(
			rechazo,
			f'La solicitud de {self.servicio.nombre} para el '
			f'{cita_rechazada.fecha:%d/%m/%Y} a las 11:00 fue rechazada.',
		)
		cita_rechazada.refresh_from_db()
		self.assertEqual(cita_rechazada.estado, 'RECHAZADA')

		self.client.force_login(self.cliente_persona)
		self.assertEqual(self.client.post(url).status_code, 403)

	def test_client_messages_use_safe_recipient_and_read_notifications(self):
		self.cliente_persona.first_name = 'Ana'
		self.cliente_persona.last_name = 'Ríos'
		self.cliente_persona.save(update_fields=['first_name', 'last_name'])
		self.client.force_login(self.cliente_persona)

		inicio = self.client.get(reverse('App_agenda:c_inicio'))
		self.assertContains(inicio, 'Hola, Ana')
		self.assertContains(inicio, 'Ana Ríos')
		self.assertNotContains(inicio, 'sin leer')

		response = self.client.post(
			reverse('App_agenda:c_mensajes'),
			{'contenido': 'Hola', 'destinatario_id': '99999'},
		)
		self.assertRedirects(response, reverse('App_agenda:c_mensajes'))
		mensaje = Mensaje.objects.get()
		self.assertEqual(mensaje.destinatario, self.estilista_persona)

		otro_usuario = Persona.objects.create_user(
			username='other-client',
			password='MakeupTest2026!abc',
			rol='cliente',
		)
		historial = self.client.get(reverse('App_agenda:c_mensajes'))
		self.assertContains(historial, 'Pendiente')
		Mensaje.objects.create(
			remitente=self.estilista_persona,
			destinatario=self.cliente_persona,
			contenido='Respuesta',
		)
		otro_mensaje = Mensaje.objects.create(
			remitente=self.estilista_persona,
			destinatario=otro_usuario,
			contenido='Mensaje para otra persona',
		)

		inicio = self.client.get(reverse('App_agenda:c_inicio'))
		self.assertContains(inicio, '1 notificación sin leer')
		historial = self.client.get(reverse('App_agenda:c_mensajes'))
		self.assertContains(historial, 'Respondido por la estilista')
		self.assertTrue(
			Mensaje.objects.get(
				destinatario=self.cliente_persona,
				contenido='Respuesta',
			).leido
		)
		inicio = self.client.get(reverse('App_agenda:c_inicio'))
		self.assertNotContains(inicio, 'sin leer')
		otro_mensaje.refresh_from_db()
		self.assertFalse(otro_mensaje.leido)

	def test_client_cannot_send_when_stylist_recipient_is_ambiguous(self):
		otra_persona = Persona.objects.create_user(
			username='another-stylist',
			password='MakeupTest2026!abc',
			rol='estilista',
		)
		Estilista.objects.create(persona=otra_persona)
		self.client.force_login(self.cliente_persona)

		response = self.client.post(
			reverse('App_agenda:c_mensajes'),
			{'contenido': 'No debe llegar a destinatario incorrecto'},
		)

		self.assertEqual(response.status_code, 200)
		self.assertFalse(Mensaje.objects.exists())
		self.assertContains(response, 'No se pudo determinar')

	def test_sidebar_highlights_the_current_stylist_section(self):
		self.client.force_login(self.estilista_persona)

		response = self.client.get(reverse('App_agenda:e_solicitudes'))

		self.assertContains(
			response,
			'href="/agenda/estilista/solicitudes/" class="flex items-center gap-3 px-4 py-2.5 bg-[#d6336c] text-white',
		)

	def test_sidebar_highlights_only_the_current_client_section(self):
		self.client.force_login(self.cliente_persona)

		response = self.client.get(reverse('App_agenda:c_mis_citas'))

		self.assertContains(
			response,
			'href="/agenda/mis-citas/" class="flex items-center gap-3 px-4 py-3 rounded-xl transition-colors text-xs font-medium bg-[#d6336c] text-white',
		)
		self.assertContains(
			response,
			'href="/agenda/inicio/" class="flex items-center gap-3 px-4 py-3 rounded-xl transition-colors text-xs font-medium text-gray-600 hover:bg-gray-50',
		)

# Create your tests here.
