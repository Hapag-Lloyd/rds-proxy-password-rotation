import os
import uuid
import random
from unittest import TestCase
from unittest.mock import Mock

import boto3
import psycopg
from aws_lambda_powertools import Logger

from rds_proxy_password_rotation.adapter.aws_secrets_manager import AwsSecretsManagerService
from rds_proxy_password_rotation.adapter.postgresql_database_service import PostgreSqlDatabaseService
from rds_proxy_password_rotation.model import DatabaseCredentials, RotationStep
from rds_proxy_password_rotation.password_rotation_application import PasswordRotationApplication, PasswordRotationResult


class TestPasswordRotationApplicationInfra(TestCase):
    __secret_name_without_rotation = f'secret_without_rotation_enabled_{uuid.uuid4()}'
    __secret_name_with_rotation = f'secret_with_rotation_enabled_{uuid.uuid4()}'
    __s3_bucket_name = f'my-bucket-{uuid.uuid4()}'
    __function_name = f'rotation--{uuid.uuid4()}'

    __test_path = os.path.join(os.path.dirname(__file__), '..')

    @classmethod
    def setUpClass(cls):
        secret_value_without_rotation = DatabaseCredentials(username='admin', password='admin', database_host='localhost', database_port=5432, database_name='test')
        secret_value_with_rotation = DatabaseCredentials(username='admin1', password='admin', database_host='localhost', database_port=5432, database_name='test')

        cls.secretsmanager = boto3.client(service_name='secretsmanager', endpoint_url='http://localhost:4566', aws_access_key_id='test',
                                          aws_secret_access_key='test', region_name='eu-central-1')

        # secret without rotation
        cls.secretsmanager.create_secret(
            Name=cls.__secret_name_without_rotation
        )
        cls.secretsmanager.put_secret_value(
            SecretId=cls.__secret_name_without_rotation,
            SecretString=secret_value_without_rotation.model_dump_json()
        )

        # secret with rotation
        cls.s3_client = boto3.client('s3', endpoint_url='http://localhost:4566', aws_access_key_id='test',
                                     aws_secret_access_key='test', region_name='eu-central-1')

        cls.s3_client.create_bucket(Bucket=cls.__s3_bucket_name, CreateBucketConfiguration={'LocationConstraint': 'eu-central-1'})
        cls.s3_client.upload_file(os.path.join(cls.__test_path, 'lambda_function.zip'), cls.__s3_bucket_name, 'function.zip')

        cls.lambda_client = boto3.client('lambda', endpoint_url='http://localhost:4566', aws_access_key_id='test',
                                         aws_secret_access_key='test', region_name='eu-central-1')

        cls.rotation_function = cls.lambda_client.create_function(
            Code={
                'S3Bucket': cls.__s3_bucket_name,
                'S3Key': 'function.zip',
            },
            Description='Dummy function',
            FunctionName=cls.__function_name,
            Handler='lambda.handler',
            Publish=True,
            Role='arn:aws:iam::123456789012:role/lambda-role',
            Runtime='python3.10',
        )
        cls.lambda_client.add_permission(
            FunctionName=cls.__function_name,
            Action='lambda:InvokeFunction',
            StatementId='1',
            Principal='secretsmanager.amazonaws.com',
        )

        secret = cls.secretsmanager.create_secret(
            Name=cls.__secret_name_with_rotation
        )
        cls.secretsmanager.put_secret_value(
            SecretId=cls.__secret_name_with_rotation,
            SecretString=secret_value_with_rotation.model_dump_json()
        )

        cls.secretsmanager.rotate_secret(
            SecretId=secret['ARN'],
            RotationLambdaARN=cls.rotation_function['FunctionArn'],
            RotationRules={
                'AutomaticallyAfterDays': 123,
                'Duration': '3h',
                'ScheduleExpression': 'rate(10 days)'
            }
        )

    def setUp(self):
        self.password_service = AwsSecretsManagerService(TestPasswordRotationApplicationInfra.secretsmanager, Mock(spec=Logger))
        self.database_service = PostgreSqlDatabaseService(Mock(spec=Logger))

    def test_should_create_new_password_when_rotate_secret_given_rotation_step_is_create_secret(self):
        # given
        given_token = f'{uuid.uuid4()}'
        given_secret_name = f'secret_with_rotation_{uuid.uuid4()}'
        given_current_value = DatabaseCredentials(username='admin', password='admin', database_host='localhost', database_port=5432, database_name='test')
        given_application = PasswordRotationApplication(self.password_service, self.database_service, Mock(spec=Logger))

        TestPasswordRotationApplicationInfra.__create_secret(given_secret_name, given_current_value, given_token, None)

        # when
        actual_result = given_application.rotate_secret(RotationStep.CREATE_SECRET, given_secret_name, given_token)
        actual_pending_value = TestPasswordRotationApplicationInfra.secretsmanager.get_secret_value(SecretId=given_secret_name, VersionStage='AWSPENDING', VersionId=given_token)

        # then
        self.assertEqual(actual_result, PasswordRotationResult.STEP_EXECUTED)
        self.assertNotEqual(DatabaseCredentials.model_validate_json(actual_pending_value['SecretString']).password, given_current_value.password)

    def test_should_add_pending_credentials_when_rotate_secret_given_rotation_step_is_create_secret(self):
        # given
        given_token = f'{uuid.uuid4()}'
        given_secret_name = f'secret_with_rotation_{uuid.uuid4()}'
        given_current_value = DatabaseCredentials(username='admin1', password='admin', database_host='localhost', database_port=5432, database_name='test')
        given_application = PasswordRotationApplication(self.password_service, self.database_service, Mock(spec=Logger))

        TestPasswordRotationApplicationInfra.__create_secret(given_secret_name, given_current_value, given_token, None)

        # when
        given_application.rotate_secret(RotationStep.CREATE_SECRET, given_secret_name, given_token)

        # then
        try:
            TestPasswordRotationApplicationInfra.secretsmanager.get_secret_value(SecretId=given_secret_name, VersionStage='AWSPENDING', VersionId=given_token)
        except TestPasswordRotationApplicationInfra.secretsmanager.exceptions.ResourceNotFoundException:
            self.fail("AWSPENDING version not found for secret: {}".format(given_secret_name))

    def test_should_return_nothing_to_rotate_when_rotate_secret_given_rotation_step_is_finish_secret(self):
        # given
        given_application = PasswordRotationApplication(self.password_service, self.database_service, Mock(spec=Logger))

        # when
        actual_result = given_application.rotate_secret(RotationStep.CREATE_SECRET, TestPasswordRotationApplicationInfra.__secret_name_without_rotation, f'{uuid.uuid4()}')

        # then
        assert actual_result == PasswordRotationResult.NOTHING_TO_ROTATE

    def test_should_use_another_username_when_rotate_secret_given_multi_user_rotation(self):
        # given
        given_token = f'{uuid.uuid4()}'
        given_secret_name = f'secret_with_rotation_{uuid.uuid4()}'
        given_current_value = DatabaseCredentials(username='admin1', password='admin', database_host='localhost', database_port=5432, database_name='test')
        given_application = PasswordRotationApplication(self.password_service, self.database_service, Mock(spec=Logger))

        TestPasswordRotationApplicationInfra.__create_secret(given_secret_name, given_current_value, given_token, None)

        # when
        actual_result = given_application.rotate_secret(RotationStep.CREATE_SECRET, given_secret_name, given_token)
        actual_pending_value = TestPasswordRotationApplicationInfra.secretsmanager.get_secret_value(SecretId=given_secret_name, VersionStage='AWSPENDING', VersionId=given_token)

        # then
        self.assertEqual(actual_result, PasswordRotationResult.STEP_EXECUTED)
        self.assertEqual(DatabaseCredentials.model_validate_json(actual_pending_value['SecretString']).username, "admin2")

    def test_should_raise_exception_when_rotate_secret_given_user_credentials_are_invalid_in_test_secret(self):
        # given
        given_token = f'{uuid.uuid4()}'
        given_secret_name = f'secret_with_rotation_{uuid.uuid4()}'
        given_current_value = DatabaseCredentials(username='admin', password='admin', database_host='localhost', database_port=5432, database_name='test')
        given_pending_value = DatabaseCredentials(username='admin2', password='admin2', database_host='localhost', database_port=5432, database_name='test')
        given_application = PasswordRotationApplication(self.password_service, self.database_service, Mock(spec=Logger))

        TestPasswordRotationApplicationInfra.__create_secret(given_secret_name, given_current_value, given_token, given_pending_value)

        # when / then
        with self.assertRaises(psycopg.OperationalError):
            given_application.rotate_secret(RotationStep.TEST_SECRET, given_secret_name, given_token)

    def test_should_use_pending_credentials_for_connection_check_when_rotate_secret_given_step_is_test_secret(self):
        # given
        given_token = f'{uuid.uuid4()}'
        given_secret_name = f'secret_with_rotation_{uuid.uuid4()}'
        given_current_value = DatabaseCredentials(username='admin', password='admin', database_host='localhost', database_port=5432, database_name='test')
        given_pending_value = DatabaseCredentials(username='admin2', password='admin2', database_host='localhost', database_port=5432, database_name='test')
        given_application = PasswordRotationApplication(self.password_service, self.database_service, Mock(spec=Logger))

        TestPasswordRotationApplicationInfra.__create_secret(given_secret_name, given_current_value, given_token, given_pending_value)

        # when / then
        with self.assertRaises(psycopg.OperationalError) as context:
            given_application.rotate_secret(RotationStep.TEST_SECRET, given_secret_name, given_token)

        self.assertIn('failed for user "admin2"', str(context.exception))

    @classmethod
    def __create_secret(cls, name: str, current_value: DatabaseCredentials, token: str, pending_value: DatabaseCredentials):
        secret = cls.secretsmanager.create_secret(
            Name=name
        )

        cls.secretsmanager.put_secret_value(
            SecretId=name,
            SecretString=current_value.model_dump_json(),
            VersionStages=['AWSCURRENT']
        )

        rotation_function = cls.lambda_client.create_function(
            Code={
                'S3Bucket': cls.__s3_bucket_name,
                'S3Key': 'function.zip',
            },
            Description='Dummy function',
            FunctionName=f'{cls.__function_name}_{random.randint(1, 999999999)}',
            Handler='lambda.handler',
            Publish=True,
            Role='arn:aws:iam::123456789012:role/lambda-role',
            Runtime='python3.10',
        )

        cls.secretsmanager.rotate_secret(
            SecretId=secret['ARN'],
            RotationLambdaARN=rotation_function['FunctionArn'],
            RotationRules={
                'AutomaticallyAfterDays': 123,
                'Duration': '3h',
                'ScheduleExpression': 'rate(10 days)'
            }
        )

        if pending_value:
            cls.secretsmanager.put_secret_value(
                SecretId=name,
                SecretString=pending_value.model_dump_json(),
                VersionStages=['AWSPENDING'], ClientRequestToken=token
            )
