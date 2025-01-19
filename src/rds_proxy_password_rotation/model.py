from enum import Enum

from pydantic import BaseModel
from typing_extensions import Optional


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


class DatabaseCredentials(BaseModel, frozen=True, extra='allow'):
    username: str
    password: str

    database_host: str
    database_port: int
    database_name: str

    proxy_secret_ids: Optional[list[str]]
