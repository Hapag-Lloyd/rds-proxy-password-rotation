import uuid
from unittest import TestCase
from unittest.mock import Mock

import psycopg
from psycopg import Connection, sql
from aws_lambda_powertools import Logger

from rds_proxy_password_rotation.adapter.postgresql_database_service import PostgreSqlDatabaseService
from rds_proxy_password_rotation.model import UserCredentials, DatabaseCredentials, PasswordType


class TestAwsSecretsManagerService(TestCase):
    conn = None
    service = PostgreSqlDatabaseService(Mock(spec=Logger))
    root_credentials = DatabaseCredentials(username='postgres', password='postgres', database_host='localhost', database_port=5432, database_name='postgres', rotation_type=PasswordType.AWS_RDS)

    def setUp(self):
        self.conn = self.service._get_connection(self.root_credentials)
        self.service = PostgreSqlDatabaseService(Mock(spec=Logger))
        self.created_users = []

    def tearDown(self):
        """Clean up created test users to prevent database pollution and improve test performance"""
        if self.created_users:
            try:
                with self.conn.cursor() as cur:
                    for username in self.created_users:
                        try:
                            cur.execute(sql.SQL("DROP USER IF EXISTS {}").format(sql.Identifier(username)))
                        except Exception:
                            # Ignore errors during cleanup
                            pass
                    self.conn.commit()
            except Exception:
                # Ignore cleanup errors
                pass

        self.conn.close()

    def test_should_update_username_and_password_when_change_user_credentials_given_user_exists(self):
        # Given
        old_credentials = self.root_credentials.model_copy(update={'username': f'test_user_{uuid.uuid4()}_a', 'password': 'test_password'})
        new_credentials = old_credentials.model_copy(update={'password': 'new_test_password'})

        self.created_users.append(old_credentials.username)

        self.__create_user(self.conn, old_credentials)

        # When
        self.service.change_user_credentials(old_credentials, new_credentials.password)

        # Then
        self.service._get_connection(new_credentials)


    def test_should_raise_exception_when_change_user_credentials_given_user_does_not_exist(self):
        # Given
        old_credentials = self.root_credentials.model_copy(update={'username': f'test_user_{uuid.uuid4()}_b', 'password': 'test_password'})
        new_credentials = old_credentials.model_copy(update={'password': 'new_test_password'})

        # When
        with self.assertRaises(psycopg.OperationalError):
            self.service.change_user_credentials(old_credentials, new_credentials.password)

    def test_should_raise_exception_when_test_user_credentials_given_user_does_not_exist(self):
        # Given
        credentials = self.root_credentials.model_copy(update={'username': f'test_user_{uuid.uuid4()}_c', 'password': 'test_password'})

        # When
        with self.assertRaises(psycopg.OperationalError):
            self.service.test_user_credentials(credentials)

    def test_should_return_true_when_test_user_credentials_given_user_credentials_are_valid(self):
        # Given
        credentials = self.root_credentials.model_copy(update={'username': f'test_user_{uuid.uuid4()}_d', 'password': 'test_password'})
        self.created_users.append(credentials.username)

        self.__create_user(self.conn, credentials)

        # When
        result = self.service.test_user_credentials(credentials)

        # Then
        self.assertTrue(result)

    def test_should_set_the_password_when_change_user_credentials_given_invalid_characters_in_password(self):
        # Given
        old_credentials = self.root_credentials.model_copy(update={'username': f'test_user_{uuid.uuid4()}_b', 'password': 'test_password'})
        new_credentials = old_credentials.model_copy(update={'password': "xx'x c=s"})

        self.__create_user(self.conn, old_credentials)

        # When
        self.service.change_user_credentials(old_credentials, new_credentials.password)

        successfully_connected = False
        with self.service._get_connection(new_credentials):
            successfully_connected = True

        self.assertTrue(successfully_connected)

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
