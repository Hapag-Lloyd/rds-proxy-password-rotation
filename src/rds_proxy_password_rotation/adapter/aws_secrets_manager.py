from uuid import uuid4

from aws_lambda_powertools import Logger
from cachetools import cached, LRUCache
from mypy_boto3_secretsmanager.client import SecretsManagerClient
from mypy_boto3_secretsmanager.type_defs import DescribeSecretResponseTypeDef
from pydantic import ValidationError

from rds_proxy_password_rotation.model import DatabaseCredentials, PasswordStage
from rds_proxy_password_rotation.services import PasswordService


class AwsSecretsManagerService(PasswordService):
    def __init__(self, secretsmanager_client: SecretsManagerClient, logger: Logger):
        self.client = secretsmanager_client
        self.logger = logger

    def is_rotation_enabled(self, secret_id: str) -> bool:
        metadata = self.__get_secret_metadata(secret_id)

        return 'RotationEnabled' in metadata and metadata['RotationEnabled']

    def ensure_valid_secret_state(self, secret_id: str, token: str) -> bool:
        metadata = self.__get_secret_metadata(secret_id)
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

    def get_database_credential(self, secret_id: str, stage: PasswordStage, token: str = None) -> DatabaseCredentials | None:
        stage_string = AwsSecretsManagerService.__get_stage_string(stage)

        try:
            if token is None:
                secret = self.client.get_secret_value(SecretId=secret_id, VersionStage=stage_string)
            else:
                secret = self.client.get_secret_value(SecretId=secret_id, VersionId=token, VersionStage=stage_string)

            return DatabaseCredentials.model_validate_json(secret['SecretString'])
        except ValidationError as e:
            self.logger.error(f"Failed to parse secret value for secret {secret_id} (stage: {stage_string}, token: {token})")

            raise e
        except self.client.exceptions.ResourceNotFoundException:
            self.logger.error(f"Failed to retrieve secret value for secret {secret_id} (stage: {stage_string}, token: {token})")

        return None

    def set_new_pending_password(self, secret_id: str, token: str, credential: DatabaseCredentials):
        if token is None:
            token = str(uuid4())

        pending_credential = credential.model_copy(update={'password': self.client.get_random_password(ExcludeCharacters=':/@"\'\\')['RandomPassword']})

        self.client.put_secret_value(
                SecretId=secret_id,
                ClientRequestToken=token,
                SecretString=pending_credential.model_dump_json(),
                VersionStages=[AwsSecretsManagerService.__get_stage_string(PasswordStage.PENDING)])

        self.logger.info(f'new pending secret created: {secret_id} and version {token}')

    @cached(cache=LRUCache(maxsize=20))
    def __get_secret_metadata(self, secret_id: str) -> DescribeSecretResponseTypeDef:
        return self.client.describe_secret(SecretId=secret_id)

    @staticmethod
    def __get_stage_string(stage: PasswordStage) -> str:
        match stage:
            case PasswordStage.CURRENT:
                return "AWSCURRENT"
            case PasswordStage.PENDING:
                return "AWSPENDING"
            case PasswordStage.PREVIOUS:
                return "AWSPREVIOUS"
            case _:
                raise ValueError(f"Invalid stage: {stage}")
