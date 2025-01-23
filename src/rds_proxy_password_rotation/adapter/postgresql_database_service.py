import psycopg
from aws_lambda_powertools import Logger
from psycopg import Connection

from rds_proxy_password_rotation.model import DatabaseCredentials
from rds_proxy_password_rotation.services import DatabaseService


class PostgreSqlDatabaseService(DatabaseService):
    def __init__(self, logger: Logger):
        self.logger = logger

    def change_user_credentials(self, old_credentials: DatabaseCredentials, new_credentials: DatabaseCredentials):
        conn = self.__get_connection(old_credentials)

        try:
            with conn.cursor() as cur:
                cur.execute('ALTER USER %s WITH PASSWORD %s', (new_credentials.username,new_credentials.password))
                conn.commit()
        finally:
            conn.close()

    def __get_connection(self, credentials: DatabaseCredentials) -> Connection | None:
        connect_string = (f'dbname={credentials.database_name} sslmode=verify-full port={credentials.database_port}'
                          f' user={credentials.username} host={credentials.database_host}'
                          f' password={credentials.password}')

        try:
            return psycopg.connect(connect_string)
        except psycopg.OperationalError as e:
            self.logger.error(f'Failed to connect to database {credentials.database_name} on {credentials.database_host}:{credentials.database_port} as {credentials.username}')

            raise e
