from aws_lambda_powertools import Logger
from dependency_injector import containers, providers

from rds_proxy_password_rotatation.adapter.aws_secrets_manager import AwsSecretsManagerService
from rds_proxy_password_rotatation.password_rotation_application import PasswordRotationApplication


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    logger = providers.Singleton(
        Logger,
    )

    secrets_manager = providers.Singleton(
        AwsSecretsManagerService,
    )

    password_rotation_application = providers.Singleton(
        PasswordRotationApplication,
        secrets_manager=secrets_manager,
        logger=logger,
    )
