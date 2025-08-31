from abc import ABC, abstractmethod
from typing import List

from rds_proxy_password_rotation.model import DatabaseCredentials, PasswordStage, UserCredentials, Credentials


class PasswordService(ABC):
    @abstractmethod
    def is_rotation_enabled(self, secret_id: str) -> bool:
        pass

    @abstractmethod
    def ensure_valid_secret_state(self, secret_id: str, token: str) -> bool:
        pass

    @abstractmethod
    def get_database_credentials(self, secret_id: str, stage: PasswordStage, token: str = None) -> DatabaseCredentials | None:
        pass

    @abstractmethod
    def get_user_credentials(self, secret_id: str, stage: PasswordStage, token: str = None) -> UserCredentials | None:
        pass

    @abstractmethod
    def set_new_pending_password(self, secret_id: str, token: str, new_username: str, credential: DatabaseCredentials):
        pass

    @abstractmethod
    def set_credentials(self, secret_id: str, token: str, credential: Credentials):
        pass

    @abstractmethod
    def is_multi_user_rotation(self, secret_id: str) -> bool:
        pass

    @abstractmethod
    def get_next_username(self, current_username: str, usernames: List[str]) -> str:
        """
        :param username: The username to rotate.
        :return: Returns the next username in a multi-user rotation strategy based on the given username. For single-user rotation,
                 it returns the same username.
        """
        pass

    @abstractmethod
    def make_new_credentials_current(self, secret_id: str, token: str):
        pass


class DatabaseService(ABC):
    @abstractmethod
    def change_user_credentials(self, old_credentials: DatabaseCredentials, new_password: str):
        pass

    @abstractmethod
    def test_user_credentials(self, credentials: DatabaseCredentials):
        pass
