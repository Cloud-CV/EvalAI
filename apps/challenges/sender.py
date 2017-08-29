import json
import pika


def publish_challenge_edit_message(challenge_id):

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.exchange_declare(exchange='evalai_submissions', type='topic')

    channel.queue_declare(queue='challenge_edit_queue', durable=True)

    message = {
        'challenge_id': challenge_id,
    }
    channel.basic_publish(exchange='evalai_submissions',
                          routing_key='challenge.edit.*',
                          body=json.dumps(message),
                          properties=pika.BasicProperties(delivery_mode=2))

    print(" [x] Sent %r" % message)
    connection.close()
