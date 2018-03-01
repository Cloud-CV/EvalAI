import json
import pika

from django.conf import settings

from tests.unit.submission_worker.fake_publisher import FakePublisher


def publish_submission_message(challenge_id, phase_id, submission_id):
    message = {
        'challenge_id': challenge_id,
        'phase_id': phase_id,
        'submission_id': submission_id
    }

    if settings.TESTING:
        """
        Fake sender for testing.
        """
        channel = FakePublisher()
        channel.basic_publish(exchange='evalai_submissions',
                              routing_key='submission.*.*',
                              body=json.dumps(message))
    else:
        connection = pika.BlockingConnection(pika.ConnectionParameters(
                host='localhost'))
        channel = connection.channel()
        channel.exchange_declare(exchange='evalai_submissions', type='topic')

        # though worker is creating the queue(queue creation is idempotent too)
        # but lets create the queue here again, so that messages dont get missed
        # later on we can apply a check on queue message length to raise some alert
        # this way we will be notified of worker being up or not
        channel.queue_declare(queue='submission_task_queue', durable=True)
        channel.basic_publish(exchange='evalai_submissions',
                              routing_key='submission.*.*',
                              body=json.dumps(message),
                              properties=pika.BasicProperties(delivery_mode=2))    # make message persistent

        print(" [x] Sent %r" % message)
        connection.close()
