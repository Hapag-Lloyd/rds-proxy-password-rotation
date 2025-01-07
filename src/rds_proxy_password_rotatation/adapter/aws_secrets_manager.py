import boto3

from rds_proxy_password_rotatation.services import SecretsManagerService


class AwsSecretsManagerService(SecretsManagerService):
    def __init__(self):
        self.client = boto3.client('secretsmanager')

    def is_rotation_enabled(self, secret_id: str) -> bool:
        metadata = self.client.describe_secret(SecretId=secret_id)

        return 'RotationEnabled' in metadata and metadata['RotationEnabled']
