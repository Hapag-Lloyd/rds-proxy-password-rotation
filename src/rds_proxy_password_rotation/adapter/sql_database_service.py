import psycopg
from psycopg import Connection

from rds_proxy_password_rotation.model import DatabaseCredentials
from rds_proxy_password_rotation.services import DatabaseService


class PostgreSqlDatabaseService(DatabaseService):
    def is_credential_valid(self, credentials: DatabaseCredentials):
        conn = self.__get_connection(credentials)
        if conn:
            conn.close()
            return True
        return False

    def __get_connection(self, credentials: DatabaseCredentials) -> Connection | None:
        connect_string = (f'dbname={credentials.database_name} sslmode=require port={credentials.database_port}'
                          f' user={credentials.username} host={credentials.database_host}'
                          f' password={credentials.password}')

        try:
            return psycopg.connect(connect_string)
        except psycopg.OperationalError:
            return None
