from scripts.workers.submission_worker import (test_add_challenge_callback, test_process_submission_callback)

class FakePublisher(object):
    
    consumer_endpoints = {
                            "submission.*.*": test_process_submission_callback,
                            "challenge.*.*": test_add_challenge_callback,
                         }

    def __init__(self):
        pass

    def call_consumer(self, msg):
        pass

    def basic_publish(self, exchange, routing_key, body):

        """
        Invoking Submission Worker from here.
        """
        try:
            endpoint = self.consumer_endpoints[routing_key]
            endpoint(body)
        except Exception as e:
            raise e
