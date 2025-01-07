import boto3
from mypy_boto3_secretsmanager.client import SecretsManagerClient

from rds_proxy_password_rotatation.services import SecretsManagerService


class AwsSecretsManagerService(SecretsManagerService):
    def __init__(self, secretsmanager_client: SecretsManagerClient):
        self.client = secretsmanager_client

    def is_rotation_enabled(self, secret_id: str) -> bool:
        metadata = self.client.describe_secret(SecretId=secret_id)

        return 'RotationEnabled' in metadata and metadata['RotationEnabled']
