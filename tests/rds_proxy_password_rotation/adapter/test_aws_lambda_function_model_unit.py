from unittest import TestCase

from rds_proxy_password_rotation.adapter.aws_lambda_function_model import AwsRotationStep
from rds_proxy_password_rotation.model import RotationStep

class TestAwsRotationStep(TestCase):
    def test_should_return_rotation_step_when_to_rotation_step_given_create_secret(self):
        # Given

        # When
        rotation_step = AwsRotationStep.CREATE_SECRET.to_rotation_step()

        # Then
        self.assertEqual(rotation_step, RotationStep.CREATE_SECRET)

    def test_should_return_rotation_step_when_to_rotation_step_given_set_secret(self):
        # Given

        # When
        rotation_step = AwsRotationStep.SET_SECRET.to_rotation_step()

        # Then
        self.assertEqual(rotation_step, RotationStep.SET_SECRET)

    def test_should_return_rotation_step_when_to_rotation_step_given_test_secret(self):
        # Given

        # When
        rotation_step = AwsRotationStep.TEST_SECRET.to_rotation_step()

        # Then
        self.assertEqual(rotation_step, RotationStep.TEST_SECRET)

    def test_should_return_rotation_step_when_to_rotation_step_given_finish_secret(self):
        # Given

        # When
        rotation_step = AwsRotationStep.FINISH_SECRET.to_rotation_step()

        # Then
        self.assertEqual(rotation_step, RotationStep.FINISH_SECRET)
