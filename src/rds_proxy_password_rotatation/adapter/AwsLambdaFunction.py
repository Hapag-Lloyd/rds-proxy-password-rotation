from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.typing import LambdaContext

from adapter.AwsSecretManagerRotationEvent import AwsSecretManagerRotationEvent


@event_parser(model=AwsSecretManagerRotationEvent)
def lambda_handler(event: AwsSecretManagerRotationEvent, context: LambdaContext) -> None:
    print(event)
    print(context)

    return event
