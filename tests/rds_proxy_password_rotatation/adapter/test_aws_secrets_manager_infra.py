import uuid
from unittest import TestCase

import boto3

from rds_proxy_password_rotatation.adapter.aws_secrets_manager import AwsSecretsManagerService

class TestAwsSecretsManagerService(TestCase):
    secretname_without_rotation = f'secret_without_rotation_enabled_{uuid.uuid4()}'
    secretname_with_rotation = f'secret_with_rotation_enabled_{uuid.uuid4()}'

    @classmethod
    def setUpClass(self):
        self.secretsmanager = boto3.client(service_name='secretsmanager', endpoint_url='http://localhost:4566',aws_access_key_id='test',
                                      aws_secret_access_key='test')
        secret = self.secretsmanager.create_secret(
            Name=self.secretname_without_rotation
        )

        secret = self.secretsmanager.create_secret(
            Name=self.secretname_with_rotation
        )

        """ secretsmanager.rotate_secret(
            SecretId=secret['ARN'],
            RotationRules={
                'AutomaticallyAfterDays': 123,
                'Duration': '3h',
                'ScheduleExpression': 'rate(10 days)'
            },
            RotateImmediately=False
        ) """

    @classmethod
    def tearDownClass(self):
        self.secretsmanager.delete_secret(
            SecretId=self.secretname_without_rotation,
        )
        self.secretsmanager.delete_secret(
            SecretId=self.secretname_with_rotation,
        )

    def test_should_return_false_when_is_rotation_enabled_given_secret_has_rotation_disabled(self):
        # Given

        # When
        result = AwsSecretsManagerService(self.secretsmanager).is_rotation_enabled(self.secretname_without_rotation)

        # Then
        self.assertFalse(result)

    def test_should_return_true_when_is_rotation_enabled_given_secret_has_rotation_enabled(self):
        # Given

        # When
        result = AwsSecretsManagerService(self.secretsmanager).is_rotation_enabled(self.secretname_with_rotation)

        # Then
        self.assertTrue(result)
