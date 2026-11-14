# Novedad Maison 3.1: carrusel fotográfico desde Administrador

Ahora puedes sustituir la ilustración de mujer de la portada y el inicio de sesión. Entra con tu cuenta de **Administrador** a `/administracion/portada/` (menú **Fotos de portada**), sube varias fotografías JPG/PNG/WebP, selecciona **Portada** y/o **Acceso**, ordena o elimina. El carrusel cambia cada **5,8 segundos** con un desvanecimiento de **1,25 segundos**. Si no hay fotos se conserva la ilustración actual.

**Para actualizar una base existente** ejecuta `python manage.py migrate` después de hacer copia de seguridad. Ver `documentacion/MAISON_3_1_CARRUSEL_ADMIN.md`.

---

# Leidy Make Up — MAISON 3.0 (edición de diseño)

**Nueva versión visual del proyecto Django completo**, basada en Atelier 2.0. Conserva los modelos, las migraciones, las rutas y los formularios de negocio anteriores: registro por código enviado a Gmail, cuatro roles (visitante, cliente, estilista y administrador), agenda, facturación y galería de múltiples fotografías por servicio.

## Novedades visuales

- Identidad MAISON: cacao profundo, crema, cobre y terracota; tipografías Cormorant Garamond y Manrope con fuentes de respaldo.
- Portada diseñada de nuevo: composición editorial, ilustración SVG original de respaldo que no depende de imágenes externas, catálogo dinámico, narrativa del estudio, proceso de reserva y llamados a la acción.
- Inicio de sesión en dos columnas, con selector funcional de rol y presentación adaptable en móviles.
- Catálogo y detalle del servicio con paleta unificada, tarjetas y galerías; las fotografías que publique la estilista tienen prioridad sobre la ilustración de respaldo.
- Paneles de cliente, estilista y administrador con colores, bordes, encabezados y métricas cohesionados.
- Mejor presentación de la carga múltiple de fotografías, previsualización local y nombre de cada archivo.
- Todas las mejoras de la nueva edición están separadas en `static/css/maison.css`, `static/js/maison.js` y `static/img/beauty-illustration.svg`.

## Inicio rápido (Linux)

```bash
bash iniciar_linux.sh
```

Abre `http://127.0.0.1:8000/`. En la terminal, dentro de la carpeta con `manage.py`, crea tu superusuario con `python manage.py createsuperuser`. Para crear la cuenta de estilista, entra a `/admin/`, crea la **Persona** con rol `Estilista` y su perfil **Estilista** correspondiente.

Para cambiar contraseña: `python manage.py changepassword NOMBRE_DE_USUARIO`.

**Gmail real:** configurar en `.env` las variables `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` con una **contraseña de aplicación**, y el resto según `.env.example`. El correo en modo consola imprime el código en el terminal; no envía Gmail hasta configurar SMTP. Nunca subas `.env` o contraseñas a un repositorio.

**Render:** la configuración previa sigue disponible. Debes configurar PostgreSQL, una cuenta de correo SMTP y almacenamiento persistente (por ejemplo, R2/S3) antes de usar el proyecto en producción; el almacenamiento temporal de Render no conserva permanentemente las fotos.

**Pruebas:** ejecuta `python manage.py check`, `python manage.py makemigrations --check --dry-run`, `python manage.py migrate` y `python manage.py test App_usuarios App_servicios App_agenda App_facturacion App_administracion`. La capa Maison cambia sobre todo plantillas y CSS; no constituye una garantía de que las pruebas del proyecto heredado estén resueltas.

---

# Leidy Make Up — Galería fotográfica + verificación de correo

Proyecto académico SENA / ADSO. Reconstrucción del código Django original con los cuatro roles **Visitante, Cliente, Estilista y Administrador**, agenda de citas, servicios, cobros, reportes y gestión de usuarios. Esta es una evolución de la versión de **53 requisitos funcionales**; los documentos históricos se conservan en `documentacion/` y no se presentan como pruebas de esta nueva entrega.

## Qué se agregó

