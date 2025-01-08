from abc import ABC, abstractmethod

class SecretsManagerService(ABC):
    @abstractmethod
    def is_rotation_enabled(self, secret_id: str) -> bool:
        pass

    @abstractmethod
    def ensure_valid_secret_state(self, secret_id: str, token: str) -> bool:
        pass
