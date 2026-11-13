"""Pruebas añadidas para requisitos RF-CLI, RF-EST y RNF de la matriz 2026."""
from datetime import datetime, time, timedelta
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from App_agenda.forms import estilistas_disponibles
from App_agenda.models import (Cita, Horario, BloqueoAgenda, ConfiguracionAgenda,
                               BitacoraCita, Notificacion)
from App_facturacion.models import RegistroCobro, Pago, CierreCaja
from App_facturacion.servicios import obtener_cobro, registrar_pago
from App_servicios.models import Servicio
from App_usuarios.models import Persona, Cliente, Estilista


class Requisitos2026Tests(TestCase):
    def setUp(self):
        self.client_user=Persona.objects.create_user(username='cliente2026',email='client@example.org',password='Clave2026Test!23',rol='cliente')
        self.cliente=Cliente.objects.create(persona=self.client_user,telefono='12345')
        self.stylist_user=Persona.objects.create_user(username='stylist2026',email='stylist@example.org',password='Clave2026Test!23',rol='estilista')
        self.estilista=Estilista.objects.create(persona=self.stylist_user)
        self.service=Servicio.objects.create(nombre='Maquillaje',categoria='Belleza',precio=Decimal('100000'),duracion=60)
        self.fecha=timezone.localdate()+timedelta(days=4)
        Horario.objects.create(estilista=self.estilista,dia_semana=self.fecha.weekday(),hora_inicio=time(8),hora_fin=time(17))
        self.cita=Cita.objects.create(cliente=self.cliente,estilista=self.estilista,servicio=self.service,
                                     fecha=self.fecha,hora_inicio=time(10),estado='PENDIENTE')

    def test_cita_no_finaliza_sola_y_estados_reales(self):
        self.cita.fecha = timezone.localdate()-timedelta(days=1)
        self.cita.estado = 'CONFIRMADA'
        self.cita.save(update_fields=['fecha','estado'])
        self.assertEqual(self.cita.estado_visual,'CONFIRMADA')
        self.assertNotEqual(self.cita.estado_visual,'FINALIZADA')

    def test_cancelacion_con_dos_horas_y_bitacora(self):
        self.client.force_login(self.client_user)
        res=self.client.post(reverse('App_agenda:cancelar_cita',args=[self.cita.pk]))
        self.assertEqual(res.status_code,302)
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado,'CANCELADA')
        self.assertTrue(BitacoraCita.objects.filter(cita=self.cita,accion='CANCELACION').exists())
        self.assertTrue(Notificacion.objects.filter(persona=self.stylist_user,cita=self.cita).exists())

    def test_cancelacion_no_permitida_dentro_de_dos_horas(self):
        proxima=timezone.localtime(timezone.now()+timedelta(minutes=80))
        self.cita.fecha,self.cita.hora_inicio=proxima.date(),proxima.time().replace(second=0,microsecond=0)
        self.cita.save(update_fields=['fecha','hora_inicio'])
        self.client.force_login(self.client_user)
        self.client.post(reverse('App_agenda:cancelar_cita',args=[self.cita.pk]))
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado,'PENDIENTE')

    def test_reprogramacion_solo_pendiente_con_disponibilidad(self):
        nueva_fecha=self.fecha+timedelta(days=7)
        Horario.objects.create(estilista=self.estilista,dia_semana=nueva_fecha.weekday(),hora_inicio=time(8),hora_fin=time(17))
        self.client.force_login(self.client_user)
        self.client.post(reverse('App_agenda:reprogramar_cita',args=[self.cita.pk]),
                         {'fecha':nueva_fecha.isoformat(),'hora_inicio':'11:00'})
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.fecha,nueva_fecha)
        self.assertEqual(self.cita.estado,'PENDIENTE')
        self.assertTrue(BitacoraCita.objects.filter(cita=self.cita,accion='REPROGRAMACION').exists())

    def test_bloqueo_inhabilita_horario_y_confirmacion(self):
        BloqueoAgenda.objects.create(estilista=self.estilista,fecha_inicio=self.fecha,fecha_fin=self.fecha,motivo='Descanso')
        self.assertNotIn(self.estilista,estilistas_disponibles(self.fecha,time(11),self.service))
        self.client.force_login(self.stylist_user)
        self.client.post(reverse('App_agenda:actualizar_solicitud',args=[self.cita.pk,'CONFIRMADA']))
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado,'PENDIENTE')

    def test_confirmacion_crea_cobro_y_notificacion(self):
        self.client.force_login(self.stylist_user)
        self.client.post(reverse('App_agenda:actualizar_solicitud',args=[self.cita.pk,'CONFIRMADA']))
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado,'CONFIRMADA')
        registro=RegistroCobro.objects.get(cita=self.cita)
        self.assertEqual(registro.monto_total,Decimal('100000'))
        self.assertEqual(registro.saldo_pendiente,Decimal('100000'))
        self.assertTrue(Notificacion.objects.filter(persona=self.client_user,cita=self.cita).exists())

    def test_pagos_saldo_y_metodos_seguridad(self):
        self.cita.estado='CONFIRMADA';self.cita.save(update_fields=['estado'])
        pago=registrar_pago(self.cita,Decimal('25000'),'EFECTIVO',self.stylist_user)
        r=RegistroCobro.objects.get(cita=self.cita)
        self.assertEqual(r.saldo_pendiente,Decimal('75000'))
        self.assertEqual(Pago.objects.get(pk=pago.pk).monto,Decimal('25000'))
        for monto in ('0','-1','75000.01','hola','5.999'):
            with self.subTest(monto=monto),self.assertRaises(ValidationError):
                registrar_pago(self.cita,monto,'EFECTIVO',self.stylist_user)
        with self.assertRaises(ValidationError):
            registrar_pago(self.cita,'100','TARJETA',self.stylist_user)

    def test_cierre_caja_impide_pagos_posteriores(self):
        self.cita.estado='CONFIRMADA';self.cita.save(update_fields=['estado'])
        registrar_pago(self.cita,'10000','TRANSFERENCIA',self.stylist_user)
        self.client.force_login(self.stylist_user)
        self.client.post(reverse('App_facturacion:cierre_caja'))
        cierre=CierreCaja.objects.get(fecha=timezone.localdate())
        self.assertEqual(cierre.monto_transferencia,Decimal('10000'))
        with self.assertRaises(ValidationError):
            registrar_pago(self.cita,'100','EFECTIVO',self.stylist_user)

    def test_reporte_incluye_dinero_recibido_en_citas_finalizadas(self):
        self.cita.estado='FINALIZADA';self.cita.save(update_fields=['estado'])
        registrar_pago(self.cita,'1000','EFECTIVO',self.stylist_user)
        self.client.force_login(self.stylist_user)
        response=self.client.get(reverse('App_facturacion:reportes'))
        self.assertEqual(response.context['total_ingresos'],Decimal('1000'))
        self.assertEqual(response.context['total_pendiente'],Decimal('99000'))

    def test_recibo_privado_y_exportaciones(self):
        self.cita.estado='CONFIRMADA';self.cita.save(update_fields=['estado'])
        obtener_cobro(self.cita)
        otro=Persona.objects.create_user(username='otro',password='prueba123456',rol='cliente')
        Cliente.objects.create(persona=otro)
        url=reverse('App_facturacion:recibo',args=[self.cita.pk])
        self.client.force_login(otro)
        self.assertEqual(self.client.get(url).status_code,404)
        self.client.force_login(self.client_user)
        self.assertEqual(self.client.get(url).status_code,200)
        self.client.force_login(self.stylist_user)
        xlsx=self.client.get(reverse('App_facturacion:exportar_reporte',args=['xlsx']))
        pdf=self.client.get(reverse('App_facturacion:exportar_reporte',args=['pdf']))
        self.assertEqual(xlsx.status_code,200)
        self.assertTrue(xlsx.content.startswith(b'PK'))
        self.assertEqual(pdf.status_code,200)
        self.assertTrue(pdf.content.startswith(b'%PDF'))

    def test_notificaciones_accesibles_para_ambos_roles(self):
        Notificacion.objects.create(persona=self.stylist_user,titulo='Solicitud',contenido='Nueva cita')
        self.client.force_login(self.stylist_user)
        resp=self.client.get(reverse('App_agenda:notificaciones'))
        self.assertContains(resp,'Solicitud')
        self.client.post(reverse('App_agenda:notificaciones'))
        self.assertFalse(Notificacion.objects.filter(persona=self.stylist_user,leida=False).exists())

    def test_preferencia_pago_y_no_cobro_en_reserva_pendiente(self):
        self.cita.metodo_pago_preferido='TRANSFERENCIA';self.cita.save(update_fields=['metodo_pago_preferido'])
        self.assertEqual(self.cita.get_metodo_pago_preferido_display(),'Transferencia bancaria')
        self.assertFalse(RegistroCobro.objects.filter(cita=self.cita).exists())

    def test_recuperacion_con_correo_y_token(self):
        from django.test import override_settings
        from django.core import mail
        with override_settings(MAILERS={'default': {'BACKEND':'django.core.mail.backends.locmem.EmailBackend'}}):
            resp=self.client.post(reverse('App_usuarios:password_reset'),{'email':'client@example.org'})
            self.assertEqual(resp.status_code,302)
            self.assertEqual(len(mail.outbox),1)
            self.assertIn('restablecer',mail.outbox[0].body)

    def test_administradora_puede_bloquear_dia_sin_citas_confirmadas(self):
        self.client.force_login(self.stylist_user)
        res=self.client.post(reverse('App_usuarios:configuracion'),{
            'accion':'guardar_bloqueo','fecha_inicio':self.fecha,'fecha_fin':self.fecha,
            'motivo':'Festivo'})
        self.assertEqual(res.status_code,302)
        self.assertTrue(BloqueoAgenda.objects.filter(estilista=self.estilista).exists())
        disponible=self.client.get(reverse('App_agenda:disponibilidad_reserva'),{
            'fecha':self.fecha.isoformat(),'servicio_id':self.service.pk})
        # Un estilista solo puede consultar reservas desde su panel: la API es para clientas.
        self.assertEqual(disponible.status_code,403)
        self.client.force_login(self.client_user)
        disponible=self.client.get(reverse('App_agenda:disponibilidad_reserva'),{
            'fecha':self.fecha.isoformat(),'servicio_id':self.service.pk})
        franjas=disponible.json()['slots']
        self.assertEqual(len(franjas),29)
        self.assertTrue(all(not franja['disponible'] for franja in franjas))
        self.assertTrue(all(franja['estado']=='unavailable' for franja in franjas))

    def test_media_privada_no_se_expone_directamente(self):
        self.client.logout()
        response=self.client.get('/media/citas/archivos/secret.jpg')
        self.assertEqual(response.status_code,404)

    def test_politicas_de_cancelacion_configurables(self):
        cfg=ConfiguracionAgenda.objects.create(estilista=self.estilista, anticipacion_reserva_minutos=60,
                                                anticipacion_cancelacion_minutos=10000)
        self.assertFalse(self.cita.puede_cancelar)
        cfg.anticipacion_cancelacion_minutos=120
        cfg.save(update_fields=['anticipacion_cancelacion_minutos'])
        self.assertTrue(self.cita.puede_cancelar)
