# Leidy Make Up Maison 3.2 — guía para $0

## Qué cambia
- Render Web Service **Free**: Python/Django con subdominio `*.onrender.com`, HTTPS, sin pagar.
- Gmail API HTTPS: el servidor manda códigos desde `make.up.leidy.1986@gmail.com` usando OAuth 2.0, sin SMTP ni contraseñas de aplicación.
- Supabase **Free**: PostgreSQL y **dos buckets** para imágenes (públicas) y adjuntos (privados) que no se pierdan al reiniciar Render.
- Conserva los roles (administrador, estilista, cliente), citas, verificación por código, galería de servicios y carrusel de portada.

## A. Cuenta de Google: generar autorización OAuth
1. Abre https://console.cloud.google.com/ con la cuenta de Gmail emisora. Crea un proyecto, por ejemplo `LeidyMakeUp`.
2. En **APIs y servicios > Biblioteca**, habilita **Gmail API**.
3. Configura **Pantalla de consentimiento OAuth / Google Auth Platform**: audiencia **External**, nombre `Leidy Make Up`. Si te deja en **Testing**, añade `make.up.leidy.1986@gmail.com` como usuario de prueba.
4. Añade **solamente** el permiso `https://www.googleapis.com/auth/gmail.send` (envío; nunca permisos de lectura de bandeja).
5. En **Clientes / Credenciales**, crea un **ID de cliente OAuth de tipo Aplicación de escritorio (Desktop)**. Copia CLIENT_ID y CLIENT_SECRET, sin publicarlos.
6. En tu PC (Linux), crea `.env` copiando `.env.example` y pon `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET` y `DJANGO_SECRET_KEY`.
7. Instala dependencias y ejecuta:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-postgresql.txt
   python manage.py configurar_gmail_api
   ```
   Se abrirá el navegador para AUTORIZAR **tu cuenta remitente** (no la de las clientas). Esta autorización inicial se hace **una sola vez** o al caducar/revocar el token.
8. El comando guarda el refresh token directamente en `.env` con permisos privados (`0600`) y no lo imprime. Configura `GMAIL_REFRESH_TOKEN` en **Render > Environment** usando tu copia local privada. **NUNCA** lo envíes a terceros, GitHub, screenshots ni conversaciones.
9. `Pr_makeupweb.gmail_backend.GmailAPIBackend` es el backend predeterminado. Con OAuth autorizado, puedes ejecutar una prueba real local:
   ```bash
   python manage.py shell -c "from django.core.mail import send_mail; print(send_mail('Prueba Leidy','Prueba Gmail API','make.up.leidy.1986@gmail.com',['TU_OTRO_CORREO@gmail.com']))"
   ```
   Usa una dirección de prueba real y comprueba bandeja y spam. Si muestra `1`, la API aceptó el envío, pero **no garantiza entrega**. Esta prueba contacta Gmail y no forma parte de las pruebas automatizadas.

**Límite importante:** en modo OAuth *Testing* con audiencia *External*, Google caduca los refresh tokens tras **7 días**. Para uso duradero, la publicación OAuth **In production** y/o verificación de Google puede ser necesaria, sobre todo por el scope sensible `gmail.send`. No puedo garantizar que Google la apruebe, ni que no exija verificaciones. Para demostración académica, es posible volver a autorizar localmente cuando haga falta. Solo quien administra Gmail realiza OAuth; las clientas registran su correo normalmente, sin dar permisos Google.

## B. Supabase Free: DB y fotos (sin datos perdidos)
1. Ve a https://supabase.com y crea un proyecto **Free** (no elegir Pro ni pruebas de pago). Guarda la contraseña de base de datos.
2. Supabase > **Database > Connect**: copia la conexión URI de **Session pooler** (compatible IPv4, puerto usual 5432), NO solo el direct host IPv6. Esta URL es `DATABASE_URL` en Render; incluye contraseña, **no compartirla**. Sustituye el marcador de contraseña completo, incluidos sus corchetes de ejemplo. Si la contraseña contiene caracteres reservados, codifica solo la contraseña con `urllib.parse.quote(password, safe='')`; no codifiques la URI completa ni dejes corchetes literales.
3. En Linux, valida el formato localmente sin mostrar la URI: `python scripts/diagnosticar_supabase.py`. Cuando el formato sea válido, prueba la conexión TLS real con `python scripts/diagnosticar_supabase.py --connect`; esta prueba ejecuta únicamente `SELECT 1`.
4. Supabase > **Storage**: crea bucket `leidy-publico`, tipo **Public** (únicamente fotos de servicios y portada). Crea `leidy-privado`, tipo **Private** (adjuntos de citas). NO hagas público el bucket privado.
5. Supabase > **Project Settings > API Keys**: guarda la clave nueva de servidor **Secret key** (`sb_secret_...`, no la *publishable*) como `SUPABASE_SECRET_KEY` solo en Render. Para Storage privado configura también `SUPABASE_SERVICE_ROLE_KEY` con el JWT de servidor legacy: la API key `sb_secret_...` no es un JWT y no debe enviarse como `Authorization: Bearer`; los endpoints privados requieren autorización de servidor. Ambas claves permanecen solo en el backend.
6. Anota la URL del proyecto `https://...supabase.co` como `SUPABASE_URL`.
7. El código usa `supabase_storage.py`: fotos públicas con URLs públicas HTTPS y adjuntos privados sin URL pública y con descarga autorizada desde Django.

