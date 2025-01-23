from unittest import TestCase
from unittest.mock import Mock

import psycopg
from psycopg import Connection, sql
from aws_lambda_powertools import Logger

from rds_proxy_password_rotation.adapter.postgresql_database_service import PostgreSqlDatabaseService
from rds_proxy_password_rotation.model import UserCredentials


class TestAwsSecretsManagerService(TestCase):
    root_credentials = UserCredentials(username='postgres', password='postgres')

    def setUp(self):
        self.service = PostgreSqlDatabaseService(Mock(spec=Logger))

    def test_should_update_username_and_password_when_change_user_credentials_given_user_exists(self):
        # Given
        old_credentials = UserCredentials(username='test_user', password='test_password')
        new_credentials = UserCredentials(username='new_test_user', password='new_test_password')

        conn = self.__get_connection(self.root_credentials)
        self.__create_user(conn, old_credentials)

        # When
        self.service.change_user_credentials(old_credentials, new_credentials)

        # Then
        conn.close()

        self.__get_connection(new_credentials).close()
        self.assertTrue(True)

    def __get_connection(self, credentials: UserCredentials) -> Connection:
        connect_string = (f'dbname=postgres sslmode=allow port=5432'
                          f' user={credentials.username} host=localhost'
                          f' password={credentials.password}')

        return psycopg.connect(connect_string)

    def __create_user(self, conn: Connection, credentials: UserCredentials):
        with conn.cursor() as cur:
            cur.execute(sql.SQL("CREATE USER {} WITH PASSWORD {}").format(sql.Identifier(credentials.username), credentials.password))
            conn.commit()
