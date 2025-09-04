import pytest


@pytest.fixture(autouse=True)
def setup_boto3():
    import os
    os.environ['AWS_DEFAULT_REGION'] = 'eu-central-1'
