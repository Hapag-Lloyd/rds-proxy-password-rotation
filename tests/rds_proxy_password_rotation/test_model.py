import json
from unittest import TestCase

from rds_proxy_password_rotation.model import DatabaseCredentials


class TestDatabaseCredentials(TestCase):
    def test_should_allow_extra_fields(self):
        # Given
        data = {
            "username": "admin",
            "password": "admin",
            "extra_field": "extra_value"
        }

        # When
        credentials = DatabaseCredentials.model_validate_json(json.dumps(data))

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
