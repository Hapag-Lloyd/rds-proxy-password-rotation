import uuid
from unittest import TestCase
from unittest.mock import Mock

import boto3
import os

from aws_lambda_powertools import Logger

from rds_proxy_password_rotatation.adapter.aws_secrets_manager import AwsSecretsManagerService

class TestAwsSecretsManagerService(TestCase):
    __secret_name_without_rotation = f'secret_without_rotation_enabled_{uuid.uuid4()}'
    __secret_name_with_rotation = f'secret_with_rotation_enabled_{uuid.uuid4()}'

    __test_path = os.path.join(os.path.dirname(__file__), '..', '..')

    @classmethod
    def setUpClass(cls):
        secret_value = {
            'username': 'admin',
            'password': 'admin'
        }

        cls.secretsmanager = boto3.client(service_name='secretsmanager', endpoint_url='http://localhost:4566', aws_access_key_id='test',
                                          aws_secret_access_key='test', region_name='eu-central-1')

        # secret without rotation
        cls.secretsmanager.create_secret(
            Name=cls.__secret_name_without_rotation
        )
        cls.secretsmanager.put_secret_value(
            SecretId=cls.__secret_name_without_rotation,
            SecretString=str(secret_value)
        )

        # secret with rotation
        cls.s3_client = boto3.client('s3', endpoint_url='http://localhost:4566', aws_access_key_id='test',
                                     aws_secret_access_key='test', region_name='eu-central-1')

        cls.s3_client.create_bucket(Bucket='s3bucket', CreateBucketConfiguration={'LocationConstraint': 'eu-central-1'})
        cls.s3_client.upload_file(os.path.join(cls.__test_path, 'lambda_function.zip'), 's3bucket', 'function.zip')

        cls.lambda_client = boto3.client('lambda', endpoint_url='http://localhost:4566', aws_access_key_id='test',
                                         aws_secret_access_key='test', region_name='eu-central-1')

        rotation_function = cls.lambda_client.create_function(
            Code={
                'S3Bucket': 's3bucket',
                'S3Key': 'function.zip',
            },
            Description='Dummy function',
            FunctionName='function_name',
            Handler='lambda.handler',
            Publish=True,
            Role='arn:aws:iam::123456789012:role/lambda-role',
            Runtime='python3.10',
        )
        cls.lambda_client.add_permission(
            FunctionName='function_name',
            Action='lambda:InvokeFunction',
            StatementId='1',
            Principal='secretsmanager.amazonaws.com',
        )

        secret = cls.secretsmanager.create_secret(
            Name=cls.__secret_name_with_rotation
        )
        cls.secretsmanager.put_secret_value(
            SecretId=cls.__secret_name_with_rotation,
            SecretString=str(secret_value)
        )

        cls.secretsmanager.rotate_secret(
            SecretId=secret['ARN'],
            RotationLambdaARN=rotation_function['FunctionArn'],
            RotationRules={
                'AutomaticallyAfterDays': 123,
                'Duration': '3h',
                'ScheduleExpression': 'rate(10 days)'
            },
        )

    @classmethod
    def tearDownClass(cls):
        cls.secretsmanager.delete_secret(
            SecretId=cls.__secret_name_without_rotation,
        )
        cls.secretsmanager.delete_secret(
            SecretId=cls.__secret_name_with_rotation,
        )

        cls.lambda_client.delete_function(FunctionName='function_name')

        cls.s3_client.delete_object(Bucket='s3bucket', Key='function.zip')
        cls.s3_client.delete_bucket(Bucket='s3bucket')

    def test_should_return_false_when_is_rotation_enabled_given_secret_has_rotation_disabled(self):
        # Given

        # When
        result = AwsSecretsManagerService(self.secretsmanager, Mock(spec=Logger)).is_rotation_enabled(self.__secret_name_without_rotation)

        # Then
        self.assertFalse(result)

    def test_should_return_true_when_is_rotation_enabled_given_secret_has_rotation_enabled(self):
        # Given

        # When
        result = AwsSecretsManagerService(self.secretsmanager, Mock(spec=Logger)).is_rotation_enabled(self.__secret_name_with_rotation)

        # Then
        self.assertTrue(result)
