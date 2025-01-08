from aws_lambda_powertools import Logger
from mypy_boto3_secretsmanager.client import SecretsManagerClient

from rds_proxy_password_rotatation.services import SecretsManagerService


class AwsSecretsManagerService(SecretsManagerService):
    def __init__(self, secretsmanager_client: SecretsManagerClient, logger: Logger):
        self.client = secretsmanager_client
        self.logger = logger

    def is_rotation_enabled(self, secret_id: str) -> bool:
        metadata = self.client.describe_secret(SecretId=secret_id)

        return 'RotationEnabled' in metadata and metadata['RotationEnabled']

    def ensure_valid_secret_state(self, secret_id: str, token: str) -> bool:
        metadata = self.client.describe_secret(SecretId=secret_id)
        versions = metadata['VersionIdsToStages']

        if token not in versions:
            self.logger.error("Secret version %s has no stage for rotation of secret %s." % (token, secret_id))
            raise ValueError("Secret version %s has no stage for rotation of secret %s." % (token, secret_id))
        elif "AWSCURRENT" in versions[token]:
            self.logger.info("Secret version %s already set as AWSCURRENT for secret %s." % (token, secret_id))
            return False
        elif "AWSPENDING" not in versions[token]:
            self.logger.error("Secret version %s not set as AWSPENDING for rotation of secret %s." % (token, secret_id))
            raise ValueError("Secret version %s not set as AWSPENDING for rotation of secret %s." % (token, secret_id))
        else:
            return True
