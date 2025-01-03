from pydantic import BaseModel, Field


class AwsSecretManagerRotationEvent(BaseModel):
    step: str = Field(alias='Step')
    secretId: str = Field(alias='SecretId')
    clientRequestToken: str = Field(alias='ClientRequestToken')
    rotationToken: str = Field(alias='RotationToken')
