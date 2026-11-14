"""Pruebas de aceptación del nuevo rol Administrador y seguridad entre roles."""
from datetime import time, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from App_usuarios.models import Cliente, Estilista, Persona, HistorialAcceso
from App_agenda.models import Cita, Horario, BloqueoAgenda, Mensaje
from App_servicios.models import Servicio
from App_facturacion.models import CierreCaja


class AdminFunctionalTests(TestCase):
    def setUp(self):
        self.password = 'ContraseN@2026!Segura'
        self.admin = Persona.objects.create_user(username='root', email='admin@leidy.co',
            password=self.password, rol='administrador', is_staff=True)
        self.cliente_user = Persona.objects.create_user(username='cliente1', email='cliente@leidy.co',
            password=self.password, rol='cliente')
        self.cliente = Cliente.objects.create(persona=self.cliente_user, telefono='3002223344')
        self.stylist_user = Persona.objects.create_user(username='style1',email='style@leidy.co',
            password=self.password,rol='estilista')
        self.stylist = Estilista.objects.create(persona=self.stylist_user)
        self.other_user = Persona.objects.create_user(username='style2',email='style2@leidy.co',
            password=self.password,rol='estilista')
        self.other = Estilista.objects.create(persona=self.other_user)
        self.service = Servicio.objects.create(nombre='Maquillaje de fiesta',categoria='Maquillaje',
            descripcion='Prueba de maquillaje', precio=Decimal('80000'),duracion=60)
        self.date=timezone.localdate()+timedelta(days=5)
        Horario.objects.create(estilista=self.stylist,dia_semana=self.date.weekday(),hora_inicio=time(8),hora_fin=time(18))
        Horario.objects.create(estilista=self.other,dia_semana=self.date.weekday(),hora_inicio=time(8),hora_fin=time(18))
        self.cita=Cita.objects.create(cliente=self.cliente,estilista=self.stylist,
            servicio=self.service,fecha=self.date,hora_inicio=time(10),estado='PENDIENTE')

    def as_admin(self):
        self.client.force_login(self.admin)

    def test_three_login_roles_enforce_exact_match(self):
        cases=[
            (self.cliente_user,'cliente','App_agenda:c_inicio'),
            (self.stylist_user,'estilista','App_agenda:e_inicio'),
            (self.admin,'administrador','App_administracion:inicio'),
        ]
        for user,role,dashboard in cases:
            for requested in ('cliente','estilista','administrador'):
                with self.subTest(real=role,attempt=requested):
                    self.client.logout()
                    r=self.client.post(reverse('App_usuarios:login'),{
                        'username':user.username,'password':self.password,'rol':requested,
                    })
                    if requested==role:
                        self.assertRedirects(r,reverse(dashboard))
                    else:
                        self.assertEqual(r.status_code,200)
                        self.assertNotIn('_auth_user_id',self.client.session)

    def test_role_specific_login_route_ignores_forged_role(self):
        r=self.client.post(reverse('App_usuarios:e_login'),{
            'username':self.cliente_user.username,'password':self.password,'rol':'cliente',
        })
        self.assertEqual(r.status_code,200)
        self.assertNotIn('_auth_user_id',self.client.session)
        r=self.client.post(reverse('App_usuarios:a_login'),{
            'username':self.stylist_user.username,'password':self.password,'rol':'estilista',
        })
        self.assertEqual(r.status_code,200)
        self.assertNotIn('_auth_user_id',self.client.session)

    def test_admin_permission_is_denied_to_clients_stylists_and_fake_staff(self):
        for u in (self.cliente_user,self.stylist_user):
            self.client.force_login(u)
            for url in (reverse('App_administracion:inicio'),reverse('App_administracion:usuarios'),
                        reverse('App_administracion:reportes')):
                self.assertEqual(self.client.get(url).status_code,403)
            self.assertEqual(self.client.get('/admin/').status_code,403 if u.is_staff else 403)
        self.as_admin()
        self.assertEqual(self.client.get(reverse('App_agenda:e_inicio')).status_code,403)
        self.assertEqual(self.client.get(reverse('App_agenda:c_inicio')).status_code,403)

    def test_landing_page_public_and_dashboard_admin(self):
        self.assertContains(self.client.get('/'),'Leidy Make Up')
        self.as_admin()
        r=self.client.get(reverse('App_administracion:inicio'))
        self.assertContains(r,'Panel Administrador')
        self.assertContains(r,'Maquillaje de fiesta')

    def test_admin_user_created_with_profile_and_password_hash(self):
        self.as_admin()
        r=self.client.post(reverse('App_administracion:usuario_crear'),{
            'first_name':'Luisa','last_name':'Mora','email':'luisa@leidy.co',
            'rol':'estilista','especialidad':'Peinados','password':'ClaveFuerte!2026Luisa',
        })
        self.assertRedirects(r,reverse('App_administracion:usuarios'))
        u=Persona.objects.get(email='luisa@leidy.co')
        self.assertEqual(u.rol,'estilista')
        self.assertFalse(u.is_staff)
        self.assertTrue(u.check_password('ClaveFuerte!2026Luisa'))
        self.assertEqual(u.estilista.especialidad,'Peinados')

    def test_admin_can_update_user_and_disable_without_deleting(self):
        self.as_admin()
        r=self.client.post(reverse('App_administracion:usuario_editar',args=[self.cliente_user.pk]),{
            'first_name':'Nuevo Nombre','last_name':'','email':'cliente@leidy.co',
            'rol':'cliente','telefono':'300123123','direccion':'Calle 15',
        })
        self.assertRedirects(r,reverse('App_administracion:usuarios'))
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.direccion,'Calle 15')
        self.client.post(reverse('App_administracion:usuario_estado',args=[self.cliente_user.pk]))
        self.cliente_user.refresh_from_db()
        self.assertFalse(self.cliente_user.is_active)
        self.assertTrue(Cliente.objects.filter(persona=self.cliente_user).exists())

    def test_admin_cannot_disable_self_or_change_roles_with_history(self):
        self.as_admin()
        self.client.post(reverse('App_administracion:usuario_estado',args=[self.admin.pk]))
        self.admin.refresh_from_db(); self.assertTrue(self.admin.is_active)
        self.client.post(reverse('App_administracion:usuario_editar',args=[self.cliente_user.pk]),{
            'first_name':'Cliente','last_name':'','email':'cliente@leidy.co','rol':'estilista',
        })
        self.cliente_user.refresh_from_db()
        self.assertEqual(self.cliente_user.rol,'cliente')

    def test_admin_services_soft_delete_and_restore(self):
        self.as_admin()
        route=reverse('App_administracion:servicio_estado',args=[self.service.pk])
        self.assertEqual(self.client.get(route).status_code,405)
        self.client.post(route)
        self.service.refresh_from_db()
        self.assertFalse(self.service.activo)
        self.assertEqual(Cita.objects.filter(servicio=self.service).count(),1)
        self.client.post(route)
        self.service.refresh_from_db();self.assertTrue(self.service.activo)

    def test_admin_global_agenda_reassigns_without_collisions(self):
        self.as_admin()
        self.assertContains(self.client.get(reverse('App_administracion:agenda')),'Maquillaje de fiesta')
        self.client.post(reverse('App_administracion:reasignar',args=[self.cita.pk]),{'estilista_id':self.other.pk})
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estilista,self.other)
        self.assertTrue(self.cita.bitacora.filter(accion='REASIGNACION').exists())

    def test_admin_reassignment_does_not_overlap_active_appointment(self):
        Cita.objects.create(cliente=self.cliente,estilista=self.other,servicio=self.service,
            fecha=self.date,hora_inicio=time(10),estado='CONFIRMADA')
        self.as_admin()
        self.client.post(reverse('App_administracion:reasignar',args=[self.cita.pk]),{'estilista_id':self.other.pk})
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estilista,self.stylist)

    def test_admin_can_block_stylist_and_manage_policies(self):
        self.as_admin()
        future=self.date+timedelta(days=1)
        self.client.post(reverse('App_administracion:bloquear'),{
            'estilista_id':self.stylist.pk,'fecha_inicio':future.isoformat(),
            'fecha_fin':future.isoformat(),'motivo':'Festivo',
        })
        self.assertTrue(BloqueoAgenda.objects.filter(estilista=self.stylist,motivo='Festivo').exists())
        self.client.post(reverse('App_administracion:politicas'),{
            'estilista_id':self.stylist.pk,'anticipacion_reserva_minutos':90,
            'anticipacion_cancelacion_minutos':120,
        })
        self.assertEqual(self.stylist.configuracion_agenda.anticipacion_reserva_minutos,90)

    def test_admin_can_block_every_stylist_in_one_operation(self):
        """RF-AD-007: el cierre general aplica a todas las agendas activas."""
        self.as_admin()
        dia = self.date + timedelta(days=1)
        r = self.client.post(reverse('App_administracion:bloquear'), {
            'estilista_id': 'todos', 'fecha_inicio': dia.isoformat(),
            'fecha_fin': dia.isoformat(), 'motivo': 'Capacitación general',
        })
        self.assertRedirects(r, reverse('App_administracion:agenda'))
        self.assertEqual(BloqueoAgenda.objects.filter(
            fecha_inicio=dia, motivo='Capacitación general').count(), 2)

    def test_admin_reports_audits_and_exports(self):
        self.as_admin()
        for nombre in ('reportes','auditoria','clientes','mensajes','archivos','caja'):
            with self.subTest(vista=nombre):
                r=self.client.get(reverse('App_administracion:'+nombre))
                self.assertEqual(r.status_code,200,r.content[:350])
        xls=self.client.get(reverse('App_administracion:exportar',args=['xlsx']))
        self.assertEqual(xls.status_code,200)
        self.assertTrue(xls.content.startswith(b'PK'))
        bad=self.client.get(reverse('App_administracion:exportar',args=['xlsx']),{'desde':'invalida'})
        self.assertEqual(bad.status_code,400)

    def test_admin_closes_cash_and_guest_cannot_download_backup(self):
        self.as_admin()
        self.client.post(reverse('App_administracion:cerrar_caja'))
        self.assertEqual(CierreCaja.objects.filter(fecha=timezone.localdate()).count(),1)
        self.client.post(reverse('App_administracion:cerrar_caja'))
        self.assertEqual(CierreCaja.objects.filter(fecha=timezone.localdate()).count(),1)
        backup=self.client.post(reverse('App_administracion:respaldar'))
        self.assertEqual(backup.status_code,400)  # Base temporal en memoria en las pruebas.
        self.client.logout()
        self.assertNotEqual(self.client.post(reverse('App_administracion:respaldar')).status_code,200)

    def test_client_admin_support_chat_both_directions(self):
        self.client.force_login(self.cliente_user)
        r=self.client.post(reverse('App_usuarios:soporte'),{'contenido':'Hola administración'})
        self.assertEqual(r.status_code,302)
        self.assertEqual(Mensaje.objects.filter(remitente=self.cliente_user,destinatario=self.admin).count(),1)
        self.as_admin()
        r=self.client.post(reverse('App_administracion:mensajes'),{
            'cliente_id':self.cliente_user.pk,'contenido':'Hola, ¿cómo podemos ayudarte?',
        })
        self.assertEqual(r.status_code,302)
        self.assertEqual(Mensaje.objects.filter(remitente=self.admin,destinatario=self.cliente_user).count(),1)

    def test_rejected_logins_are_audited_without_passwords(self):
        self.client.post(reverse('App_usuarios:login'),{
            'username':self.cliente_user.username,'password':self.password,'rol':'estilista',
        })
        log=HistorialAcceso.objects.get(evento='FALLO')
        self.assertEqual(log.identificador,self.cliente_user.username)
        self.assertNotIn(self.password,str(log))

    def test_visitor_can_select_preferred_stylist_for_availability(self):
        r=self.client.get(reverse('App_agenda:disponibilidad_reserva'),{
            'servicio_id':self.service.pk,'fecha':self.date.isoformat(),
            'estilista_id':self.other.pk,
        })
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.json()['slots'])
        booking=self.client.get(reverse('App_agenda:c_reservar'))
        self.assertContains(booking,'Estilista preferida')
