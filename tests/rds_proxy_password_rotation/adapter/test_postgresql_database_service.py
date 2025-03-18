import uuid
from unittest import TestCase
from unittest.mock import Mock

import psycopg
from psycopg import Connection, sql
from aws_lambda_powertools import Logger

from rds_proxy_password_rotation.adapter.postgresql_database_service import PostgreSqlDatabaseService
from rds_proxy_password_rotation.model import UserCredentials, DatabaseCredentials


class TestAwsSecretsManagerService(TestCase):
    root_credentials = DatabaseCredentials(username='postgres', password='postgres', database_host='localhost', database_port=5432, database_name='postgres')

    def setUp(self):
        self.service = PostgreSqlDatabaseService(Mock(spec=Logger))

    def test_should_update_username_and_password_when_change_user_credentials_given_user_exists(self):
        # Given
        old_credentials = self.root_credentials.model_copy(update={'username': f'test_user_{uuid.uuid4()}_a', 'password': 'test_password'})
        new_credentials = old_credentials.model_copy(update={'password': 'new_test_password'})

        conn = self.__get_connection(self.root_credentials)
        self.__create_user(conn, old_credentials)

        # When
        self.service.change_user_credentials(old_credentials, new_credentials.password)

        # Then
        conn.close()

        self.__get_connection(new_credentials).close()

    def test_should_raise_exception_when_change_user_credentials_given_user_does_not_exist(self):
        # Given
        old_credentials = self.root_credentials.model_copy(update={'username': f'test_user_{uuid.uuid4()}_b', 'password': 'test_password'})
        new_credentials = old_credentials.model_copy(update={'password': 'new_test_password'})

        # When
        with self.assertRaises(psycopg.OperationalError):
            self.service.change_user_credentials(old_credentials, new_credentials.password)

    def __get_connection(self, credentials: DatabaseCredentials) -> Connection:
        connect_string = (f'dbname={credentials.database_name} sslmode=require port={credentials.database_port}'
                          f' user={credentials.username} host={credentials.database_host}'
                          f' password={credentials.password}')

        return psycopg.connect(connect_string)

    def __create_user(self, conn: Connection, credentials: UserCredentials):
        with conn.cursor() as cur:
            cur.execute(sql.SQL("CREATE USER {} WITH PASSWORD {}").format(sql.Identifier(credentials.username), credentials.password))
            cur.execute(sql.SQL("ALTER USER {} WITH NOSUPERUSER").format(sql.Identifier(credentials.username)))
            conn.commit()
