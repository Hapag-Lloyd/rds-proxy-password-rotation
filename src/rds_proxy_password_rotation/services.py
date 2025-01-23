from abc import ABC, abstractmethod

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
    def set_new_pending_password(self, secret_id: str, token: str, credential: DatabaseCredentials):
        pass

    @abstractmethod
    def set_credentials(self, secret_id: str, token: str, credential: Credentials):
        pass

    @abstractmethod
    def is_multi_user_rotation(self, secret_id: str) -> bool:
        pass

    @abstractmethod
    def get_other_username(self, username: str) -> str:
        """
        Use '1' and '2' as suffixes for the username to indicate multi-user rotation.

        :param username: The username to rotate.
        :return: Returns the other username in a multi-user rotation strategy based on the given username. For single-user rotation,
                 it returns the same username.
        """
        pass


class DatabaseService(ABC):
    @abstractmethod
    def change_user_credentials(self, old_credentials: DatabaseCredentials, new_credentials: DatabaseCredentials):
        pass
