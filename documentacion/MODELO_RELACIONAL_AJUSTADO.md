# Conciliación: diagrama relacional → models.py

Documento basado en la imagen aprobada `referencias/Modelo_Relacional_Aprobado.png`.
**PK**: llave primaria; **FK**: clave foránea; **1:1**: relación exclusiva; **N**: muchas filas.

| Entidad | App / modelo Django | Columnas clave y correspondencias |
|---|---|---|
| Persona | `App_usuarios.Persona` | PK `id`; `username`, `email`, `password`, `rol`; nombres y permisos de Django; email único no vacío (ignorando mayúsculas) |
| Cliente | `App_usuarios.Cliente` | `persona_id` FK 1:1/única; `telefono`, `direccion` |
| Estilista | `App_usuarios.Estilista` | `persona_id` FK 1:1/única; `especialidad` |
| HistorialAcceso | `App_usuarios.HistorialAcceso` | PK `id`; `persona_id` FK opcional en intentos sin usuario identificado; `identificador`, `evento`, `fecha` |
| Servicio | `App_servicios.Servicio` | PK `id`; `nombre`, `categoria`, `precio`, `duracion`, `activo`; `descripcion` adicional |
| Horario | `App_agenda.Horario` | PK `id`; `estilista_id` FK; `dia_semana`, `hora_inicio`, `hora_fin`, `activo` |
| ConfiguracionAgenda | `App_agenda.ConfiguracionAgenda` | PK `id`; `estilista_id` FK 1:1/única; antelación para reservar/cancelar |
| BloqueoAgenda | `App_agenda.BloqueoAgenda` | PK `id`; `estilista_id` FK; intervalo y motivo de bloqueo |
| Cita | `App_agenda.Cita` | PK `id`; `cliente_id`, `estilista_id`, `servicio_id` FK; `fecha`, `hora_inicio`, `hora_fin`, `estado`; notas y metadatos |
| CitaArchivo | `App_agenda.CitaArchivo` | PK `id`; `cita_id` FK; ruta de adjunto, tipo, nombre |
| Mensaje | `App_agenda.Mensaje` | PK `id`; `cita_id` FK opcional; `remitente_id`, `destinatario_id` FK adicionales para chat/soporte; `contenido` |
| BitacoraCita | `App_agenda.BitacoraCita` | PK `id`; `cita_id`, `persona_id` FK (persona opcional si el usuario fue eliminado); `accion`, estados, detalle |
| Notificacion | `App_agenda.Notificacion` | PK `id`; `persona_id` FK; `cita_id` FK opcional; `titulo`, `contenido`, `leida` |
| RegistroCobro | `App_facturacion.RegistroCobro` | PK `id`; `cita_id` FK 1:1/única; `cliente_id` FK adicional; total, abonos y saldo |
| Pago | `App_facturacion.Pago` | PK `id`; `registro_cobro_id` FK; `monto`, `metodo`, `referencia` |
| CierreCaja | `App_facturacion.CierreCaja` | PK `id`; `cerrado_por_id` FK a Persona; `fecha`, totales por método, `cerrado_en` |

## Cardinalidades y decisiones

- `Persona → Cliente` y `Persona → Estilista` son **1:0..1** (OneToOneField).
- `Estilista → ConfiguracionAgenda` es **1:0..1** (OneToOneField).
- `Cita → RegistroCobro` es **1:0..1** (OneToOneField), mientras `RegistroCobro → Pago` es **1:N**.
- `Mensaje.cita` es opcional: un mensaje de soporte a Administración puede no asociarse a ninguna cita;
  los mensajes cliente↔estilista ahora guardan la última cita compartida.
- Para que la auditoría se pueda conservar, `HistorialAcceso.persona` y
  `BitacoraCita.persona` aceptan NULL. Para mensajes y notificaciones se conservan
  referencias a personas autenticadas.
- Las columnas `password` son el **hash Django**, nunca la contraseña en texto plano.
- `Pago.registro_cobro_id` y `CierreCaja.cerrado_por_id` coinciden exactamente
  con las claves foráneas mostradas en el diagrama.

## Migraciones nuevas

`App_usuarios/migrations/0004_relaciones_persona_y_email_unico.py` y
`App_agenda/migrations/0009_relaciones_cita_persona_mensaje.py` y
`App_facturacion/migrations/0004_pago_registro_cobro_fk.py` actualizan
el esquema sin eliminar las demás tablas ni recrear cuentas. Para una base
existente, comprueba previamente que no haya emails repetidos ignorando
mayúsculas, pues el índice único rechazaría esos duplicados.

## Verificación recomendada

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test App_usuarios.tests_modelo_relacional App_agenda.tests_modelo_relacional
python manage.py test
```
