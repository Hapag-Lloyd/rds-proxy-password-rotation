from enum import Enum
from typing import List

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


class PasswordType(Enum):
    AWS_RDS = "AWS RDS"


class Credentials(BaseModel, extra='allow'):
    rotation_type: PasswordType
    rotation_usernames: Optional[List[str]] = []


class UserCredentials(Credentials):
    username: str
    password: str


class DatabaseCredentials(UserCredentials):
    database_host: str
    database_port: int
    database_name: str

    proxy_secret_ids: Optional[list[UserCredentials]] = None

    def copy_and_replace_username(credentials: 'DatabaseCredentials', new_username: str) -> 'DatabaseCredentials':
        return credentials.model_copy(update={'username': new_username})
