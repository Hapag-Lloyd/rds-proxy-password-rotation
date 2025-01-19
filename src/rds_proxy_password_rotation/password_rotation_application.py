from enum import Enum

from aws_lambda_powertools import Logger

from rds_proxy_password_rotation.model import RotationStep, PasswordStage
from rds_proxy_password_rotation.services import PasswordService, DatabaseService


class PasswordRotationResult(Enum):
    NOTHING_TO_ROTATE = "nothing_to_rotate"
    STEP_EXECUTED = "step_executed"


class PasswordRotationApplication:
    def __init__(self, password_service: PasswordService, database_service: DatabaseService, logger: Logger):
        self.password_service = password_service
        self.database_service = database_service
        self.logger = logger

    def rotate_secret(self, step: RotationStep, secret_id: str, token: str) -> PasswordRotationResult:
        if not self.password_service.is_rotation_enabled(secret_id):
            self.logger.warning("Rotation is not enabled for the secret %s", secret_id)
            return PasswordRotationResult.NOTHING_TO_ROTATE

        if not self.password_service.ensure_valid_secret_state(secret_id, token):
            return PasswordRotationResult.NOTHING_TO_ROTATE

        match step:
            case RotationStep.CREATE_SECRET:
                self.__create_secret(secret_id, token)
            case RotationStep.SET_SECRET:
                self.__set_secret(secret_id, token)
            case RotationStep.TEST_SECRET:
                pass
            case RotationStep.FINISH_SECRET:
                pass
            case _:
                raise ValueError(f"Invalid rotation step: {step}")

        return PasswordRotationResult.STEP_EXECUTED

    def __set_secret(self, secret_id: str, token: str):
        pending_credential = self.password_service.get_database_credential(secret_id, PasswordStage.PENDING, token)
        if self.database_service.is_credential_valid(pending_credential):
            print(f'set_secret: AWSPENDING secret is already set as password'
                  f' for {pending_dict["username"]}')
            return

        current_credential = self.password_service.get_database_credential(secret_id, PasswordStage.CURRENT)
        if self.database_service.is_credential_valid(current_credential):
            raise ValueError(
                'unable to log into database with current secret of'
                f' secret arn {arn}')

        current_username = current_credential.username
        new_username = self.__get_other_username(current_username)
        is_multi_user_rotation = current_username != new_username

        if is_multi_user_rotation:
            previous_dict = get_secret_dict(service_client, arn, 'AWSPREVIOUS')
            if pending_dict['username'] != previous_dict['username']:
                raise ValueError(
                    'pending and previous have different usernames'
                    f' for secret {arn}')
            conn = get_connection(previous_dict)
            if not conn:
                raise ValueError(
                    'unable to log into database with previous secret of'
                    f' secret arn {arn}')
        else:
            if pending_dict['username'] != current_dict['username']:
                raise ValueError(
                    'pending and current have different usernames'
                    f' for secret {arn}')

        if current_credential.proxy_secret_ids:
            # See if we have a proxy secret to update.
            proxy_secret_name = secret_name.replace('/cavo-rds/', '/cavo-rds-proxy/')
            last = pending_dict['username'][-1]
            if '.proxy-' in current_dict['host'] and \
                    proxy_secret_name != secret_name and last in ('1', '2'):
                proxy_secret_name += last
            else:
                proxy_secret_name = None

        # Set the password to the pending password.
        try:
            with conn.cursor() as cur:
                # Get escaped username via quote_ident
                cur.execute("SELECT quote_ident(%s)", (pending_dict['username'],))
                escaped_username = cur.fetchone()[0]
                cur.execute(f'ALTER USER {escaped_username} WITH PASSWORD %s',
                            (pending_dict['password'],))
                # Before committing the transaction, update the secret
                # used by rds-proxy.
                if proxy_secret_name is not None:
                    service_client.put_secret_value(
                        SecretId=proxy_secret_name,
                        SecretString=json.dumps({
                            'username': pending_dict['username'],
                            'password': pending_dict['password'],
                        }),
                        VersionStages=['AWSCURRENT'])
                conn.commit()
        finally:
            conn.close()
        print('set_secret: successfully set password for user'
              f' {pending_dict["username"]} for secret {arn}')

    def __create_secret(self, secret_id: str, token: str):
        """
        Creates a new version of the secret with the password to rotate to unless a version tagged with AWSPENDING
        already exists.
        """

        credentials_to_rotate = self.password_service.get_database_credential(secret_id, PasswordStage.CURRENT)

        current_username = credentials_to_rotate.username
        new_username = PasswordRotationApplication.__get_other_username(current_username)
        is_multi_user_rotation = current_username != new_username

        if is_multi_user_rotation:
            # we rotate the previous user's password, so the current user is still valid
            credentials_to_rotate = self.password_service.get_database_credential(secret_id, PasswordStage.PREVIOUS)

        pending_credentials = self.password_service.get_database_credential(secret_id, PasswordStage.PENDING, token)

        if pending_credentials and pending_credentials.username == credentials_to_rotate['username']:
            return

        self.password_service.set_new_pending_password(secret_id, token, credentials_to_rotate)

    @staticmethod
    def __get_other_username(username: str) -> str:
        """
        Returns the other username in a multi-user rotation strategy based on the given username. For single-user rotation,
        it returns the same username.

        Use '1' and '2' as suffixes to indicate multi-user rotation.
        """

        if username.endswith('1'):
            new_username = username[:len(username) - 1] + '2'
        elif username.endswith('2'):
            new_username = username[:len(username) - 1] + '1'
        else:
            new_username = username

        return new_username
