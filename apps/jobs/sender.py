from django.conf import settings

import json
import pika


def publish_submission_message(challenge_id, phase_id, submission_id):

    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=settings.RABBITMQ_PARAMETERS['HOST']))
    channel = connection.channel()
    channel.exchange_declare(exchange='evalai_submissions', type='direct')

    # though worker is creating the queue(queue creation is idempotent too)
    # but lets create the queue here again, so that messages dont get missed
    # later on we can apply a check on queue message length to raise some alert
    # this way we will be notified of worker being up or not
    channel.queue_declare(queue='submission_challenge_{}'.format(challenge_id), durable=True)

    message = {
        'challenge_id': challenge_id,
        'phase_id': phase_id,
        'submission_id': submission_id
    }

    channel.basic_publish(exchange='evalai_submissions',
                          routing_key='submission_challenge_{}'.format(challenge_id),
                          body=json.dumps(message),
                          properties=pika.BasicProperties(delivery_mode=2))    # make message persistent

    print(" [x] Sent %r" % message)
    connection.close()
