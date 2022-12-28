import requests


def generate_repo_from_template(token, name):

    token = "token {}".format(token)

    headers = {'Authorization': token}
    payload = {'name': name}

    r = requests.post('https://api.github.com/repos/Cloud-CV/EvalAI-Starters/generate', headers=headers, json=payload)
    return r
