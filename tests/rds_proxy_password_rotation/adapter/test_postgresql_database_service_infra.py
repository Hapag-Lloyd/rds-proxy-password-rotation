import uuid
from unittest import TestCase
from unittest.mock import Mock

import psycopg
from psycopg import Connection, sql
from aws_lambda_powertools import Logger

from rds_proxy_password_rotation.adapter.postgresql_database_service import PostgreSqlDatabaseService
from rds_proxy_password_rotation.model import UserCredentials, DatabaseCredentials


class TestAwsSecretsManagerService(TestCase):
    conn = None
    root_credentials = DatabaseCredentials(username='postgres', password='postgres', database_host='localhost', database_port=5432, database_name='postgres')

    def setUp(self):
        self.service = PostgreSqlDatabaseService(Mock(spec=Logger))
        self.conn = self.service._get_connection(self.root_credentials)

    def tearDown(self):
        self.conn.close()

    def test_should_update_username_and_password_when_change_user_credentials_given_user_exists(self):
        # Given
        old_credentials = self.root_credentials.model_copy(update={'username': f'test_user_{uuid.uuid4()}_a', 'password': 'test_password'})
        new_credentials = old_credentials.model_copy(update={'password': 'new_test_password'})

        self.__create_user(self.conn, old_credentials)

        # When
        self.service.change_user_credentials(old_credentials, new_credentials.password)

        self.service._get_connection(new_credentials)

    def test_should_raise_exception_when_change_user_credentials_given_user_does_not_exist(self):
        # Given
        old_credentials = self.root_credentials.model_copy(update={'username': f'test_user_{uuid.uuid4()}_b', 'password': 'test_password'})
        new_credentials = old_credentials.model_copy(update={'password': 'new_test_password'})

        # When
        with self.assertRaises(psycopg.OperationalError):
            self.service.change_user_credentials(old_credentials, new_credentials.password)

    def test_should_set_the_password_when_change_user_credentials_given_invalid_characters_in_password(self):
        # Given
        old_credentials = self.root_credentials.model_copy(update={'username': f'test_user_{uuid.uuid4()}_b', 'password': 'test_password'})
        new_credentials = old_credentials.model_copy(update={'password': "xx'x c=s"})

        self.__create_user(self.conn, old_credentials)

        # When
        self.service.change_user_credentials(old_credentials, new_credentials.password)

        with self.service._get_connection(new_credentials):
            self.assertTrue(True)

    def test_should_not_connect_to_the_database_when_change_user_credentials_given_invalid_characters_in_username(self):
        # Given
        old_credentials = self.root_credentials.model_copy(update={'username': f'test_user_{uuid.uuid4()}_b"; DROP TABLE users; --', 'password': 'test_password'})
        new_credentials = old_credentials.model_copy(update={'password': 'new_test_password'})

        # When
        with self.assertRaises(psycopg.OperationalError) as context:
            self.service.change_user_credentials(old_credentials, new_credentials.password)

        self.assertIn('password authentication failed for user', str(context.exception))

    @staticmethod
    def __create_user(conn: Connection, credentials: UserCredentials):
        with conn.cursor() as cur:
            cur.execute(sql.SQL("CREATE USER {} WITH PASSWORD {}").format(sql.Identifier(credentials.username), credentials.password))
            cur.execute(sql.SQL("ALTER USER {} WITH NOSUPERUSER").format(sql.Identifier(credentials.username)))
            conn.commit()
