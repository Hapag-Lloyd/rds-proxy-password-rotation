from abc import ABC, abstractmethod

from rds_proxy_password_rotatation.model import DatabaseCredentials, PasswordStage


class PasswordService(ABC):
    @abstractmethod
    def is_rotation_enabled(self, secret_id: str) -> bool:
        pass

    @abstractmethod
    def ensure_valid_secret_state(self, secret_id: str, token: str) -> bool:
        pass

    @abstractmethod
    def get_database_credential(self, secret_id: str, stage: PasswordStage, token: str = None) -> DatabaseCredentials | None:
        pass

    @abstractmethod
    def set_new_pending_password(self,secret_id: str, token: str, credential: DatabaseCredentials):
        pass
