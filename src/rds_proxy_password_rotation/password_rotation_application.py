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
        pending_credential = self.password_service.get_database_credentials(secret_id, PasswordStage.PENDING, token)
        current_credential = self.password_service.get_database_credentials(secret_id, PasswordStage.CURRENT)
        is_multi_user_rotation = self.password_service.is_multi_user_rotation(secret_id)

        if is_multi_user_rotation:
            previous_credential = self.password_service.get_database_credentials(secret_id, PasswordStage.PREVIOUS)

            if pending_credential.username != previous_credential.username:
                raise ValueError('pending and previous have different usernames for secret {secret_id}')
        else:
            if pending_credential.username != current_credential.username:
                raise ValueError(f'pending and current have different usernames for secret {secret_id}')

        proxy_secret_id = None
        proxy_secret = None

        for secret_id in current_credential.proxy_secret_ids:
            proxy_secret = self.password_service.get_user_credentials(secret_id, PasswordStage.CURRENT)
            if proxy_secret.username == pending_credential.username:
                proxy_secret_id = secret_id
                break

        self.database_service.change_user_credentials(current_credential, pending_credential)
        # database and proxy user credentials have to be in sync as the proxy user is used to connect to the database
        if proxy_secret_id is not None:
            self.password_service.set_credentials(secret_id, token, proxy_secret)

        self.logger.info(f'set_secret: successfully set password for user {pending_credential.username} for secret {secret_id}')

    def __create_secret(self, secret_id: str, token: str):
        """
        Creates a new version of the secret with the password to rotate to unless a version tagged with AWSPENDING
        already exists.
        """

        credentials_to_rotate = self.password_service.get_database_credentials(secret_id, PasswordStage.CURRENT)

        current_username = credentials_to_rotate.username
        new_username = self.password_service.get_other_username(current_username)
        is_multi_user_rotation = current_username != new_username

        if is_multi_user_rotation:
            # we rotate the previous user's password, so the current user is still valid
            credentials_to_rotate = self.password_service.get_database_credentials(secret_id, PasswordStage.PREVIOUS)

        pending_credentials = self.password_service.get_database_credentials(secret_id, PasswordStage.PENDING, token)

        if pending_credentials and pending_credentials.username == credentials_to_rotate['username']:
            return

        self.password_service.set_new_pending_password(secret_id, token, credentials_to_rotate)
