from unittest import TestCase

from localstack_utils.localstack import startup_localstack, stop_localstack

from rds_proxy_password_rotatation.adapter.aws_secrets_manager import AwsSecretsManagerService

class TestAwsSecretsManagerService(TestCase):
    @classmethod
    def setUpClass(self):
        startup_localstack()

    @classmethod
    def tearDownClass(self):
        stop_localstack()
        return super().tearDown()

    def test_should_return_rotation_step_when_to_rotation_step_given_create_secret(self):
        # Given

        # When
        rotation_step = AwsSecretsManagerService.to_rotation_step("create_secret")

        # Then

