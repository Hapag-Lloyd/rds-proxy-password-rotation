from pydantic import BaseModel, Field


class AwsSecretManagerRotationEvent(BaseModel):
    """
    Step – The rotation step: create_secret, set_secret, test_secret, or finish_secret. For more information, see Four steps in a rotation function.

    SecretId – The ARN of the secret to rotate.

    ClientRequestToken – A unique identifier for the new version of the secret. This value helps ensure idempotency. For more information, see PutSecretValue: ClientRequestToken in the AWS Secrets Manager API Reference.

    RotationToken – A unique identifier that indicates the source of the request. Required for secret rotation using an assumed role or cross-account rotation, in which you rotate a secret in one account by using a Lambda rotation function in another account. In both cases, the rotation function assumes an IAM role to call Secrets Manager and then Secrets Manager uses the rotation token to validate the IAM role identity.
    """
    step: str = Field(alias='Step')
    secretId: str = Field(alias='SecretId')
    clientRequestToken: str = Field(alias='ClientRequestToken')
    rotationToken: str = Field(alias='RotationToken')
