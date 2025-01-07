from unittest import TestCase

from rds_proxy_password_rotatation.model import RotationStep
from rds_proxy_password_rotatation.adapter.aws_lambda_function import AwsRotationStep

class TestAwsRotationStep(TestCase):
    def test_should_return_rotation_step_when_to_rotation_step_given_create_secret(self):
        # Given

        # When
        rotation_step = AwsRotationStep.to_rotation_step("create_secret")

        # Then
        self.assertEqual(rotation_step, RotationStep.CREATE_SECRET)

    def test_should_return_rotation_step_when_to_rotation_step_given_set_secret(self):
        # Given

        # When
        rotation_step = AwsRotationStep.to_rotation_step("set_secret")

        # Then
        self.assertEqual(rotation_step, RotationStep.SET_SECRET)

    def test_should_return_rotation_step_when_to_rotation_step_given_test_secret(self):
        # Given

        # When
        rotation_step = AwsRotationStep.to_rotation_step("test_secret")

        # Then
        self.assertEqual(rotation_step, RotationStep.TEST_SECRET)

    def test_should_return_rotation_step_when_to_rotation_step_given_finish_secret(self):
        # Given

        # When
        rotation_step = AwsRotationStep.to_rotation_step("finish_secret")

        # Then
        self.assertEqual(rotation_step, RotationStep.FINISH_SECRET)

    def test_should_raise_value_error_when_to_rotation_step_given_invalid_step(self):
        # Given

        # When
        with self.assertRaises(ValueError):
            AwsRotationStep.to_rotation_step("invalid_step")
