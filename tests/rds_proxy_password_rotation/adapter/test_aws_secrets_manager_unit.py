from logging import Logger
from unittest import TestCase
from unittest.mock import Mock

from mypy_boto3_secretsmanager.client import SecretsManagerClient

from rds_proxy_password_rotation.adapter.aws_secrets_manager import AwsSecretsManagerService

class TestAwsSecretsManagerService(TestCase):
    usernames = ['user1', 'user2', 'user3']

    def test_should_return_user2_when_get_next_username_given_user1_is_current(self):
        # Given

        # When
        result = AwsSecretsManagerService(Mock(spec=SecretsManagerClient), Mock(spec=Logger)).get_next_username('user1', self.usernames)

        # Then
        self.assertEqual(result, 'user2')

    def test_should_return_user1_when_get_next_username_given_user3_is_current(self):
        # Given

        # When
        result = AwsSecretsManagerService(Mock(spec=SecretsManagerClient), Mock(spec=Logger)).get_next_username('user3', self.usernames)

        # Then
        self.assertEqual(result, 'user1')

    def test_should_return_the_same_username_when_get_next_username_given_single_user_rotation(self):
        # Given
        single_usernames = ['single_user']

        # When
        result = AwsSecretsManagerService(Mock(spec=SecretsManagerClient), Mock(spec=Logger)).get_next_username('single_user', single_usernames)

        # Then
        self.assertEqual(result, 'single_user')

    def test_should_return_the_same_username_when_get_next_username_given_usernames_are_not_set(self):
        # Given
        empty_usernames = []

        # When
        result = AwsSecretsManagerService(Mock(spec=SecretsManagerClient), Mock(spec=Logger)).get_next_username('any_user', empty_usernames)

        # Then
        self.assertEqual(result, 'any_user')
