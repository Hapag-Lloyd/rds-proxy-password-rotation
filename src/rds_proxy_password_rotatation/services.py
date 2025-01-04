from abc import ABC, abstractmethod

class SecretsManager(ABC):
    @abstractmethod
    def is_rotation_enabled(self, secret_id: str) -> bool:
        pass