1. **Registro mediante código al correo:** un nuevo cliente rellena nombre, apellido, celular, correo y contraseña, recibe un código de 6 dígitos y solo se crea la cuenta `Persona/Cliente` al introducir correctamente el código. Código vigente 10 minutos, 5 intentos, 3 envíos (contando el primero), reenvío mínimo cada 60 segundos, y sesión de registro hasta 30 minutos. Contraseñas y códigos pendientes se guardan con hash. El código anterior queda invalidado al reenviar. El cambio de correo en Perfil también pide un código al nuevo correo. El inicio de sesión existente sigue funcionando por contraseña y rol.
2. **Galería de varias fotos por servicio:** nueva entidad `ImagenServicio`, hasta 12 imágenes JPG/PNG/WebP de hasta 5 MiB/24 MP cada una, portada editable, carga múltiple desde panel de la estilista y la administración, eliminación individual de imágenes, catálogo y vista de detalle públicos con galería de miniaturas. Los servicios desactivados no se muestran al público.
3. **Diseño premium responsivo:** nueva portada, catálogo de tarjetas con fotos, ficha de servicio, gestión de estilista y edición de servicios, con estilos refinados en `static/css/atelier.css` y mejora global de paneles de roles.
4. **Preparación para despliegue:** SMTP Gmail, PostgreSQL, HTTPS/Render, WhiteNoise, almacenamiento persistente de fotos en S3/R2, Redis opcional para límites de envío, y variables de entorno, sin credenciales precargadas.

## 1. Abrir en tu Linux (Fedora/Nobara/Ubuntu)

Abre terminal en la carpeta del proyecto, donde está `manage.py`, y ejecuta:

```bash
bash iniciar_linux.sh
```

Esto crea `.venv`, instala dependencias, crea una `.env` con clave aleatoria si no existe, aplica migraciones y abre el servidor. Abre **http://127.0.0.1:8000/**.

Alternativa manual:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edita .env: asigna DJANGO_SECRET_KEY aleatoria y DJANGO_DEBUG=True
python manage.py migrate
python manage.py check
python manage.py runserver
```

Generar clave aleatoria (requiere instalar dependencias):

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Crea administrador con `python manage.py createsuperuser` y desde `/admin/` o `/administracion/` registra la estilista, servicios y sus horarios. Sin horarios configurados no habrá citas disponibles.

## 2. Activar códigos reales por Gmail

En el archivo `.env`, añade o cambia estas variables (usando **tus propias credenciales**, no las de prueba):

```dotenv
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-cuenta@gmail.com
EMAIL_HOST_PASSWORD=CONTRASENA_DE_APLICACION_DE_GOOGLE
DEFAULT_FROM_EMAIL=tu-cuenta@gmail.com
```

Activa la verificación en dos pasos de la cuenta emisora de Google y genera una **contraseña de aplicación**, si Google ofrece esa opción para tu cuenta. **Nunca** pongas tu contraseña principal. En desarrollo puedes mantener `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend`: el código aparecerá en la terminal, y podrás probar registro sin enviar mensajes reales. No subas `.env` a GitHub.

Recorrido de prueba: `http://127.0.0.1:8000/usuarios/registro/` → introducir datos → revisar buzón o terminal → `.../usuarios/registro/confirmar/` → escribir código → iniciar sesión. Cambiar email desde `/usuarios/perfil/` también requiere confirmación.

## 3. Subir fotos de servicios (estilista)

Entrar con una cuenta de rol **Estilista** → `/servicios/` → **Agregar servicio** o **Editar y cargar fotos**. Selecciona una o varias imágenes, guarda, marca la portada deseada o elimina una imagen individual. Una clienta o visitante puede navegar por `/servicios/`, abrir un servicio y recorrer sus fotografías. Los administradores pueden cargar imágenes desde `/administracion/servicios/` y desde el admin de Django.

**Nota de seguridad:** las fotos de servicios son **públicas**; únicamente esas fotos se sirven en local bajo `/media/servicios_publicos/`. Los archivos personales subidos a citas siguen privados y no se exponen por `/media/`.

## 4. Hospedar en Render

