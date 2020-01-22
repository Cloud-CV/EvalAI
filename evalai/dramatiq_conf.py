import dramatiq
import os

from dramatiq.middleware import AgeLimit, TimeLimit, Callbacks, Pipelines, Prometheus, Retries
from dramatiq_sqs import SQSBroker


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
    endpoint_url=os.environ.get("AWS_SQS_ENDPOINT_URL", "http://localhost:9324"),
    region_name=os.environ.get("AWS_DEFAULT_REGION", "elasticmq"),
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "x"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "x"),
)
dramatiq.set_broker(broker)
