import base64
import os
import re
import stat
import tempfile
import time
from email import message_from_bytes
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests
from django.conf import settings
from django.core import mail
from django.core.mail import EmailMessage, get_connection
from django.core.mail import InvalidMailer
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.core.cache import cache
from django.urls import reverse

from App_usuarios.models import Cliente
from Pr_makeupweb.gmail_backend import GmailAPIBackend, GmailAPIError, GMAIL_API_ENDPOINT


class GmailAPIBackendTests(TestCase):
    def setUp(self):
        self.backend = GmailAPIBackend(alias='default')
        self.message = EmailMessage(
            'Asunto de prueba', 'Contenido de prueba',
            'Leidy Make Up <sender@example.com>', ['client@example.com'],
        )

    def _successful_response(self):
        response = Mock()
        response.json.return_value = {'id': 'mock-message-id'}
        return response

    @override_settings(MAILERS={'default': {'BACKEND': 'Pr_makeupweb.gmail_backend.GmailAPIBackend'}})
    def test_default_mailer_uses_gmail_backend_and_django6_arguments(self):
        connection = get_connection()

        self.assertIsInstance(connection, GmailAPIBackend)
        self.assertEqual(connection.alias, 'default')
        self.assertFalse(connection.fail_silently)
        self.assertNotIn('OPTIONS', settings.MAILERS['default'])

    def test_unknown_mailer_options_are_not_silently_discarded(self):
        with self.assertRaises(InvalidMailer):
            GmailAPIBackend(alias='default', unsupported_option=True)

    def test_posts_encoded_message_to_gmail_api(self):
        response = self._successful_response()
        with (
            patch.object(GmailAPIBackend, '_credentials', return_value=SimpleNamespace(token='mock-access-token')),
            patch('Pr_makeupweb.gmail_backend.requests.post', return_value=response) as post,
        ):
            sent = self.backend.send_messages([self.message])

        self.assertEqual(sent, 1)
        args, kwargs = post.call_args
        self.assertEqual(args[0], GMAIL_API_ENDPOINT)
        self.assertEqual(kwargs['headers']['Authorization'], 'Bearer mock-access-token')
        self.assertEqual(kwargs['timeout'], (10, 20))
        raw = kwargs['json']['raw']
        decoded = base64.urlsafe_b64decode(raw + '=' * (-len(raw) % 4))
        self.assertIn(b'Contenido de prueba', decoded)

    def test_http_failure_raises_safe_error(self):
        response = self._successful_response()
        response.raise_for_status.side_effect = requests.HTTPError('private-test-detail')
        with (
            patch.object(GmailAPIBackend, '_credentials', return_value=SimpleNamespace(token='mock-access-token')),
            patch('Pr_makeupweb.gmail_backend.requests.post', return_value=response),
            patch('Pr_makeupweb.gmail_backend.logger.error') as log_error,
        ):
            with self.assertRaises(GmailAPIError) as raised:
                self.backend.send_messages([self.message])

        self.assertNotIn('private-test-detail', str(raised.exception))
        self.assertNotIn('private-test-detail', str(log_error.call_args))

    @override_settings(GMAIL_CLIENT_ID='', GMAIL_CLIENT_SECRET='', GMAIL_REFRESH_TOKEN='')
    def test_missing_oauth_credentials_do_not_make_http_request(self):
        with patch('Pr_makeupweb.gmail_backend.requests.post') as post:
            with self.assertRaises(GmailAPIError):
                self.backend.send_messages([self.message])
        post.assert_not_called()

    @override_settings(GMAIL_CLIENT_ID='', GMAIL_CLIENT_SECRET='', GMAIL_REFRESH_TOKEN='')
    def test_fail_silently_returns_zero_when_credentials_are_missing(self):
        backend = GmailAPIBackend(fail_silently=True, alias='default')
        self.assertEqual(backend.send_messages([self.message]), 0)


