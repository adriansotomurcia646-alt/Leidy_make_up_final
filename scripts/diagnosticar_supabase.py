#!/usr/bin/env python3
"""Diagnóstico redactado de DATABASE_URL; no conecta salvo con --connect."""
import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from Pr_makeupweb.database_config import diagnose_database_url


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--connect', action='store_true',
        help='Intenta SELECT 1 por TLS después de validar la URI.',
    )
    parser.add_argument('--timeout', type=int, default=8, help='Timeout de conexión en segundos.')
    args = parser.parse_args()

    load_dotenv(ROOT / '.env')
    database_url = os.environ.get('DATABASE_URL')
    status, problem = diagnose_database_url(database_url)
    for key, label in (
        ('present', 'DATABASE_URL presente'),
        ('postgres_scheme', 'Esquema PostgreSQL'),
        ('username_present', 'Usuario presente'),
        ('password_present', 'Contraseña presente'),
        ('host_present', 'Host presente'),
        ('port_valid', 'Puerto válido'),
        ('brackets_in_username', 'Corchetes en usuario'),
        ('brackets_in_password', 'Corchetes en contraseña'),
        ('malformed_percent_escape', 'Escape porcentual malformado'),
    ):
        print(f'{label}: {"sí" if status[key] else "no"}')

    if problem:
        print(f'Diagnóstico: {problem}')
        return 2
    print('Formato: válido; todavía no se ha probado una conexión de red.')

    if args.connect:
        if args.timeout < 1:
            print('Conexión: timeout inválido.')
            return 2
        try:
            import psycopg

            with psycopg.connect(
                database_url,
                connect_timeout=args.timeout,
                sslmode='require',
            ) as connection:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT 1')
                    cursor.fetchone()
        except Exception as error:
            print(f'Conexión PostgreSQL: ERROR ({type(error).__name__}); revisa host, credenciales, red y TLS.')
            return 1
        print('Conexión PostgreSQL por TLS: OK (SELECT 1).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
