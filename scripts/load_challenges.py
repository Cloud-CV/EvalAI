def load_single_challenge(url, challenge_id):
    try:
        response = requests.get(url)
    except Exception as e:
        print 'Failed to download evaluation script from {}, error {}'.format(url, e)

    if response and response.status_code == 200:
        challenge_eval_script = join('active_challenges', 'challenge_{}'.format(challenge_id))
        with open(challenge_eval_script + '.zip', 'w') as f:
            f.write(response.content)
        # extract zip file
        zip_ref = zipfile.ZipFile(challenge_eval_script + '.zip', 'r')
        zip_ref.extractall(challenge_eval_script)
        zip_ref.close()
        # delete zip file
        try:
            os.remove(challenge_eval_script + '.zip')
        except Exception as e:
            print 'Failed to remove zip file {}, error {}'.format(challenge_eval_script, e)

        challenge_module = importlib.import_module('active_challenges.challenge_{}'.format(challenge_id))

        EVALUATION_SCRIPTS[str(challenge_id)] = challenge_module
        print EVALUATION_SCRIPTS
        # just to check, will be definitely removed.
        dummy_args = {'hey': 'how'}
        EVALUATION_SCRIPTS[str(challenge_id)].main(dummy_args)

def fetch_active_challenge():
    '''
        Fetches the active challenges(start date < now < end date)
    '''
    q_params = {}
    q_params['start_date__lt'] = timezone.now()
    q_params['end_date__gt'] = timezone.now()

    active_challenges = Challenge.objects.filter(**q_params)
    print active_challenges
    return active_challenges

def load_active_challenges():
    active_challenges = fetch_active_challenge()

    for challenge in active_challenges:
        eval_script_url = challenge.evaluation_script
        challenge_id = challenge.id
        load_single_challenge(eval_script_url, challenge_id)
