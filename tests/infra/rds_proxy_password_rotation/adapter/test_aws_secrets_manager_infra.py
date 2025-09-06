import json
import uuid
from unittest import TestCase
from unittest.mock import Mock

import boto3
import os

from aws_lambda_powertools import Logger

from rds_proxy_password_rotation.adapter.aws_secrets_manager import AwsSecretsManagerService
from rds_proxy_password_rotation.model import PasswordStage, DatabaseCredentials, PasswordType


class TestAwsSecretsManagerService(TestCase):
    __secret_name_without_rotation = f'secret_without_rotation_enabled_{uuid.uuid4()}'
    __secret_name_with_rotation = f'secret_with_rotation_enabled_{uuid.uuid4()}'
    __secret_name_with_missing_fields = f'secret_with_missing_fields_{uuid.uuid4()}'
    __secret_name_with_additional_fields = f'secret_with_additional_fields_{uuid.uuid4()}'

    __s3_bucket_name = f'my-bucket-{uuid.uuid4()}'
    __function_name = f'rotation--{uuid.uuid4()}'

    __test_path = os.path.join(os.path.dirname(__file__), '..', '..', '..')

    @classmethod
    def setUpClass(cls):
        secret_value_without_rotation = DatabaseCredentials(username='admin', password='admin', database_host='localhost', database_port=5432, database_name='test', rotation_type=PasswordType.AWS_RDS)

        secret_value_with_rotation = DatabaseCredentials(username='admin1', password='admin', database_host='localhost', database_port=5432, database_name='test', rotation_type=PasswordType.AWS_RDS)

        additional_fields_secret_value = {
            "username": "admin",
            "password": "admin",
            "database_host": "localhost",
            "database_port": 5432,
            "database_name": "test",
            "some_field": "some_value"
        }

        missing_mandatory_fields_secret_value = {
            "x": "admin",
            "y": "admin"
        }

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

        # secret with missing fields
        cls.secretsmanager.create_secret(
            Name=cls.__secret_name_with_missing_fields
        )
        cls.secretsmanager.put_secret_value(
            SecretId=cls.__secret_name_with_missing_fields,
            SecretString=json.dumps(missing_mandatory_fields_secret_value)
        )

        # secret with additional fields
        cls.secretsmanager.create_secret(
            Name=cls.__secret_name_with_additional_fields
        )
        cls.secretsmanager.put_secret_value(
            SecretId=cls.__secret_name_with_additional_fields,
            SecretString=json.dumps(additional_fields_secret_value)
        )

        # secret with rotation
        cls.s3_client = boto3.client('s3', endpoint_url='http://localhost:4566', aws_access_key_id='test',
                                     aws_secret_access_key='test', region_name='eu-central-1')

        cls.s3_client.create_bucket(Bucket=cls.__s3_bucket_name, CreateBucketConfiguration={'LocationConstraint': 'eu-central-1'})
        cls.s3_client.upload_file(os.path.join(cls.__test_path, 'lambda_function.zip'), cls.__s3_bucket_name, 'function.zip')

        cls.lambda_client = boto3.client('lambda', endpoint_url='http://localhost:4566', aws_access_key_id='test',
                                         aws_secret_access_key='test', region_name='eu-central-1')

        rotation_function = cls.lambda_client.create_function(
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
        cls.secretsmanager.delete_secret(
            SecretId=cls.__secret_name_with_missing_fields,
        )
        cls.secretsmanager.delete_secret(
            SecretId=cls.__secret_name_with_additional_fields,
        )

        cls.lambda_client.delete_function(FunctionName=cls.__function_name)

        cls.s3_client.delete_object(Bucket=cls.__s3_bucket_name, Key='function.zip')
        cls.s3_client.delete_bucket(Bucket=cls.__s3_bucket_name)

    def test_should_change_the_password_when_set_new_pending_password_given_secret_exists(self):
        # Given
        credentials = DatabaseCredentials(username='admin', password='admin', database_host='localhost', database_port=5432, database_name='test', rotation_type=PasswordType.AWS_RDS)
        token = str(uuid.uuid4())
        credential_name = str(uuid.uuid4())

        self.secretsmanager.create_secret(
            Name=credential_name
        )
        self.secretsmanager.put_secret_value(
            SecretId=credential_name,
            SecretString=credentials.model_dump_json()
        )

        # When
        AwsSecretsManagerService(self.secretsmanager, Mock(spec=Logger)).set_new_pending_password(
            self.__secret_name_with_additional_fields, token, credentials)

        # Then
        secret = self.secretsmanager.get_secret_value(SecretId=self.__secret_name_with_additional_fields, VersionStage='AWSPENDING', VersionId=token)

        self.assertIsNotNone(secret)
        self.assertNotEqual(json.loads(secret['SecretString'])['password'], credentials.password)

    def test_should_not_touch_additional_fields_when_set_new_pending_password_given_secret_exists(self):
        # Given
        credentials = DatabaseCredentials(username='admin', password='admin', database_host='localhost', database_port=5432, database_name='test', some_field='some_value', rotation_type=PasswordType.AWS_RDS)
        token = str(uuid.uuid4())
        credential_name = str(uuid.uuid4())

        self.secretsmanager.create_secret(
            Name=credential_name
        )
        self.secretsmanager.put_secret_value(
            SecretId=credential_name,
            SecretString=credentials.model_dump_json()
        )

        # When
        AwsSecretsManagerService(self.secretsmanager, Mock(spec=Logger)).set_new_pending_password(
            self.__secret_name_with_additional_fields, token, credentials)

        # Then
        secret = self.secretsmanager.get_secret_value(SecretId=self.__secret_name_with_additional_fields, VersionStage='AWSPENDING', VersionId=token)

        self.assertIsNotNone(secret)

        self.assertEqual(json.loads(secret['SecretString']), json.loads(secret['SecretString']) | {"some_field": "some_value"})

    def test_should_set_new_pending_password_when_set_new_pending_password_given_secret_exists(self):
        # Given
        credentials = DatabaseCredentials(username='admin', password='admin', database_host='localhost', database_port=5432, database_name='test', rotation_type=PasswordType.AWS_RDS)
        token = str(uuid.uuid4())
        credential_name = str(uuid.uuid4())

        self.secretsmanager.create_secret(
            Name=credential_name
        )
        self.secretsmanager.put_secret_value(
            SecretId=credential_name,
            SecretString=credentials.model_dump_json()
        )

        # When
        AwsSecretsManagerService(self.secretsmanager, Mock(spec=Logger)).set_new_pending_password(
            self.__secret_name_without_rotation, token,credentials)

        # Then
        secret = self.secretsmanager.get_secret_value(SecretId=self.__secret_name_without_rotation, VersionStage='AWSPENDING', VersionId=token)

        self.assertIsNotNone(secret)

    def test_should_return_database_credentials_when_get_database_credentials_given_secret_exists(self):
        # Given

        # When
        result = AwsSecretsManagerService(self.secretsmanager, Mock(spec=Logger)).get_database_credentials(
            self.__secret_name_without_rotation, PasswordStage.CURRENT)

        # Then
        self.assertEqual(result.username, 'admin')
        self.assertEqual(result.password, 'admin')

    def test_should_throw_validation_exception_when_get_database_credentials_given_missing_mandatory_fields(self):
        # Given

        # When
        with self.assertRaises(ValueError):
            AwsSecretsManagerService(self.secretsmanager, Mock(spec=Logger)).get_database_credentials(
                self.__secret_name_with_missing_fields, PasswordStage.CURRENT)

    def test_should_return_none_when_get_database_credentials_given_secret_does_not_exist(self):
        # Given

        # When
        result = AwsSecretsManagerService(self.secretsmanager, Mock(spec=Logger)).get_database_credentials(
            'non_existing_secret', PasswordStage.CURRENT)

        # Then
        self.assertIsNone(result)

    def test_should_return_user_credentials_when_get_user_credentials_given_secret_exists(self):
        # Given

        # When
        result = AwsSecretsManagerService(self.secretsmanager, Mock(spec=Logger)).get_user_credentials(
            self.__secret_name_without_rotation, PasswordStage.CURRENT)

        # Then
        self.assertEqual(result.username, 'admin')
        self.assertEqual(result.password, 'admin')

    def test_should_throw_validation_exception_when_get_user_credentials_given_missing_mandatory_fields(self):
        # Given

        # When
        with self.assertRaises(ValueError):
            AwsSecretsManagerService(self.secretsmanager, Mock(spec=Logger)).get_user_credentials(
                self.__secret_name_with_missing_fields, PasswordStage.CURRENT)

    def test_should_return_none_when_get_user_credentials_given_secret_does_not_exist(self):
        # Given

        # When
        result = AwsSecretsManagerService(self.secretsmanager, Mock(spec=Logger)).get_user_credentials(
            'non_existing_secret', PasswordStage.CURRENT)

        # Then
        self.assertIsNone(result)

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

    def test_should_update_the_secret_when_set_credentials_given_secret_exists(self):
        # Given
        credentials = DatabaseCredentials(username='xxx', password='admin', database_host='localhost', database_port=5432, database_name='test', rotation_type=PasswordType.AWS_RDS)
        token = str(uuid.uuid4())
        credential_name = str(uuid.uuid4())

        self.secretsmanager.create_secret(
            Name=credential_name
        )
        self.secretsmanager.put_secret_value(
            SecretId=credential_name,
            SecretString=credentials.model_dump_json()
        )

        # When
        AwsSecretsManagerService(self.secretsmanager, Mock(spec=Logger)).set_credentials(
            credential_name, token, credentials.model_copy(update={'password': 'new_password'}))

        # Then
        secret = self.secretsmanager.get_secret_value(SecretId=credential_name, VersionStage='AWSCURRENT', VersionId=token)

        self.assertIsNotNone(secret)
        self.assertEqual(DatabaseCredentials.model_validate_json(secret['SecretString']).password, 'new_password')

    def test_should_not_change_current_credentials_when_make_new_credentials_current_given_new_credentials_are_already_current(self):
        # Given
        current_credentials = DatabaseCredentials(username='admin', password='admin', database_host='localhost', database_port=5432, database_name='test', rotation_type=PasswordType.AWS_RDS)
        pending_credentials = DatabaseCredentials(username='admin2', password='admin2', database_host='localhost', database_port=5432, database_name='test', rotation_type=PasswordType.AWS_RDS)
        token = str(uuid.uuid4())
        credential_name = str(uuid.uuid4())

        self.secretsmanager.create_secret(
            Name=credential_name
        )
        self.secretsmanager.put_secret_value(
            SecretId=credential_name,
            SecretString=current_credentials.model_dump_json(),
            ClientRequestToken=token
        )
        self.secretsmanager.put_secret_value(
            SecretId=credential_name,
            SecretString=pending_credentials.model_dump_json(),
            ClientRequestToken=str(uuid.uuid4()),
            VersionStages=['AWSPENDING']
        )

        # When
        AwsSecretsManagerService(self.secretsmanager, Mock(spec=Logger)).make_new_credentials_current(
            credential_name, token)

        # Then
        secret = self.secretsmanager.get_secret_value(SecretId=credential_name, VersionStage='AWSCURRENT')

        self.assertIsNotNone(secret)
        self.assertEqual(DatabaseCredentials.model_validate_json(secret['SecretString']).password, 'admin')

    def test_should_make_new_credentials_current_when_make_new_credentials_current_given_new_credentials_are_not_current(self):
        # Given
        current_credentials = DatabaseCredentials(username='admin', password='admin', database_host='localhost', database_port=5432, database_name='test', rotation_type=PasswordType.AWS_RDS)
        pending_credentials = DatabaseCredentials(username='admin', password='admin2', database_host='localhost', database_port=5432, database_name='test', rotation_type=PasswordType.AWS_RDS)
        token = str(uuid.uuid4())
        credential_name = str(uuid.uuid4())

        self.secretsmanager.create_secret(
            Name=credential_name
        )
        self.secretsmanager.put_secret_value(
            SecretId=credential_name,
            SecretString=current_credentials.model_dump_json(),
            ClientRequestToken=str(uuid.uuid4())
        )
        self.secretsmanager.put_secret_value(
            SecretId=credential_name,
            SecretString=pending_credentials.model_dump_json(),
            ClientRequestToken=token,
            VersionStages=['AWSPENDING']
        )

        # When
        AwsSecretsManagerService(self.secretsmanager, Mock(spec=Logger)).make_new_credentials_current(
            credential_name, token)

        # Then
        secret = self.secretsmanager.get_secret_value(SecretId=credential_name, VersionStage='AWSCURRENT')

        self.assertIsNotNone(secret)
        self.assertEqual(DatabaseCredentials.model_validate_json(secret['SecretString']).password, 'admin2')

    def test_should_have_one_current_with_correct_token_when_make_new_credentials_current_given_rotation_takes_place(self):
        # Given
        current_credentials = DatabaseCredentials(username='admin', password='admin', database_host='localhost', database_port=5432, database_name='test', rotation_type=PasswordType.AWS_RDS)
        pending_credentials = DatabaseCredentials(username='admin', password='admin2', database_host='localhost', database_port=5432, database_name='test', rotation_type=PasswordType.AWS_RDS)
        token = str(uuid.uuid4())
        credential_name = str(uuid.uuid4())

        self.secretsmanager.create_secret(
            Name=credential_name
        )
        self.secretsmanager.put_secret_value(
            SecretId=credential_name,
            SecretString=current_credentials.model_dump_json(),
            ClientRequestToken=str(uuid.uuid4())
        )
        self.secretsmanager.put_secret_value(
            SecretId=credential_name,
            SecretString=pending_credentials.model_dump_json(),
            ClientRequestToken=token,
            VersionStages=['AWSPENDING']
        )

        # When
        AwsSecretsManagerService(self.secretsmanager, Mock(spec=Logger)).make_new_credentials_current(
            credential_name, token)

        # Then
        metadata = self.secretsmanager.describe_secret(SecretId=credential_name)
        current_versions = [version for version, stages in metadata['VersionIdsToStages'].items() if 'AWSCURRENT' in stages]

        self.assertEqual(len(current_versions), 1)
        self.assertEqual(current_versions[0], token)

    def test_should_have_one_previous_with_correct_token_when_make_new_credentials_current_given_rotation_takes_place(self):
        # Given
        current_credentials = DatabaseCredentials(username='admin', password='admin', database_host='localhost', database_port=5432, database_name='test', rotation_type=PasswordType.AWS_RDS)
        pending_credentials = DatabaseCredentials(username='admin2', password='admin2', database_host='localhost', database_port=5432, database_name='test', rotation_type=PasswordType.AWS_RDS)
        previous_credentials = DatabaseCredentials(username='adminPrev', password='adminPrev', database_host='localhost', database_port=5432, database_name='test', rotation_type=PasswordType.AWS_RDS)
        token = str(uuid.uuid4())
        credential_name = str(uuid.uuid4())

        self.secretsmanager.create_secret(
            Name=credential_name
        )
        self.secretsmanager.put_secret_value(
            SecretId=credential_name,
            SecretString=current_credentials.model_dump_json(),
            ClientRequestToken=str(uuid.uuid4())
        )
        self.secretsmanager.put_secret_value(
            SecretId=credential_name,
            SecretString=pending_credentials.model_dump_json(),
            ClientRequestToken=token,
            VersionStages=['AWSPENDING']
        )
        self.secretsmanager.put_secret_value(
            SecretId=credential_name,
            SecretString=previous_credentials.model_dump_json(),
            ClientRequestToken=str(uuid.uuid4()),
            VersionStages=['AWSPREVIOUS']
        )

        # When
        AwsSecretsManagerService(self.secretsmanager, Mock(spec=Logger)).make_new_credentials_current(
            credential_name, token)

        # Then
        metadata = self.secretsmanager.describe_secret(SecretId=credential_name)
        previous_versions = [version for version, stages in metadata['VersionIdsToStages'].items() if 'AWSPREVIOUS' in stages]

        self.assertEqual(len(previous_versions), 1)
        self.assertNotEqual(previous_versions[0], token)
