"""Almacenamiento de archivos para Supabase Storage (HTTPS).

Public: imágenes de servicios y carrusel con un bucket PÚBLICO.
Private: referencias de citas con un bucket PRIVADO, solo descarga autenticada.
El secreto service_role se usa exclusivamente en servidor, jamás en JavaScript.
"""
from urllib.parse import quote

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.core.exceptions import SuspiciousFileOperation
from django.utils.deconstruct import deconstructible


@deconstructible
class SupabaseStorage(Storage):
    def __init__(self, bucket=None, public=False):
        self.bucket = bucket or (settings.SUPABASE_PUBLIC_BUCKET if public else settings.SUPABASE_PRIVATE_BUCKET)
        self.public = public
        self.api_base = settings.SUPABASE_URL.rstrip('/') + '/storage/v1'
        self.key = settings.SUPABASE_SECRET_KEY
        self.timeout = (10, 30)

    def _path(self, name):
        name = str(name).replace('\\', '/')
        partes = name.split('/')
        if not name or name.startswith('/') or any(p in ('..', '.', '') for p in partes):
            raise SuspiciousFileOperation('Ruta de archivo inválida')
        return quote(name, safe='/')

    def _url_objeto(self, name):
        return f'{self.api_base}/object/{quote(self.bucket, safe="")}/{self._path(name)}'

    def _url_descarga(self, name):
        return f'{self.api_base}/object/authenticated/{quote(self.bucket, safe="")}/{self._path(name)}'

    def _url_info(self, name):
        return f'{self.api_base}/object/info/{quote(self.bucket, safe="")}/{self._path(name)}'

    def _headers(self, mimetype=None):
        # Nuevas claves sb_secret son opacas; NO se pasan como JWT Bearer.
        # Las claves service_role antiguas sí son JWT, por eso se añade Bearer.
        encabezados = {'apikey': self.key}
        if not self.key.startswith('sb_secret_'):
            encabezados['Authorization'] = f'Bearer {self.key}'
        if mimetype:
            encabezados['Content-Type'] = mimetype
            encabezados['x-upsert'] = 'false'
        return encabezados

    def _save(self, name, content):
        import mimetypes
        # Django asigna un nombre UUID a las fotos; esto también aplica a adjuntos.
        name = self.get_available_name(name)
        body = content.read()
        mimetype = getattr(content, 'content_type', None) or mimetypes.guess_type(name)[0] or 'application/octet-stream'
        response = requests.post(self._url_objeto(name), data=body,
                                 headers=self._headers(mimetype), timeout=self.timeout)
        response.raise_for_status()
        return name

    def _open(self, name, mode='rb'):
        if mode not in ('rb', 'r'):
            raise ValueError('Solo lectura')
        response = requests.get(self._url_descarga(name), headers=self._headers(), timeout=self.timeout)
        if response.status_code == 404:
            raise FileNotFoundError(name)
        response.raise_for_status()
        file = ContentFile(response.content, name=name)
        file.seek(0)
        return file

    def exists(self, name):
        response = requests.head(self._url_info(name), headers=self._headers(), timeout=self.timeout)
        if response.status_code == 404:
            return False
        response.raise_for_status()
        return True

    def delete(self, name):
        if not name:
            return
        response = requests.delete(self._url_objeto(name), headers=self._headers(), timeout=self.timeout)
        if response.status_code not in (200, 204, 404):
            response.raise_for_status()

    def url(self, name):
        if not self.public:
            raise ValueError('No existe URL pública para archivos privados de citas')
        return f'{self.api_base}/object/public/{quote(self.bucket, safe="")}/{self._path(name)}'

    def size(self, name):
        response = requests.head(self._url_info(name), headers=self._headers(), timeout=self.timeout)
        response.raise_for_status()
        return int(response.headers.get('content-length', 0))

    def get_modified_time(self, name):
        from django.utils import timezone
        return timezone.now()
