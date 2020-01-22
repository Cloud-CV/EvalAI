import time
from unittest import TestCase

import dramatiq
from moto import mock_sqs

from evalai.dramatiq_conf import broker

dramatiq.set_broker(broker)


class TestDramatiqWorker(TestCase):

    @classmethod
    def setUpClass(cls):
        worker = dramatiq.Worker(broker)
        worker.start()

    def setUp(self):
        self.db = []  # Dummy database to perform operations
        self.n_messages = 3
        self.dummy_data = {"test_field": "test_data"}
        self.queue_name = "default"
        self.dummy_task = dramatiq.actor(self.dummy_method, queue_name=self.queue_name)

    def dummy_method(self, data):
        self.db.append(data)
        print("Task completed")
        print(self.db)

    def test_enqueue_and_process_message(self):
        message = self.dummy_task.send(self.dummy_data)

        # wait for task to complete
        time.sleep(1)

        # verify that message was sent to correct queue
        self.assertEqual(message.queue_name, self.queue_name)

        # verify task success
        self.assertEqual(self.db, [self.dummy_data])

    def test_enqueue_and_process_multiple_messages(self):
        data_list = [i for i in range(self.n_messages)]

        @dramatiq.actor(queue_name=self.queue_name)
        def dummy_method(data):
            self.db.append(data)

        messages = [self.dummy_task.send(data) for data in data_list]
        time.sleep(2)  # wait for task to finish

        # verify all messages are sent to correct queue
        for message in messages:
            self.assertEqual(message.queue_name, self.queue_name)

        # verify task completion
        self.assertEqual(self.db, data_list)
