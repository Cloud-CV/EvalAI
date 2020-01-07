import dramatiq
import os

from dramatiq.middleware import AgeLimit, TimeLimit, Callbacks, Pipelines, Prometheus, Retries
from dramatiq_sqs import SQSBroker


if os.environ.get('IN_DOCKER'):
    endpoint_url = "http://sqs:9324"
else:
    endpoint_url = "http://localhost:9324"

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
    endpoint_url=endpoint_url,
    region_name="elasticmq",
    aws_access_key_id="x",
    aws_secret_access_key="x",
)
dramatiq.set_broker(broker)
