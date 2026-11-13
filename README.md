# Leidy Make Up — proyecto Django reconstruido

Versión académica, ajustada al **modelo relacional de 16 entidades** y contrastada con
**53 historias/requisitos funcionales** (Visitante 3, Cliente 18, Estilista 14,
Administrador 18). Se incluyen copias de los tres originales bajo `documentacion/referencias/`.

## Cambio solicitado: sin verificación de correo

Al registrarse, el cliente entrega **nombre, apellidos, teléfono, correo único y
contraseña segura**. El sistema comprueba formato y duplicidad del correo, **crea
la cuenta ACTIVA inmediatamente** y permite iniciar sesión: **no envía correos
de activación ni pide abrir un enlace para validar la cuenta**. El correo de
recuperación de contraseña es una función separada, conservada por RF-CLI-003;
en local se imprime en la consola si no hay servidor SMTP configurado.

## Cómo ejecutar en Linux (Nobara/Fedora, Ubuntu, etc.)

Abre una terminal dentro de la carpeta del proyecto (la que contiene `manage.py`):

```bash
bash iniciar_linux.sh
```

El script crea `.venv`, instala requisitos, genera una `.env` local con clave
segura si no existe, ejecuta las migraciones y levanta el servidor. Visita
`http://127.0.0.1:8000/`.

Para crear una cuenta de Administrador, en **otra terminal** dentro del proyecto:

```bash
source .venv/bin/activate
python manage.py createsuperuser
```

Luego ingresa en `/usuarios/administrador/login/` o `/admin/`.
Crea desde `/administracion/` al menos una estilista, un servicio activo y sus
horarios laborales. Sin estos datos, el calendario no tendrá horas reservables.

## Instalación manual

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env  # Completar DJANGO_SECRET_KEY con una clave segura.
python manage.py migrate
python manage.py check
python manage.py runserver
```

No subas el archivo `.env` ni `db.sqlite3` a GitHub. Para despliegue con PostgreSQL instala `pip install -r requirements-postgresql.txt` y configura las variables `DB_*`.

## Arquitectura y relaciones

| Aplicación | Modelos |
|---|---|
| App_usuarios | Persona (cuenta de Django), Cliente, Estilista, HistorialAcceso |
| App_servicios | Servicio |
| App_agenda | Horario, Cita, ConfiguracionAgenda, BloqueoAgenda, CitaArchivo, Mensaje, BitacoraCita, Notificacion |
| App_facturacion | RegistroCobro, Pago, CierreCaja |
| App_inicio | Portada pública |
| App_administracion | Panel administrativo, sin modelo adicional |

**Relaciones críticas:** Persona 1:0..1 Cliente y Persona 1:0..1 Estilista;
Estilista 1:N Horario, 1:1 ConfiguracionAgenda y 1:N BloqueoAgenda;
Cliente/Estilista/Servicio 1:N Cita; Cita 1:N archivos, mensajes (asociación
opcional), notificaciones y bitácora; Cita 1:0..1 RegistroCobro; RegistroCobro
1:N Pago; Persona 1:N HistorialAcceso, Notificacion, BitacoraCita y CierreCaja.
En `documentacion/MODELO_RELACIONAL_AJUSTADO.md` está la tabla campo a campo.

## URLs por rol

- Visitante: `/`, `/servicios/`, `/agenda/reservar/` (consulta pública de disponibilidad).
- Registro de cliente: `/usuarios/registro/` (sin verificación).
- Inicio de sesión: `/usuarios/login/` (selección de rol) y
  `/usuarios/estilista/login/`, `/usuarios/administrador/login/`.
- Cliente: `/agenda/inicio/`, `/agenda/mis-citas/`, `/agenda/mensajes/`,
  `/agenda/notificaciones/` y `/usuarios/perfil/`.
- Estilista: `/agenda/estilista/` y sus menús de solicitudes/calendario.
- Administrador: `/administracion/` (usuarios, servicios, citas, reportes,
  pagos, cierres y respaldos). Django admin: `/admin/`.
- Recuperar contraseña: `/usuarios/recuperar-clave/` (no es verificación de cuenta).

## Pruebas

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Las nuevas pruebas de registro inmediato y relaciones están en
`App_usuarios/tests_modelo_relacional.py` y `App_agenda/tests_modelo_relacional.py`.
Para ejecutarlas junto con las originales:

```bash
python manage.py test App_usuarios App_servicios App_agenda App_facturacion App_administracion
```

**Validación de esta entrega:** se verificó la sintaxis Python y los enlaces
estructurales mediante análisis estático. No fue posible ejecutar Django ni las
pruebas dentro del entorno de generación porque no están instaladas sus
dependencias y la conexión a PyPI estaba bloqueada. Ejecútalas en tu equipo
antes de dar por verificados los flujos; las 107 pruebas que menciona el
proyecto original pertenecen a la versión previa, **no** son un resultado
confirmado de esta revisión.

## Alcance y límites verificables

Se preservaron las vistas, formularios, 16 modelos y flujos existentes (reservas,
cancelaciones, reprogramaciones, recordatorios internos, chat, adjuntos,
bitácora, cobros/abonos, PDF/Excel y respaldo local). Los módulos de
**notificaciones en vivo por WebSocket, SMTP real, sincronización automática
con nube, infraestructura desplegada y prueba de accesibilidad exhaustiva**
no están entregados como servicios operativos. La matriz original en
`documentacion/MATRIZ_ESTADOS_RF.csv` es una evaluación de la versión previa:
sus estados no deben considerarse una certificación de la versión reconstruida.

## Seguridad y datos

Contraseñas con hash Django; validación de rol por servidor; formularios CSRF,
consultas y archivos por autorización; conexión cifrada y gestión de secretos
en producción. Se distribuye **sin datos personales ni base de datos real**.
Para migrar una instalación real, realiza un respaldo privado previo;
no sobrescribas la base actual con una base vacía.
