#!/usr/bin/env python
from __future__ import absolute_import
import os
import pika
import importlib
import requests
import zipfile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.dev')

import django
django.setup()

from os.path import join

from django.conf import settings
from django.utils import timezone

from challenges.models import Challenge

from load_challenges import (load_active_challenges,)

# close old database conenctions so that it should not timeout
django.db.close_old_connections()

# global dictionary
EVALUATION_SCRIPTS = {}

############ RABBITMQ SETTINGS START #######################

# pika connection object 
connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='task_queue', durable=True)
print(' [*] Waiting for messages. To exit press CTRL+C')

############### RABBITMQ SETTINGS END ######################

load_active_challenges()

def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)
    ch.basic_ack(delivery_tag = method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback,
                      queue='task_queue')


channel.start_consuming()
