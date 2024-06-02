
import os
import pytz
import warnings

from datetime import datetime
from dateutil.parser import parse
from auto_stop_workers import start_worker, stop_worker
from evalai_interface import EvalAI_Interface

warnings.filterwarnings("ignore")

utc = pytz.UTC

ENV = os.environ.get("ENV", "dev")

evalai_endpoint = os.environ.get("API_HOST_URL")
auth_token = os.environ.get("AUTH_TOKEN")




def scale_down_workers(challenge, num_workers):
    if num_workers > 0:
        response = stop_worker(challenge_id=challenge["id"])
        print("AWS API Response: {}".format(response))
        print(
            "Stopped worker for Challenge ID: {}, Title: {}".format(
                challenge["id"], challenge["title"]
            )
        )
    
    else:
        print(
            "No workers and pending messages found for Challenge ID: {}, Title: {}. Skipping.".format(
                challenge["id"], challenge["title"]
            )
        )



def scale_down_workers_for_challenges(evalai_interface, response):
    for challenge in response["results"]:
        try:
            # this is the most important line
            if challenge["evaluation_module_error"] is not None:  
                num_workers = (0 if challenge["workers"] is None else int(challenge["workers"]))
                print("number of workers", num_workers)

                scale_down_workers(challenge, num_workers)
        except Exception as e:
            print(e)

def create_evalai_interface(auth_token, evalai_endpoint):
    evalai_interface = EvalAI_Interface(auth_token, evalai_endpoint)
    return evalai_interface

def start():
    evalai_interface = create_evalai_interface(auth_token, evalai_endpoint)
    response = evalai_interface.get_challenges()

    scale_down_workers_for_challenges(evalai_interface, response)
if __name__ == "__main__":
    pass
    # start