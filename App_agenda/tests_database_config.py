from django.test import SimpleTestCase

from Pr_makeupweb.database_config import (
    DatabaseURLValidationError,
    diagnose_database_url,
    parse_database_url,
)


class DatabaseURLValidationTests(SimpleTestCase):
    def test_parses_encoded_password_and_requires_tls_in_production(self):
        database_url = 'postgresql://pooler-user:pa%5Bss%5D@pooler.example.test:5432/postgres'

        status, problem = diagnose_database_url(database_url)
        config = parse_database_url(database_url, conn_max_age=60, ssl_require=True)

        self.assertIsNone(problem)
        self.assertTrue(status['postgres_scheme'])
        self.assertTrue(status['password_present'])
        self.assertEqual(config['PASSWORD'], 'pa[ss]')
        self.assertEqual(config['CONN_MAX_AGE'], 60)
        self.assertEqual(config['OPTIONS']['sslmode'], 'require')

    def test_rejects_unencoded_password_brackets_without_echoing_uri(self):
        database_url = 'postgresql://pooler-user:private-value[brackets]@pooler.example.test:5432/postgres'

        status, problem = diagnose_database_url(database_url)

        self.assertTrue(status['brackets_in_password'])
        self.assertTrue(status['host_present'])
        self.assertTrue(status['port_valid'])
        self.assertIn('contraseña', problem)
        self.assertNotIn('private-value', problem)
        with self.assertRaises(DatabaseURLValidationError) as raised:
            parse_database_url(database_url, conn_max_age=60, ssl_require=True)
        self.assertNotIn('private-value', str(raised.exception))

    def test_rejects_invalid_port_without_echoing_uri(self):
        status, problem = diagnose_database_url(
            'postgresql://user:password@pooler.example.test:70000/postgres'
        )

        self.assertFalse(status['port_valid'])
        self.assertIn('puerto', problem)
        self.assertNotIn('password', problem)

    def test_requires_postgresql_scheme_and_nonempty_uri(self):
        for database_url in ('', 'sqlite:///db.sqlite3', None):
            with self.subTest(database_url=database_url):
                _, problem = diagnose_database_url(database_url)
                self.assertIsNotNone(problem)
