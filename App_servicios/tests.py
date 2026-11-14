from datetime import date, time

from django.test import TestCase
from django.urls import reverse

from App_agenda.models import Cita
from App_usuarios.models import Cliente, Estilista, Persona

from .models import Servicio


class ServicioWorkflowTests(TestCase):
	def setUp(self):
		self.estilista_persona = Persona.objects.create_user(
			username='stylist', password='MakeupTest2026!abc', rol='estilista'
		)
		Estilista.objects.create(persona=self.estilista_persona)
		self.cliente_persona = Persona.objects.create_user(
			username='client', password='MakeupTest2026!abc', rol='cliente'
		)
		Cliente.objects.create(persona=self.cliente_persona)

	def test_stylist_crud_updates_the_customer_catalog(self):
		self.client.force_login(self.estilista_persona)
		create_response = self.client.post(
			reverse('App_servicios:crear'),
			{
				'nombre': 'Maquillaje social',
				'categoria': 'Maquillaje',
				'descripcion': 'Servicio de prueba',
				'precio': '65000.00',
				'duracion': '60',
			},
		)
		self.assertRedirects(create_response, reverse('App_servicios:lista'))
		servicio = Servicio.objects.get(nombre='Maquillaje social')

		self.client.post(
			reverse('App_servicios:editar', kwargs={'pk': servicio.pk}),
			{
				'nombre': 'Maquillaje de noche',
				'categoria': 'Maquillaje',
				'descripcion': 'Actualizado',
				'precio': '75000.00',
				'duracion': '90',
			},
		)
		servicio.refresh_from_db()
		self.assertEqual(servicio.nombre, 'Maquillaje de noche')
		self.assertEqual(servicio.duracion, 90)

		self.client.logout()
		catalogo_publico = self.client.get(reverse('App_servicios:lista'))
		self.assertContains(catalogo_publico, 'Maquillaje de noche')
		self.client.force_login(self.estilista_persona)

		self.client.post(
			reverse('App_servicios:eliminar', kwargs={'pk': servicio.pk})
		)
		servicio.refresh_from_db()
		self.assertFalse(servicio.activo)

		self.client.force_login(self.cliente_persona)
		catalogo = self.client.get(reverse('App_servicios:lista'))
		self.assertEqual(catalogo.status_code, 200)
		self.assertNotContains(catalogo, 'Maquillaje de noche')

	def test_deactivated_service_is_hidden_from_customers_and_available_for_future_reservations(self):
		servicio = Servicio.objects.create(
			nombre='Servicio temporal',
			categoria='Maquillaje',
			precio='50000.00',
			duracion=60,
		)
		self.client.force_login(self.estilista_persona)

		response = self.client.post(
			reverse('App_servicios:eliminar', args=[servicio.pk]),
			follow=True,
		)

		self.assertContains(response, 'El servicio fue desactivado')
		self.assertContains(response, 'Servicios desactivados')
		self.assertContains(response, 'Servicio desactivado')
		self.assertContains(response, 'Reactivar')
		self.assertContains(response, 'Eliminar permanentemente')
		self.assertContains(response, 'Servicio temporal')
		servicio.refresh_from_db()
		self.assertFalse(servicio.activo)

		self.client.force_login(self.cliente_persona)
		catalogo = self.client.get(reverse('App_servicios:lista'))
		reserva = self.client.get(reverse('App_agenda:c_reservar'))
		self.assertNotContains(catalogo, 'Servicio temporal')
		self.assertNotIn(
			servicio,
			reserva.context['form'].fields['servicio'].queryset,
		)

	def test_reactivating_service_restores_it_to_customer_catalog(self):
		servicio = Servicio.objects.create(
			nombre='Servicio reactivable',
			categoria='Maquillaje',
			precio='50000.00',
			duracion=60,
			activo=False,
		)
		self.client.force_login(self.estilista_persona)

		response = self.client.post(
			reverse('App_servicios:reactivar', args=[servicio.pk]),
			follow=True,
		)

		self.assertContains(response, 'El servicio fue reactivado correctamente.')
		servicio.refresh_from_db()
		self.assertTrue(servicio.activo)
		self.assertContains(response, 'Servicios activos')
		self.assertNotContains(response, 'Servicio desactivado')

		self.client.force_login(self.cliente_persona)
		catalogo = self.client.get(reverse('App_servicios:lista'))
		self.assertContains(catalogo, 'Servicio reactivable')

	def test_permanent_deletion_removes_service_without_appointment_history(self):
		servicio = Servicio.objects.create(
			nombre='Servicio sin historial',
			categoria='Maquillaje',
			precio='50000.00',
			duracion=60,
			activo=False,
		)
		self.client.force_login(self.estilista_persona)

		response = self.client.post(
			reverse('App_servicios:eliminar_permanentemente', args=[servicio.pk]),
			follow=True,
		)

		self.assertContains(response, 'El servicio fue eliminado permanentemente.')
		self.assertFalse(Servicio.objects.filter(pk=servicio.pk).exists())
		self.assertNotContains(response, 'Servicio sin historial')

	def test_permanent_deletion_preserves_inactive_service_with_appointment_history(self):
		servicio = Servicio.objects.create(
			nombre='Servicio con historial',
			categoria='Maquillaje',
			precio='50000.00',
			duracion=60,
			activo=False,
		)
		cliente = Cliente.objects.get(persona=self.cliente_persona)
		estilista = Estilista.objects.get(persona=self.estilista_persona)
		Cita.objects.create(
			cliente=cliente,
			estilista=estilista,
			servicio=servicio,
			fecha=date(2026, 12, 1),
			hora_inicio=time(10, 0),
		)
		self.client.force_login(self.estilista_persona)

		response = self.client.post(
			reverse('App_servicios:eliminar_permanentemente', args=[servicio.pk]),
			follow=True,
		)

		self.assertContains(response, 'tiene citas asociadas')
		servicio.refresh_from_db()
		self.assertFalse(servicio.activo)
		self.assertTrue(Cita.objects.filter(servicio=servicio).exists())

	def test_service_admin_actions_require_post_and_stylist_role(self):
		servicio = Servicio.objects.create(
			nombre='Servicio protegido',
			categoria='Maquillaje',
			precio='50000.00',
			duracion=60,
			activo=False,
		)
		reactivate_url = reverse('App_servicios:reactivar', args=[servicio.pk])
		delete_url = reverse(
			'App_servicios:eliminar_permanentemente',
			args=[servicio.pk],
		)

		self.client.force_login(self.estilista_persona)
		self.assertEqual(self.client.get(reactivate_url).status_code, 405)
		self.assertEqual(self.client.get(delete_url).status_code, 405)

		self.client.force_login(self.cliente_persona)
		self.assertEqual(self.client.post(reactivate_url).status_code, 403)
		self.assertEqual(self.client.post(delete_url).status_code, 403)
		servicio.refresh_from_db()
		self.assertFalse(servicio.activo)
		self.assertTrue(Servicio.objects.filter(pk=servicio.pk).exists())

	def test_administrative_catalog_separates_active_and_inactive_without_duplicates(self):
		activo = Servicio.objects.create(
			nombre='Único servicio activo',
			categoria='Maquillaje',
			precio='50000.00',
			duracion=60,
		)
		inactivo = Servicio.objects.create(
			nombre='Único servicio inactivo',
			categoria='Maquillaje',
			precio='40000.00',
			duracion=45,
			activo=False,
		)
		self.client.force_login(self.estilista_persona)

		response = self.client.get(reverse('App_servicios:lista'))

		self.assertEqual(list(response.context['servicios']), [activo])
		self.assertEqual(
			list(response.context['servicios_desactivados']),
			[inactivo],
		)
		self.assertEqual(
			response.content.count(f'data-service-id="{activo.pk}"'.encode()),
			1,
		)
		self.assertEqual(
			response.content.count(f'data-service-id="{inactivo.pk}"'.encode()),
			1,
		)
		self.assertContains(response, 'Único servicio inactivo')
		self.assertEqual(response.content.count(b'Servicio desactivado'), 1)

	def test_stylist_service_form_routes_render_existing_template(self):
		self.client.force_login(self.estilista_persona)
		create_page = self.client.get(reverse('App_servicios:crear'))
		self.assertEqual(create_page.status_code, 200)
		self.assertTemplateUsed(create_page, 'E_servicio_form.html')

		servicio = Servicio.objects.create(
			nombre='Peinado',
			categoria='Cabello',
			precio='40000.00',
			duracion=45,
		)
		edit_page = self.client.get(
			reverse('App_servicios:editar', kwargs={'pk': servicio.pk})
		)
		self.assertEqual(edit_page.status_code, 200)
		self.assertTemplateUsed(edit_page, 'E_servicio_form.html')
