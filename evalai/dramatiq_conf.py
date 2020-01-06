import dramatiq

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
    endpoint_url="http://127.0.0.1:9324",
    region_name="elasticmq",
    aws_access_key_id="x",
    aws_secret_access_key="x",
)
dramatiq.set_broker(broker)
