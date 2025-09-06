import requests

from rds_proxy_password_rotation.adapter.aws_lambda_function_model import AwsSecretManagerRotationEvent


def execute_api_call(request: AwsSecretManagerRotationEvent) -> requests.Response:
    url = "http://localhost:9000/2015-03-31/functions/function/invocations"
    response = requests.post(url, json=request)

    return response

def test_alive():
    # given
    # Create a sample AwsSecretManagerRotationEvent
    given_event = {
        "xxx": "yyy"
    }

    # when
    actual_response = execute_api_call(given_event)

    # then
    assert actual_response.status_code == 200
