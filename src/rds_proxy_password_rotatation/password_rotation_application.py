from enum import Enum

from aws_lambda_powertools import Logger

from rds_proxy_password_rotatation.model import RotationStep
from rds_proxy_password_rotatation.services import PasswordService


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
                self.__create_secret(secret_id, token)
            case RotationStep.SET_SECRET:
                pass
            case RotationStep.TEST_SECRET:
                pass
            case RotationStep.FINISH_SECRET:
                pass
            case _:
                raise ValueError(f"Invalid rotation step: {step}")

        return PasswordRotationResult.STEP_EXECUTED

    def __create_secret(self, secret_id: str, token: str):
        """
        Creates a new version of the secret with the password to rotate to unless a version tagged with AWSPENDING
        already exists.
        """

        credentials_to_rotate = self.password_service.get_credential(secret_id, 'AWSCURRENT')

        current_username = credentials_to_rotate.username
        new_username = PasswordRotationApplication.__get_other_username(current_username)
        is_multi_user_rotation = current_username != new_username

        if is_multi_user_rotation:
            # we rotate the previous user's password, so the current user is still valid
            credentials_to_rotate = self.password_service.get_credential(secret_id, 'AWSPREVIOUS')

        pending_credentials = self.password_service.get_credential(secret_id, 'AWSPENDING', token)

        if pending_credentials and pending_credentials.username == credentials_to_rotate['username']:
            return

        self.password_service.set_new_pending_password(secret_id, 'AWSPENDING', token, credentials_to_rotate)

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
