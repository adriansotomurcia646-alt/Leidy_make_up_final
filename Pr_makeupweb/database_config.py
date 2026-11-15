"""Validación redactada de DATABASE_URL para Django y diagnóstico local."""
import re
from urllib.parse import urlsplit

class DatabaseURLValidationError(ValueError):
    """Error de formato que nunca incluye la URI ni sus credenciales."""


def diagnose_database_url(database_url):
    """Devuelve indicadores no sensibles y un error de formato sanitizado."""
    status = {
        'present': bool(database_url),
        'postgres_scheme': False,
        'username_present': False,
        'password_present': False,
        'host_present': False,
        'port_valid': False,
        'brackets_in_username': False,
        'brackets_in_password': False,
        'malformed_percent_escape': False,
    }
    if not database_url:
        return status, 'DATABASE_URL no está configurada.'
    if database_url != database_url.strip() or any(char.isspace() for char in database_url):
        return status, 'DATABASE_URL contiene espacios sin codificar.'

    scheme, separator, remainder = database_url.partition('://')
    status['postgres_scheme'] = separator == '://' and scheme in {'postgres', 'postgresql'}
    if not status['postgres_scheme']:
        return status, 'DATABASE_URL debe usar el esquema postgres:// o postgresql://.'

    authority = re.split(r'[/?#]', remainder, maxsplit=1)[0]
    userinfo, has_userinfo, _ = authority.rpartition('@')
    if not has_userinfo:
        return status, 'DATABASE_URL no contiene usuario y contraseña separados del host.'

    username, has_password, password = userinfo.partition(':')
    status['username_present'] = bool(username)
    status['password_present'] = has_password and bool(password)
    status['brackets_in_username'] = '[' in username or ']' in username
    status['brackets_in_password'] = has_password and ('[' in password or ']' in password)
    status['malformed_percent_escape'] = bool(
        re.search(r'%(?![0-9A-Fa-f]{2})', userinfo)
    )
    try:
        parsed = urlsplit(database_url)
    except ValueError:
        # A bad userinfo character can prevent urlsplit() from reaching the
        # host. Parse a sanitized temporary authority to report each component.
        try:
            parsed = urlsplit(f'{scheme}://diagnostic:diagnostic@{authority.rsplit("@", 1)[-1]}/')
        except ValueError:
            return status, 'DATABASE_URL tiene una autoridad o un puerto inválido.'
    try:
        status['host_present'] = bool(parsed.hostname)
        status['port_valid'] = parsed.port is None or 1 <= parsed.port <= 65535
    except ValueError:
        status['host_present'] = bool(parsed.hostname)
        status['port_valid'] = False

    if not status['host_present']:
        return status, 'DATABASE_URL no contiene un host válido.'
    if not status['port_valid']:
        return status, 'DATABASE_URL contiene un puerto inválido.'
    if status['brackets_in_username']:
        return status, 'DATABASE_URL contiene corchetes sin codificar en el usuario.'
    if status['brackets_in_password']:
        return status, (
            'DATABASE_URL contiene corchetes sin codificar en la contraseña. '
            'Si son parte de la contraseña real, codifícala localmente con '
            'urllib.parse.quote(password, safe=""); no codifiques la URI completa.'
        )
    if authority.count('@') > 1:
        return status, 'DATABASE_URL contiene un carácter @ sin codificar en usuario o contraseña.'
    if status['malformed_percent_escape']:
        return status, 'DATABASE_URL contiene un escape porcentual incompleto en usuario o contraseña.'
    if not status['username_present'] or not status['password_present']:
        return status, 'DATABASE_URL requiere usuario y contraseña.'

    try:
        import dj_database_url
    except ImportError:
        return status, 'Falta dj-database-url; instala requirements-postgresql.txt.'
    try:
        dj_database_url.parse(database_url)
    except Exception:
        return status, 'dj-database-url no pudo interpretar DATABASE_URL; revisa su formato.'
    return status, None


def parse_database_url(database_url, *, conn_max_age, ssl_require):
    """Valida y convierte una URI sin revelar valores si falla el parser."""
    _, problem = diagnose_database_url(database_url)
    if problem:
        raise DatabaseURLValidationError(problem)
    try:
        import dj_database_url

        return dj_database_url.parse(
            database_url,
            conn_max_age=conn_max_age,
            ssl_require=ssl_require,
        )
    except Exception:
        raise DatabaseURLValidationError(
            'dj-database-url no pudo interpretar DATABASE_URL; revisa su formato.'
        ) from None
