"""Obtiene localmente y sin contraseña de Gmail un refresh token OAuth.

1. Crear proyecto Google Cloud y habilitar Gmail API.
2. OAuth consentimiento External; usuario de prueba solo correo emisor.
3. Crear OAuth Client ID de tipo Desktop y poner ID/secret en .env local.
4. python manage.py configurar_gmail_api
5. Copiar solo las variables OAuth a Render Environment (nunca al código).
"""
import os
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import set_key
from Pr_makeupweb.gmail_backend import GMAIL_SCOPE

class Command(BaseCommand):
    help = 'Autoriza de forma local la cuenta remitente con OAuth 2.0 Gmail API'

    def add_arguments(self, parser):
        parser.add_argument('--sin-navegador', action='store_true', help='Imprime la URL de autorización')

    def handle(self, *args, **options):
        client_id = os.environ.get('GMAIL_CLIENT_ID', '')
        client_secret = os.environ.get('GMAIL_CLIENT_SECRET', '')
        if not client_id or not client_secret:
            raise CommandError('Configura GMAIL_CLIENT_ID y GMAIL_CLIENT_SECRET en .env local antes de continuar.')
        config = {'installed': {
            'client_id': client_id,
            'client_secret': client_secret,
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'redirect_uris': ['http://localhost'],
        }}
        flow = InstalledAppFlow.from_client_config(config, scopes=[GMAIL_SCOPE])
        self.stdout.write('Se abrirá Google para autorizar SOLO enviar correos; usa el Gmail emisor.')
        self.stdout.write('No compartas el resultado con nadie y nunca lo subas a GitHub.')
        try:
            creds = flow.run_local_server(
                host='localhost', port=0,
                open_browser=not options['sin_navegador'],
                authorization_prompt_message='Abre esta URL en tu navegador:\n{url}\n',
                success_message='Leidy Make Up autorizado. Ya puedes cerrar esta pestaña.',
                access_type='offline', prompt='consent',
            )
        except Exception as e:
            raise CommandError(f'No se pudo completar OAuth: {type(e).__name__}. Verifica cliente Desktop y usuario de prueba.') from e
        if not creds.refresh_token:
            raise CommandError('Google no devolvió refresh token; revoca el acceso anterior y repite.')
        env_path = settings.BASE_DIR / '.env'
        try:
            set_key(env_path, 'GMAIL_REFRESH_TOKEN', creds.refresh_token, quote_mode='always')
            os.chmod(env_path, 0o600)
        except OSError:
            raise CommandError('OAuth se completó, pero no se pudo guardar el token en .env. Revisa permisos.') from None
        self.stdout.write(self.style.SUCCESS('Autorización completada. Refresh token guardado en .env con permisos privados.'))
        self.stdout.write('Configura GMAIL_REFRESH_TOKEN también en Render Environment sin publicarlo.')
        self.stdout.write('OJO: en OAuth modo Testing, este refresh token puede caducar a los 7 días.')
