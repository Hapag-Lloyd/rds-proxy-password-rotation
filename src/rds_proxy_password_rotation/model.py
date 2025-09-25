from enum import Enum

from pydantic import BaseModel, field_validator
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


class UserCredentials(Credentials):
    username: str
    password: str

    def get_next_username(self) -> str:
        if self.username[-1].isdigit():
            next_digit = 2 if self.username[-1] == '1' else 1  # only toggle between 1 and 2
            return self.username[:-1] + str(next_digit)
        else:
            return self.username

    @classmethod
    @field_validator('username')
    def validate_username(cls, username: str) -> str:
        if username[-1] not in ('1', '2'):
            raise ValueError(f"<username> must end with '1' or '2' as required by the rotation logic. Invalid: {username}")

        return username


class DatabaseCredentials(UserCredentials):
    database_host: str
    database_port: int
    database_name: str

    proxy_secret_ids: Optional[list[UserCredentials]] = None

    def copy_and_replace_username(self, new_username: str) -> 'DatabaseCredentials':
        return self.model_copy(update={'username': new_username})
