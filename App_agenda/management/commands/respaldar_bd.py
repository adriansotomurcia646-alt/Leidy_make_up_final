"""Copia consistente de SQLite, únicamente desarrollo/local."""
import sqlite3
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Crea un respaldo SQLite consistente en backups/ (nunca lo subas a Git).'

    def handle(self, *args, **opts):
        db = settings.DATABASES['default']
        if db['ENGINE'] != 'django.db.backends.sqlite3':
            raise CommandError('Para PostgreSQL use pg_dump con las credenciales de despliegue.')
        ruta = Path(db['NAME'])
        if not ruta.exists():
            raise CommandError('La base de datos aún no existe.')
        carpeta = Path(settings.BASE_DIR) / 'backups'
        carpeta.mkdir(exist_ok=True)
        destino = carpeta / ('leidy-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.sqlite3')
        with sqlite3.connect(str(ruta)) as fuente, sqlite3.connect(str(destino)) as salida:
            fuente.backup(salida)
        self.stdout.write(self.style.SUCCESS(f'Respaldo creado: {destino}'))
