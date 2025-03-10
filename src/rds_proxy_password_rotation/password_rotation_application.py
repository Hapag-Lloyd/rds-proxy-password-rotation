from enum import Enum

from aws_lambda_powertools import Logger

from rds_proxy_password_rotation.model import RotationStep, PasswordStage
from rds_proxy_password_rotation.services import PasswordService


class PasswordRotationResult(Enum):
    NOTHING_TO_ROTATE = "nothing_to_rotate"
    STEP_EXECUTED = "step_executed"


class PasswordRotationApplication:
    def __init__(self, password_service: PasswordService, logger: Logger):
        self.password_service = password_service
        self.logger = logger

    def rotate_secret(self, step: RotationStep, secret_id: str, token: str) -> PasswordRotationResult:
        if not self.password_service.is_rotation_enabled(secret_id):
            self.logger.warning("Rotation is not enabled for the secret %s", secret_id)
            return PasswordRotationResult.NOTHING_TO_ROTATE

        if not self.password_service.ensure_valid_secret_state(secret_id, token):
            return PasswordRotationResult.NOTHING_TO_ROTATE

        match step:
            case RotationStep.CREATE_SECRET:
                self.__create_new_secret_version_if_no_pending_version_exists(secret_id, token)
            case RotationStep.SET_SECRET:
                pass
            case RotationStep.TEST_SECRET:
                pass
            case RotationStep.FINISH_SECRET:
                pass
            case _:
                raise ValueError(f"Invalid rotation step: {step}")

        return PasswordRotationResult.STEP_EXECUTED

    def __create_new_secret_version_if_no_pending_version_exists(self, secret_id: str, token: str):
        """
        Creates a new version of the secret with the password to rotate to unless a version tagged with AWSPENDING
        already exists.
        """

        if self.password_service.get_database_credential(secret_id, PasswordStage.PENDING, token):
          return

        credentials_to_rotate = self.password_service.get_database_credential(secret_id, PasswordStage.CURRENT)

        current_username = credentials_to_rotate.username
        new_username = PasswordRotationApplication.__get_other_username(current_username)
        is_multi_user_rotation = current_username != new_username

        if is_multi_user_rotation:
            # we rotate the previous user's password, so the current user is still valid
            credentials_to_rotate = self.password_service.get_database_credential(secret_id, PasswordStage.PREVIOUS)


        self.password_service.set_new_pending_password(secret_id, token, credentials_to_rotate)

    @staticmethod
    def __get_other_username(username: str) -> str:
        """
        Returns the other username in a multi-user rotation strategy based on the given username. For single-user rotation,
        it returns the same username.

        Use '1' and '2' as suffixes to indicate multi-user rotation.
        """

        if username.endswith('_blue'):
            new_username = username[:len(username) - len('blue')] + 'green'
        elif username.endswith('green'):
            new_username = username[:len(username) - len('green')] + 'blue'
        else:
            new_username = username

        return new_username
