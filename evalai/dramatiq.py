import os

from dramatiq.middleware import AgeLimit, TimeLimit, Callbacks, Pipelines, Prometheus, Retries
from dramatiq_sqs import SQSBroker

AWS_SQS_ENDPOINT = os.environ.get('AWS_SQS_ENDPOINT', 'http://127.0.0.1:9324')
AWS_SQS_REGION = os.environ.get('AWS_SQS_REGION', 'us-east-1')

broker = SQSBroker(
    namespace="dramatiq_sqs_tests",
    middleware=[
        Prometheus(),
        AgeLimit(),
        TimeLimit(),
        Callbacks(),
        Pipelines(),
        Retries(min_backoff=1000, max_backoff=900000, max_retries=96),
    ],
    endpoint_url=AWS_SQS_ENDPOINT,
    region_name=AWS_SQS_REGION,
)
