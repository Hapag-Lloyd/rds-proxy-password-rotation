from enum import Enum

from rds_proxy_password_rotatation.model import RotationStep


class AwsRotationStep(Enum):
    CREATE_SECRET = "create_secret"
    """Create a new version of the secret"""
    SET_SECRET = "set_secret"
    """Change the credentials in the database or service"""
    TEST_SECRET = "test_secret"
    """Test the new secret version"""
    FINISH_SECRET = "finish_secret"
    """Finish the rotation"""

    @staticmethod
    def to_rotation_step(step: str) -> RotationStep:
        match step:
            case AwsRotationStep.CREATE_SECRET.value:
                return RotationStep.CREATE_SECRET
            case AwsRotationStep.SET_SECRET.value:
                return RotationStep.SET_SECRET
            case AwsRotationStep.TEST_SECRET.value:
                return RotationStep.TEST_SECRET
            case AwsRotationStep.FINISH_SECRET.value:
                return RotationStep.FINISH_SECRET
            case _:
                raise ValueError(f"Invalid rotation step: {step}")
