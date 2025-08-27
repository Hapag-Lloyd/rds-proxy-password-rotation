import psycopg
from aws_lambda_powertools import Logger
from psycopg import Connection, sql

from rds_proxy_password_rotation.model import DatabaseCredentials
from rds_proxy_password_rotation.services import DatabaseService


class PostgreSqlDatabaseService(DatabaseService):
    def __init__(self, logger: Logger):
        self.logger = logger

    def test_user_credentials(self, credentials: DatabaseCredentials) -> bool:
        with self.__get_connection(credentials) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")

                return True

    def change_user_credentials(self, old_credentials: DatabaseCredentials, new_password: str):
        with self.__get_connection(old_credentials) as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(sql.SQL("ALTER USER {} WITH PASSWORD {}").format(sql.Identifier(old_credentials.username), new_password))
                    conn.commit()
            finally:
                conn.close()

    def __get_connection(self, credentials: DatabaseCredentials) -> Connection:
        connect_string = (f'dbname={credentials.database_name} sslmode=require port={credentials.database_port}'
                          f' user={credentials.username} host={credentials.database_host}'
                          f' password={credentials.password} connect_timeout=3')

        try:
            return psycopg.connect(connect_string)
        except psycopg.OperationalError as e:
            self.logger.error(f'Failed to connect to database {credentials.database_name} on {credentials.database_host}:{credentials.database_port} as {credentials.username}')

            raise e
