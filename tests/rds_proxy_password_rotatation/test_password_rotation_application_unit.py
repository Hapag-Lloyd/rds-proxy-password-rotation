from unittest import TestCase
from unittest.mock import Mock

from aws_lambda_powertools import Logger

from rds_proxy_password_rotatation.model import RotationStep
from rds_proxy_password_rotatation.password_rotation_application import PasswordRotationApplication, PasswordRotationResult
from rds_proxy_password_rotatation.services import SecretsManagerService


class TestPasswordRotationApplication(TestCase):
    def test_should_do_nothing_when_rotate_secret_given_secret_has_rotation_disabled(self):
        # Given
        secrets_manager = Mock(spec=SecretsManagerService)
        secrets_manager.is_rotation_enabled.return_value = False

        application = PasswordRotationApplication(secrets_manager, Mock(spec=Logger))

        # When
        result = application.rotate_secret(RotationStep.CREATE_SECRET, 'secret_id', 'token')

        # Then
        self.assertEqual(result, PasswordRotationResult.NOTHING_TO_ROTATE)

    def test_should_log_warning_when_rotate_secret_given_secret_has_rotation_disabled(self):
        # Given
        secrets_manager = Mock(spec=SecretsManagerService)
        secrets_manager.is_rotation_enabled.return_value = False

        logger = Mock(spec=Logger)

        application = PasswordRotationApplication(secrets_manager, logger)

        # When
        application.rotate_secret(RotationStep.CREATE_SECRET, 'secret_id', 'token')

        # Then
        logger.warning.assert_called()


