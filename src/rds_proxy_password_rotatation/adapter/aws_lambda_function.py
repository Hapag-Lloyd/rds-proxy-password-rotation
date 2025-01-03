from enum import Enum
from pydantic import BaseModel, Field

from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.typing import LambdaContext


class RotationStep(Enum):
    CREATE_SECRET = "create_secret"
    SET_SECRET = "set_secret"
    TEST_SECRET = "test_secret"
    FINISH_SECRET = "finish_secret"


class AwsSecretManagerRotationEvent(BaseModel):
    """
    Step – The rotation step: create_secret, set_secret, test_secret, or finish_secret. For more information, see Four steps in a rotation function.

    SecretId – The ARN of the secret to rotate.

    ClientRequestToken – A unique identifier for the new version of the secret. This value helps ensure idempotency. For more information, see PutSecretValue: ClientRequestToken in the AWS Secrets Manager API Reference.

    RotationToken – A unique identifier that indicates the source of the request. Required for secret rotation using an assumed role or cross-account rotation, in which you rotate a secret in one account by using a Lambda rotation function in another account. In both cases, the rotation function assumes an IAM role to call Secrets Manager and then Secrets Manager uses the rotation token to validate the IAM role identity.
    """
    step: RotationStep = Field(alias='Step')
    secret_id: str = Field(alias='SecretId')
    client_request_token: str = Field(alias='ClientRequestToken')
    rotation_token: str = Field(alias='RotationToken')


@event_parser(model=AwsSecretManagerRotationEvent)
def lambda_handler(event: AwsSecretManagerRotationEvent, context: LambdaContext) -> None:
    print(event)
    print(context)

    return event
