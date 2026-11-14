"""Backend Django que envía mensajes por Gmail API HTTPS, compatible con Render Free.

Usa una única cuenta de correo emisora autorizada por su propietario.
Nunca entrega a los clientes permisos OAuth ni secretos del servidor.
"""
import base64
import logging

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.exceptions import ImproperlyConfigured
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)
GMAIL_SCOPE = 'https://www.googleapis.com/auth/gmail.send'
GMAIL_API_ENDPOINT = 'https://gmail.googleapis.com/gmail/v1/users/me/messages/send'


class GmailAPIError(Exception):
    """Error de envío sin incluir respuestas HTTP ni credenciales privadas."""


class GmailAPIBackend(BaseEmailBackend):
    """Se integra sin tocar send_mail(), EmailMessage ni los flujos existentes."""

    def __init__(self, fail_silently=False, *, alias=None, **kwargs):
        self.fail_silently = fail_silently
        super().__init__(alias=alias, **kwargs)
        self._creds = None

    def _credentials(self):
        if self._creds is None:
            if not all((settings.GMAIL_CLIENT_ID, settings.GMAIL_CLIENT_SECRET, settings.GMAIL_REFRESH_TOKEN)):
                raise ImproperlyConfigured('Faltan credenciales OAuth para Gmail API.')
            self._creds = Credentials(
                token=None,
                refresh_token=settings.GMAIL_REFRESH_TOKEN,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=settings.GMAIL_CLIENT_ID,
                client_secret=settings.GMAIL_CLIENT_SECRET,
                scopes=[GMAIL_SCOPE],
            )
        if not self._creds.valid:
            self._creds.refresh(GoogleAuthRequest())
        return self._creds

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        enviados = 0
        for mensaje in email_messages:
            try:
                if not mensaje.recipients():
                    continue
                creds = self._credentials()
                raw = base64.urlsafe_b64encode(mensaje.message().as_bytes()).decode('ascii').rstrip('=')
                respuesta = requests.post(
                    GMAIL_API_ENDPOINT,
                    json={'raw': raw},
                    headers={'Authorization': f'Bearer {creds.token}'},
                    timeout=(10, 20),
                )
                respuesta.raise_for_status()
                if not respuesta.json().get('id'):
                    raise RuntimeError('Gmail API no confirmó un identificador de mensaje')
                enviados += 1
            except Exception as error:
                logger.error('Gmail API no pudo enviar un mensaje (%s).', type(error).__name__)
                if not self.fail_silently:
                    raise GmailAPIError('No se pudo enviar el correo mediante Gmail API.') from None
        return enviados