@override_settings(
    MAILERS={'default': {'BACKEND': 'Pr_makeupweb.gmail_backend.GmailAPIBackend'}},
    GMAIL_CLIENT_ID='mock-client-id',
    GMAIL_CLIENT_SECRET='mock-client-secret',
    GMAIL_REFRESH_TOKEN='mock-refresh-token',
)
class GmailVerificationFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        mail.outbox.clear()
        self.registration = {
            'nombre': 'Sara', 'apellido': 'Morales',
            'email': 'sara@example.com', 'telefono': '3111111111',
            'password': 'ClaveSegura!2026Abc',
        }

    def test_registration_code_is_sent_via_mocked_gmail_api_and_verifies_client(self):
        response = Mock()
        response.json.return_value = {'id': 'mock-message-id'}
        with (
            patch.object(GmailAPIBackend, '_credentials', return_value=SimpleNamespace(token='mock-access-token')),
            patch('Pr_makeupweb.gmail_backend.requests.post', return_value=response) as post,
        ):
            registration_response = self.client.post(
                reverse('App_usuarios:registro'), self.registration,
            )

        self.assertRedirects(registration_response, reverse('App_usuarios:confirmar_registro'))
        post.assert_called_once()
        raw = post.call_args.kwargs['json']['raw']
        decoded = base64.urlsafe_b64decode(raw + '=' * (-len(raw) % 4))
        message = message_from_bytes(decoded)
        payload = message.get_payload(decode=True).decode(message.get_content_charset() or 'utf-8')
        code = re.search(r'\b(\d{6})\b', payload).group(1)

        confirmation_response = self.client.post(
            reverse('App_usuarios:confirmar_registro'), {'codigo': code},
        )

        self.assertRedirects(confirmation_response, reverse('App_usuarios:login'))
        self.assertTrue(Cliente.objects.filter(persona__email='sara@example.com').exists())

    def test_expired_code_cannot_create_account(self):
        response = Mock()
        response.json.return_value = {'id': 'mock-message-id'}
        with (
            patch.object(GmailAPIBackend, '_credentials', return_value=SimpleNamespace(token='mock-access-token')),
            patch('Pr_makeupweb.gmail_backend.requests.post', return_value=response),
        ):
            self.client.post(reverse('App_usuarios:registro'), self.registration)

        pending = self.client.session['registro_cliente_pendiente']
        pending['vence_en'] = time.time() - 1
        session = self.client.session
        session['registro_cliente_pendiente'] = pending
        session.save()
        confirmation = self.client.post(
            reverse('App_usuarios:confirmar_registro'), {'codigo': '123456'},
        )

        self.assertEqual(confirmation.status_code, 200)
        self.assertContains(confirmation, 'El código venció.')
        self.assertFalse(Cliente.objects.filter(persona__email='sara@example.com').exists())

    def test_resend_invalidates_old_code_and_sends_a_new_one(self):
        response = Mock()
        response.json.return_value = {'id': 'mock-message-id'}
        with (
            patch.object(GmailAPIBackend, '_credentials', return_value=SimpleNamespace(token='mock-access-token')),
            patch('Pr_makeupweb.gmail_backend.requests.post', return_value=response) as post,
        ):
            self.client.post(reverse('App_usuarios:registro'), self.registration)
            pending = self.client.session['registro_cliente_pendiente']
            old_raw = post.call_args.kwargs['json']['raw']
            old_payload = base64.urlsafe_b64decode(old_raw + '=' * (-len(old_raw) % 4))
            old_message = message_from_bytes(old_payload)
            old_body = old_message.get_payload(decode=True).decode(old_message.get_content_charset() or 'utf-8')
            old_code = re.search(r'\b(\d{6})\b', old_body).group(1)

            pending['enviado_en'] = time.time() - 61
            session = self.client.session
            session['registro_cliente_pendiente'] = pending
            session.save()
            cache.clear()
            response_view = self.client.post(reverse('App_usuarios:reenviar_codigo_registro'))

        self.assertRedirects(response_view, reverse('App_usuarios:confirmar_registro'))
        self.assertEqual(post.call_count, 2)
        new_raw = post.call_args.kwargs['json']['raw']
        new_payload = base64.urlsafe_b64decode(new_raw + '=' * (-len(new_raw) % 4))
        new_message = message_from_bytes(new_payload)
        new_body = new_message.get_payload(decode=True).decode(new_message.get_content_charset() or 'utf-8')
        new_code = re.search(r'\b(\d{6})\b', new_body).group(1)
        self.assertNotEqual(old_code, new_code)
        self.assertEqual(self.client.session['registro_cliente_pendiente']['envios'], 2)

        old_confirmation = self.client.post(
            reverse('App_usuarios:confirmar_registro'), {'codigo': old_code},
        )
        self.assertEqual(old_confirmation.status_code, 200)
        self.assertFalse(Cliente.objects.filter(persona__email='sara@example.com').exists())
        new_confirmation = self.client.post(
            reverse('App_usuarios:confirmar_registro'), {'codigo': new_code},
        )
        self.assertRedirects(new_confirmation, reverse('App_usuarios:login'))
        self.assertTrue(Cliente.objects.filter(persona__email='sara@example.com').exists())

    def test_gmail_http_error_is_reported_without_creating_pending_registration(self):
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError('private-test-detail')
        with (
            patch.object(GmailAPIBackend, '_credentials', return_value=SimpleNamespace(token='mock-access-token')),
            patch('Pr_makeupweb.gmail_backend.requests.post', return_value=response),
        ):
            with self.assertLogs('App_usuarios.views', level='ERROR') as error_logs:
                registration = self.client.post(reverse('App_usuarios:registro'), self.registration)

        self.assertEqual(registration.status_code, 200)
        self.assertContains(registration, 'No fue posible enviar el código.')
        self.assertNotIn('registro_cliente_pendiente', self.client.session)
        self.assertFalse(Cliente.objects.filter(persona__email='sara@example.com').exists())
        self.assertNotIn('private-test-detail', '\n'.join(error_logs.output))


class ConfigureGmailAPICommandTests(TestCase):
    def test_refresh_token_is_saved_with_private_permissions_and_not_printed(self):
        mock_credentials = SimpleNamespace(refresh_token='mock-refresh-token')
        with tempfile.TemporaryDirectory() as directory:
            with (
                override_settings(BASE_DIR=Path(directory)),
                patch.dict(os.environ, {'GMAIL_CLIENT_ID': 'mock-client-id', 'GMAIL_CLIENT_SECRET': 'mock-client-secret'}),
                patch('App_usuarios.management.commands.configurar_gmail_api.InstalledAppFlow.from_client_config') as from_config,
            ):
                from_config.return_value.run_local_server.return_value = mock_credentials
                output = __import__('io').StringIO()
                call_command('configurar_gmail_api', sin_navegador=True, stdout=output)

            env_path = Path(directory) / '.env'
            self.assertIn("GMAIL_REFRESH_TOKEN='mock-refresh-token'", env_path.read_text())
            self.assertEqual(stat.S_IMODE(env_path.stat().st_mode), 0o600)
            self.assertNotIn('mock-refresh-token', output.getvalue())