Nota: en Supabase Free hay cuotas de base de datos, almacenamiento y egreso; puede pausarse por inactividad. No se cobra mientras sigas en el plan Free dentro de sus condiciones, pero no es SLA ni solución para un negocio con tráfico real.

## C. Publicar en Render Gratis
1. Sube este proyecto a un **repositorio privado de GitHub**, excluyendo `.env`, base de datos y token.
2. Render > **New > Blueprint**: conecta repositorio y usa `render.yaml` (Web Service `plan: free`). **No crear Render PostgreSQL Free**, porque vence a los 30 días.
3. Render solicita los secretos `sync:false`. Completa:
   - `DATABASE_URL`: conexión PostgreSQL **Session pooler** de Supabase.
   - `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`: OAuth propio.
   - `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `SUPABASE_SERVICE_ROLE_KEY`: Supabase; claves solo en el backend.
   - `DJANGO_SECRET_KEY`: Render la genera automáticamente.
   - `SUPABASE_PUBLIC_BUCKET=leidy-publico`, `SUPABASE_PRIVATE_BUCKET=leidy-privado`.
   - `EMAIL_BACKEND=Pr_makeupweb.gmail_backend.GmailAPIBackend`.
   - `GMAIL_SENDER_EMAIL=make.up.leidy.1986@gmail.com`.
   - `DJANGO_CSRF_TRUSTED_ORIGINS=https://*.onrender.com`.
   - `DB_POOLER_MODE=session` para el pooler de sesión de Supabase.
4. Si Render no solicita una variable, añádela a **Web Service > Environment** manualmente y pulsa **Save, deploy**.
5. Abre `https://<tu-subdominio>.onrender.com` y registra una clienta de prueba. Comprueba llegada de código, verificación, login y carga de fotos desde administrador.
6. Para crear el superusuario en Render Free (sin consola Shell de pago), puedes crear la cuenta inicial localmente *apuntando a la misma DATABASE_URL Supabase* con `python manage.py createsuperuser` y luego cerrar esa conexión local. No pongas credenciales de administrador en scripts públicos. Ten mucho cuidado: eso escribe la base remota.

## D. ¿Realmente es $0?
- Render Free: suspensión tras 15 minutos sin visitas, aproximadamente 1 minuto para reactivar, cuotas mensuales; subida de archivos local **no** persiste.
- Supabase Free: 500 MB DB, 1 GB Storage, pausas por inactividad y límites de transferencia.
- Supabase está retirando las claves legacy `service_role` al final de 2026. Revisa su guía de migración de Storage antes de esa fecha; no reemplaces el JWT Bearer por `sb_secret_...` sin validar la compatibilidad del endpoint privado.
- Gmail API: cuotas Google y límites diarios Gmail; no es infraestructura de email transaccional garantizada. El scope `gmail.send` es sensible y pueden exigir verificación para producción.
- El dominio gratuito `onrender.com` es de la web, NO es un dominio de correo propio.
- No te pediré tarjeta ni pagos. **Si un proveedor exige pasar a un plan de pago, detente** antes de aceptar.

## E. Problemas típicos
- `invalid_grant`: token OAuth revocado, caducado o generado en modo Testing hace >7 días; volver a autorizar localmente.
- `redirect_uri_mismatch`: cliente no es de tipo Desktop o callback OAuth erróneo.
- `No fue posible enviar el código`: mira Logs de Render, revisa Gmail API habilitada y que la cuenta remitente haya autorizado el scope.
- `cannot assign requested address`: usaste DB direct IPv6; utiliza Supabase Session pooler IPv4.
- Fotos no aparecen: revisa buckets y las variables `SUPABASE_...`. El bucket público debe ser Public y el privado Private.
- No pegues tokens, passwords, secret keys en chats, capturas, repositorios, ni logs.

## Enlaces oficiales
- https://render.com/docs/free
- https://developers.google.com/workspace/gmail/api/auth/web-server
- https://developers.google.com/identity/protocols/oauth2
- https://developers.google.com/workspace/gmail/api/auth/scopes
- https://supabase.com/pricing
