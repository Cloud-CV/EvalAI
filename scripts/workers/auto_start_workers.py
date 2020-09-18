import os
import pytz
import requests

from datetime import datetime
from dateutil import parser

utc = pytz.UTC
evalai_endpoint = os.environ.get("API_HOST_URL")
authorization_header = {
	"Authorization": "Token {}".format(os.environ.get("AUTH_TOKEN"))
}

def start_worker(challenge_id):
	start_worker_endpoint = "{}/api/challenges/{}/manage_worker/start".format(evalai_endpoint, challenge_id)
	response = requests.post(start_worker_endpoint, headers=authorization_header)
	return response


def stop_worker(challenge_id):
	stop_worker_endpoint = "{}/api/challenges/{}/manage_worker/stop".format(evalai_endpoint, challenge_id)
	response = requests.post(stop_worker_endpoint, headers=authorization_header)
	return response


def get_all_challenges():
	all_challenge_endpoint = "{}/api/challenges/challenge/present".format(evalai_endpoint)
	print(all_challenge_endpoint)
	response = requests.get(all_challenge_endpoint, headers=authorization_header)
	return response.json()


def start_or_stop_workers_for_active_challenges():
	response = get_all_challenges()

	for challenge in response["results"]:
		challenge_id = challenge["id"]
		workers = challenge["workers"]
		is_docker_based = challenge["is_docker_based"]
		challenge_start_date = parser.parse(challenge["start_date"])
		challenge_end_date = parser.parse(challenge["end_date"])
		current_date = utc.localize(datetime.now())

		print('Start submission worker for challenge id {}'.format(challenge_id))
		if not is_docker_based:
			if workers is None and challenge_start_date <= current_date:
				response = start_worker(challenge_id)
				if not response.ok:
					print('ERROR: Start worker failed for challenge id {}!'.format(challenge_id))
			if workers is not None and challenge_end_date <= current_date
				response = stop_worker(challenge_id)
				if not response.ok:
					print('ERROR: Stop worker failed for challenge id {}!'.format(challenge_id))


if __name__ == '__main__':
	start_or_stop_workers_for_active_challenges()
	print('Quitting worker auto start script!')
