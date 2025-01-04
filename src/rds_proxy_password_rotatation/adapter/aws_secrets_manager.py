from rds_proxy_password_rotatation.services import SecretsManager


class AwsSecretsManager(SecretsManager):
    def __init__(self):
        pass

    def is_rotation_enabled(self, secret_id: str) -> bool:
        pass
