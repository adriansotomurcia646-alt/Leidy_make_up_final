"""Pruebas estructurales del diagrama relacional aprobado."""
from datetime import date, time
from django.test import TestCase
from App_usuarios.models import Persona, Cliente, Estilista
from App_servicios.models import Servicio
from App_agenda.models import (Cita, Horario, ConfiguracionAgenda, BloqueoAgenda,
    CitaArchivo, Mensaje, BitacoraCita, Notificacion)
from App_facturacion.models import RegistroCobro, Pago, CierreCaja

class RelacionesAprobadasTests(TestCase):
    def test_las_claves_foraneas_coinciden_con_el_diagrama(self):
        relaciones = {
            Cliente: {'persona':Persona},
            Estilista: {'persona':Persona},
            Horario: {'estilista':Estilista},
            ConfiguracionAgenda: {'estilista':Estilista},
            BloqueoAgenda: {'estilista':Estilista},
            Cita: {'cliente':Cliente, 'estilista':Estilista, 'servicio':Servicio},
            CitaArchivo: {'cita':Cita},
            Mensaje: {'cita':Cita},
            BitacoraCita: {'cita':Cita, 'persona':Persona},
            Notificacion: {'persona':Persona},
            RegistroCobro: {'cita':Cita},
            Pago: {'registro_cobro':RegistroCobro},
            CierreCaja: {'cerrado_por':Persona},
        }
        for entidad, campos in relaciones.items():
            for nombre, objetivo in campos.items():
                with self.subTest(entidad=entidad.__name__, campo=nombre):
                    self.assertEqual(entidad._meta.get_field(nombre).remote_field.model, objetivo)
        self.assertTrue(Cliente._meta.get_field('persona').one_to_one)
        self.assertTrue(Estilista._meta.get_field('persona').one_to_one)
        self.assertTrue(ConfiguracionAgenda._meta.get_field('estilista').one_to_one)
        self.assertTrue(RegistroCobro._meta.get_field('cita').one_to_one)
