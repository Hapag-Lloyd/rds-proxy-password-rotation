from enum import Enum

from pydantic import BaseModel
from pydantic.dataclasses import dataclass


class RotationStep(Enum):
    CREATE_SECRET = "create_secret"
    """Create a new version of the secret"""
    SET_SECRET = "set_secret"
    """Change the credentials in the database or service"""
    TEST_SECRET = "test_secret"
    """Test the new secret version"""
    FINISH_SECRET = "finish_secret"
    """Finish the rotation"""


class PasswordStage(Enum):
    CURRENT = "CURRENT"
    PENDING = "PENDING"
    PREVIOUS = "PREVIOUS"


@dataclass(frozen=True)
class DatabaseCredentials(BaseModel, extra='allow'):
    username: str
    password: str

