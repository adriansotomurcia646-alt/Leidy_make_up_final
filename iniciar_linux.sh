#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo "Instala Python 3.12 o superior."; exit 1; }
if [[ ! -d .venv ]]; then python3 -m venv .venv; fi
source .venv/bin/activate
python -m pip install -r requirements-postgresql.txt
if [[ ! -f .env ]]; then
  python - <<'PYSECRET'
from pathlib import Path
import secrets
Path('.env').write_text('DJANGO_DEBUG=True\nDJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,testserver\nDJANGO_SECRET_KEY='+secrets.token_urlsafe(64)+'\n', encoding='utf-8')
print('Clave local segura generada en .env (no compartir).')
PYSECRET
fi
python manage.py migrate
python manage.py check
printf '\nAbre http://127.0.0.1:8000/\n'
python manage.py runserver
