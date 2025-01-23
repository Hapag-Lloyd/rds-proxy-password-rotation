import json
from unittest import TestCase

from rds_proxy_password_rotation.model import DatabaseCredentials, UserCredentials


class TestDatabaseCredentials(TestCase):
    def test_should_allow_extra_fields(self):
        # Given
        data = {
            "username": "admin",
            "password": "admin",
            "database_host": "localhost",
            "database_port": 5432,
            "database_name": "test",
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
