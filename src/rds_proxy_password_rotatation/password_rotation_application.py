from enum import Enum

from aws_lambda_powertools import Logger

from rds_proxy_password_rotatation.model import RotationStep
from rds_proxy_password_rotatation.services import SecretsManager


class PasswordRotationResult(Enum):
    NOTHING_TO_ROTATE = "nothing_to_rotate"


class PasswordRotationApplication:
    def __init__(self, secrets_manager: SecretsManager, logger: Logger):
        self.secrets_manager = secrets_manager
        self.logger = logger

    def rotate_secret(self, step: RotationStep, secret_id: str) -> PasswordRotationResult:
        if not self.secrets_manager.is_rotation_enabled(secret_id):
            self.logger.warning("Rotation is not enabled for the secret %s", secret_id)
            return PasswordRotationResult.NOTHING_TO_ROTATE

        if step == RotationStep.CREATE_SECRET:
            pass
        else:
            pass