1. Subir la carpeta del proyecto a un repositorio propio, sin `.env`, `.venv`, `db.sqlite3`, `media/` ni datos personales.
2. Usar `render.yaml` como guía de Web Service y PostgreSQL (o configurar manualmente). Instalar `requirements-postgresql.txt`, recolectar estáticos y arrancar Gunicorn.
3. Añadir secretos privados en Render: `DJANGO_SECRET_KEY`, `DATABASE_URL`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DJANGO_DEBUG=False`, `DJANGO_SSL_REDIRECT=True`, `DJANGO_TRUST_PROXY_SSL=True`, `DJANGO_ENABLE_WHITENOISE=True`, y credenciales Gmail SMTP (`EMAIL_*`).
4. **Obligatorio para fotos persistentes:** configurar S3 o Cloudflare R2 para `SERVICE_IMAGES_BUCKET`, `SERVICE_IMAGES_ENDPOINT_URL` (R2), `SERVICE_IMAGES_PUBLIC_DOMAIN` (dominio público), `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` y, si aplica, `SERVICE_IMAGES_REGION`. La galería **no debe guardarse solamente en el disco temporal de Render**; se perdería al reiniciar o redesplegar. No utilices el bucket público para fotos privadas de las citas.
5. Se recomienda Redis (`REDIS_URL`) para compartir el límite de solicitudes de códigos entre múltiples workers. Configura el envío SMTP de Gmail/Google Workspace respetando sus límites. Antes de abrir a usuarios reales, ejecuta pruebas, revisa seguridad, accesibilidad y copia de seguridad de la BD.

**Para una instalación ya existente**, haz copia de seguridad privada de la base de datos y las fotos antes de ejecutar migraciones. La migración de la galería es `App_servicios/migrations/0003_imagenservicio.py`. No reemplaces tu base de datos con una vacía.

## 5. Pruebas en el ordenador

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test App_usuarios App_servicios App_agenda App_facturacion App_administracion
python manage.py collectstatic --noinput
```

Las pruebas añadidas de verificación de código y de galería están en `App_usuarios/tests.py` y `App_servicios/tests_galeria.py`. **Limitación del entorno de creación:** se comprobó la sintaxis Python y el contenido del ZIP de manera estática, pero no fue posible instalar Django desde PyPI para ejecutar las pruebas de integración aquí. Esto **no es una certificación de que todas las funcionalidades pasen los tests**; valídalo ejecutando los comandos anteriores en tu Linux.

## 6. Componentes y modelo de datos

| App | Responsabilidad principal |
|---|---|
| `App_usuarios` | Personas, clientes, estilistas, roles, acceso, registro por código y perfil |
| `App_servicios` | Servicios y **ImagenServicio** (nueva relación `Servicio 1:N ImagenServicio`) |
| `App_agenda` | Disponibilidad, reservas, estados «En espera»/confirmación, adjuntos y mensajes |
| `App_facturacion` | Pagos, cobros y cierre de caja |
| `App_administracion` | Panel de administración, reportes y catálogos |
| `App_inicio` | Entrada al portal |

La documentación de requisitos del proyecto original describe 16 entidades; ahora la galería añade una entidad adicional (**17 en total**). La documentación histórica de 53 RF y el diagrama anterior **necesitan actualización formal** si se usarán como anexos finales.

## Aclaración de autenticación

El código Gmail valida el **registro** y el **cambio de correo**, pero **no activa un segundo factor en cada inicio de sesión**. Los inicios de sesión siguen usando las credenciales Django y la verificación del rol en el servidor. No se implementó login por Google OAuth ni un servicio externo de identidad.


## Diseño Atelier 2.0 (actualización visual)

La edición visual conserva la lógica de citas, cuentas, códigos de verificación, roles y fotografías.

- **Portada editorial:** identidad ciruela/marfil/rosa, hero adaptable y secciones de servicios y pasos de reserva.
- **Galería:** miniaturas seleccionables, ampliación en ventana accesible y fotos reales cargadas por estilista.
- **Paneles:** estilo unificado para cliente, estilista y administración; menú compacto en móviles.
- **Autenticación:** acceso, registro y confirmación por código con un estilo coherente.
- **Archivos:** `static/css/refinement.css` contiene la capa visual; `static/js/atelier-ui.js` contiene menús y galería.

El diseño no incorpora fotografías de muestra ficticias. Hasta que la estilista publique sus imágenes, se muestran composiciones decorativas. Se recomienda subir fotografías reales para lograr una presentación completa.

> Si el navegador conserva la hoja de estilos anterior, actualiza la página forzando recarga (Ctrl+F5).
