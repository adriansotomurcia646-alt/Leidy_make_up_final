"""Pruebas unitarias offline para Gmail API y Supabase Storage sin credenciales."""
from unittest.mock import Mock, patch
from django.core.mail import EmailMessage
from django.test import SimpleTestCase, override_settings
from Pr_makeupweb.gmail_backend import GmailAPIBackend
from Pr_makeupweb.supabase_storage import SupabaseStorage

class GmailAPITests(SimpleTestCase):
    @override_settings(GMAIL_CLIENT_ID='id', GMAIL_CLIENT_SECRET='secret',
                       GMAIL_REFRESH_TOKEN='token', GMAIL_SENDER_EMAIL='sender@gmail.com')
    @patch('Pr_makeupweb.gmail_backend.requests.post')
    @patch.object(GmailAPIBackend, '_credentials')
    def test_envia_codigo_por_https(self, cred, post):
        cred.return_value = Mock(token='access-token')
        post.return_value.json.return_value = {'id':'abc123'}
        post.return_value.raise_for_status.return_value = None
        msg = EmailMessage('Código Leidy', 'El código es 123456',
                           'sender@gmail.com', ['clienta@gmail.com'])
        self.assertEqual(GmailAPIBackend().send_messages([msg]), 1)
        args, kwargs = post.call_args
        self.assertTrue(args[0].startswith('https://gmail.googleapis.com/'))
        self.assertEqual(kwargs['headers']['Authorization'], 'Bearer access-token')
        self.assertIn('raw', kwargs['json'])

    @patch.object(GmailAPIBackend, '_credentials')
    @patch('Pr_makeupweb.gmail_backend.requests.post')
    def test_error_no_confirma_envio(self, post, cred):
        cred.return_value = Mock(token='token')
        post.return_value.json.return_value = {}
        msg = EmailMessage('Código', '123456', 'sender@gmail.com', ['c@gmail.com'])
        with self.assertRaises(RuntimeError):
            GmailAPIBackend().send_messages([msg])

class StorageAPITests(SimpleTestCase):
    @override_settings(SUPABASE_URL='https://proyecto.supabase.co',
                       SUPABASE_SECRET_KEY='supersecret',
                       SUPABASE_PUBLIC_BUCKET='leidy-publico', SUPABASE_PRIVATE_BUCKET='leidy-privado')
    @patch('Pr_makeupweb.supabase_storage.requests.post')
    @patch('Pr_makeupweb.supabase_storage.requests.head')
    def test_subida_publica_y_url(self, head, post):
        head.return_value.status_code = 404
        post.return_value.status_code = 200
        s = SupabaseStorage(public=True)
        from django.core.files.base import ContentFile
        name = s.save('carrusel/demo.jpg', ContentFile(b'jpg'))
        self.assertEqual(name, 'carrusel/demo.jpg')
        self.assertIn('/object/public/leidy-publico/', s.url(name))
        self.assertNotIn('supersecret', s.url(name))

    @override_settings(SUPABASE_URL='https://proyecto.supabase.co',
                       SUPABASE_SECRET_KEY='secreto',
                       SUPABASE_PUBLIC_BUCKET='leidy-publico', SUPABASE_PRIVATE_BUCKET='leidy-privado')
    def test_citas_privadas_sin_url(self):
        with self.assertRaises(ValueError):
            SupabaseStorage(public=False).url('citas/doc.jpg')
