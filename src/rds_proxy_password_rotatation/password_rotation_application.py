from enum import Enum

from aws_lambda_powertools import Logger

from rds_proxy_password_rotatation.model import RotationStep
from rds_proxy_password_rotatation.services import SecretsManagerService


class PasswordRotationResult(Enum):
    NOTHING_TO_ROTATE = "nothing_to_rotate"


class PasswordRotationApplication:
    def __init__(self, secrets_manager: SecretsManagerService, logger: Logger):
        self.secrets_manager = secrets_manager
        self.logger = logger

    def rotate_secret(self, step: RotationStep, secret_id: str, token: str) -> PasswordRotationResult:
        if not self.secrets_manager.is_rotation_enabled(secret_id):
            self.logger.warning("Rotation is not enabled for the secret %s", secret_id)
            return PasswordRotationResult.NOTHING_TO_ROTATE

        if not self.secrets_manager.ensure_valid_secret_state(secret_id, token):
            return PasswordRotationResult.NOTHING_TO_ROTATE

        match step:
            case RotationStep.CREATE_SECRET:
                pass
            case RotationStep.SET_SECRET:
                pass
            case RotationStep.TEST_SECRET:
                pass
            case RotationStep.FINISH_SECRET:
                pass
            case _:
                raise ValueError(f"Invalid rotation step: {step}")
