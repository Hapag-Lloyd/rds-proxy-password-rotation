import json
from unittest import TestCase

from rds_proxy_password_rotation.model import DatabaseCredentials, UserCredentials, Credentials


class TestCredentials(TestCase):
    def test_should_allow_extra_fields(self):
        # Given
        data = {
            "rotation_type": "AWS RDS",
            "extra_field": "extra_value"
        }

        # When
        credentials = Credentials.model_validate_json(json.dumps(data))

        # Then
        self.assertEqual(credentials.extra_field, "extra_value")


class TestDatabaseCredentials(TestCase):
    def test_should_allow_extra_fields(self):
        # Given
        data = {
            "username": "admin",
            "password": "admin",
            "database_host": "localhost",
            "database_port": 5432,
            "database_name": "test",
            "rotation_type": "AWS RDS",
            "extra_field": "extra_value"
        }

        # When
        credentials = DatabaseCredentials.model_validate_json(json.dumps(data))

        # Then
        self.assertEqual(credentials.username, "admin")
        self.assertEqual(credentials.password, "admin")
        self.assertEqual(credentials.extra_field, "extra_value")


class TestUserCredentials(TestCase):
    def test_should_allow_extra_fields(self):
        # Given
        data = {
            "rotation_type": "AWS RDS",
            "username": "admin",
            "password": "admin",
            "extra_field": "extra_value"
        }

        # When
        credentials = UserCredentials.model_validate_json(json.dumps(data))

        # Then
        self.assertEqual(credentials.username, "admin")
        self.assertEqual(credentials.password, "admin")
        self.assertEqual(credentials.extra_field, "extra_value")

    def test_should_throw_value_error_if_username_is_missing(self):
        # Given
        data = {
            "password": "admin",
        }

        # When
        with self.assertRaises(ValueError) as actualContext:
            DatabaseCredentials.model_validate_json(json.dumps(data))

        # Then
        self.assertIn("username", str(actualContext.exception))

    def test_should_throw_value_error_if_password_is_missing(self):
        # Given
        data = {
            "username": "admin",
        }

        # When
        with self.assertRaises(ValueError) as actualContext:
            DatabaseCredentials.model_validate_json(json.dumps(data))

        # Then
        self.assertIn("password", str(actualContext.exception))

    def test_should_return_user2_when_get_next_username_given_user1_is_current(self):
        # Given
        data = {
            "rotation_type": "AWS RDS",
            "username": "user1",
            "password": "admin",
            "database_host": "localhost",
            "database_port": 5432,
            "database_name": "test"
        }

        # When
        result = DatabaseCredentials.model_validate_json(json.dumps(data)).get_next_username()

        # Then
        self.assertEqual(result, 'user2')

    def test_should_return_user1_when_get_next_username_given_user2_is_current(self):
        # Given
        data = {
            "rotation_type": "AWS RDS",
            "username": "user2",
            "password": "admin",
            "database_host": "localhost",
            "database_port": 5432,
            "database_name": "test"
        }

        # When
        result = DatabaseCredentials.model_validate_json(json.dumps(data)).get_next_username()

        # Then
        self.assertEqual(result, 'user1')

    def test_should_return_the_same_username_when_get_next_username_given_single_user_rotation(self):
        # Given
        data = {
            "rotation_type": "AWS RDS",
            "username": "user",
            "password": "admin",
            "database_host": "localhost",
            "database_port": 5432,
            "database_name": "test"
        }

        # When
        result = DatabaseCredentials.model_validate_json(json.dumps(data)).get_next_username()

        # Then
        self.assertEqual(result, 'user3')
