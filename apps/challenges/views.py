import csv
import logging
import random
import requests
import shutil
import string
import tempfile
import yaml
import zipfile

from os.path import basename, isfile, join

from django.core.files.base import ContentFile
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone

from rest_framework import permissions, status
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes,
                                       throttle_classes,)
from rest_framework.response import Response
from rest_framework_expiring_authtoken.authentication import (ExpiringTokenAuthentication,)
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

from accounts.permissions import HasVerifiedEmail
from base.utils import paginated_queryset
from challenges.utils import (get_challenge_model,
                              get_challenge_phase_model,
                              get_challenge_phase_split_model,
                              get_dataset_split_model,
                              get_leaderboard_model)
from hosts.models import ChallengeHost, ChallengeHostTeam
from hosts.utils import get_challenge_host_teams_for_user, is_user_a_host_of_challenge, get_challenge_host_team_model
from jobs.models import Submission
from jobs.serializers import SubmissionSerializer, ChallengeSubmissionManagementSerializer
from participants.models import Participant, ParticipantTeam
from participants.utils import (get_participant_teams_for_user,
                                has_user_participated_in_challenge,
                                get_participant_team_id_of_user_for_a_challenge,)

from .models import (Challenge,
                     ChallengePhase,
                     ChallengePhaseSplit,
                     ChallengeConfiguration,
                     StarChallenge)
from .permissions import IsChallengeCreator
from .serializers import (ChallengeConfigSerializer,
                          ChallengePhaseSerializer,
                          ChallengePhaseCreateSerializer,
                          ChallengePhaseSplitSerializer,
                          ChallengeSerializer,
                          DatasetSplitSerializer,
                          LeaderboardSerializer,
                          StarChallengeSerializer,
                          ZipChallengeSerializer,
                          ZipChallengePhaseSplitSerializer,)
from .utils import get_file_content

logger = logging.getLogger(__name__)

try:
    xrange          # Python 2
except NameError:
    xrange = range  # Python 3


@throttle_classes([UserRateThrottle])
@api_view(['GET', 'POST'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def challenge_list(request, challenge_host_team_pk):
    try:
        challenge_host_team = ChallengeHostTeam.objects.get(pk=challenge_host_team_pk)
    except ChallengeHostTeam.DoesNotExist:
        response_data = {'error': 'ChallengeHostTeam does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if request.method == 'GET':
        challenge = Challenge.objects.filter(creator=challenge_host_team)
        paginator, result_page = paginated_queryset(challenge, request)
        serializer = ChallengeSerializer(result_page, many=True, context={'request': request})
        response_data = serializer.data
        return paginator.get_paginated_response(response_data)

    elif request.method == 'POST':
        if not ChallengeHost.objects.filter(user=request.user, team_name_id=challenge_host_team_pk).exists():
            response_data = {
                'error': 'Sorry, you do not belong to this Host Team!'}
            return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)

        serializer = ZipChallengeSerializer(data=request.data,
                                            context={'challenge_host_team': challenge_host_team,
                                                     'request': request})
        if serializer.is_valid():
            serializer.save()
            challenge = get_challenge_model(serializer.instance.pk)
            serializer = ChallengeSerializer(challenge)
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@throttle_classes([UserRateThrottle])
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator))
@authentication_classes((ExpiringTokenAuthentication,))
def challenge_detail(request, challenge_host_team_pk, challenge_pk):
    try:
        challenge_host_team = ChallengeHostTeam.objects.get(pk=challenge_host_team_pk)
    except ChallengeHostTeam.DoesNotExist:
        response_data = {'error': 'ChallengeHostTeam does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    try:
        challenge = Challenge.objects.get(pk=challenge_pk)
    except Challenge.DoesNotExist:
        response_data = {'error': 'Challenge does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if request.method == 'GET':
        serializer = ChallengeSerializer(challenge, context={'request': request})
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)

    elif request.method in ['PUT', 'PATCH']:
        if request.method == 'PATCH':
            serializer = ZipChallengeSerializer(challenge,
                                                data=request.data,
                                                context={'challenge_host_team': challenge_host_team,
                                                         'request': request},
                                                partial=True)
        else:
            serializer = ZipChallengeSerializer(challenge,
                                                data=request.data,
                                                context={'challenge_host_team': challenge_host_team,
                                                         'request': request})
        if serializer.is_valid():
            serializer.save()
            challenge = get_challenge_model(serializer.instance.pk)
            serializer = ChallengeSerializer(challenge)
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        challenge.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@throttle_classes([UserRateThrottle])
@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def add_participant_team_to_challenge(request, challenge_pk, participant_team_pk):

    try:
        challenge = Challenge.objects.get(pk=challenge_pk)
    except Challenge.DoesNotExist:
        response_data = {'error': 'Challenge does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    try:
        participant_team = ParticipantTeam.objects.get(pk=participant_team_pk)
    except ParticipantTeam.DoesNotExist:
        response_data = {'error': 'ParticipantTeam does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    # check to disallow the user if he is a Challenge Host for this challenge

    challenge_host_team_pk = challenge.creator.pk
    challenge_host_team_user_ids = set(ChallengeHost.objects.select_related('user').filter(
        team_name__id=challenge_host_team_pk).values_list('user', flat=True))

    participant_team_user_ids = set(Participant.objects.select_related('user').filter(
        team__id=participant_team_pk).values_list('user', flat=True))

    if challenge_host_team_user_ids & participant_team_user_ids:
        response_data = {'error': 'Sorry, You cannot participate in your own challenge!',
                         'challenge_id': int(challenge_pk), 'participant_team_id': int(participant_team_pk)}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    for user in participant_team_user_ids:
        if has_user_participated_in_challenge(user, challenge_pk):
            response_data = {'error': 'Sorry, other team member(s) have already participated in the Challenge.'
                             ' Please participate with a different team!',
                             'challenge_id': int(challenge_pk), 'participant_team_id': int(participant_team_pk)}
            return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if participant_team.challenge_set.filter(id=challenge_pk).exists():
        response_data = {'error': 'Team already exists', 'challenge_id': int(challenge_pk),
                         'participant_team_id': int(participant_team_pk)}
        return Response(response_data, status=status.HTTP_200_OK)
    else:
        challenge.participant_teams.add(participant_team)
        return Response(status=status.HTTP_201_CREATED)


@throttle_classes([UserRateThrottle])
@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator))
@authentication_classes((ExpiringTokenAuthentication,))
def disable_challenge(request, challenge_pk):
    try:
        challenge = Challenge.objects.get(pk=challenge_pk)
    except Challenge.DoesNotExist:
        response_data = {'error': 'Challenge does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    challenge.is_disabled = True
    challenge.save()
    return Response(status=status.HTTP_204_NO_CONTENT)


@throttle_classes([AnonRateThrottle])
@api_view(['GET'])
def get_all_challenges(request, challenge_time):
    """
    Returns the list of all challenges
    """
    # make sure that a valid url is requested.
    if challenge_time.lower() not in ("all", "future", "past", "present"):
        response_data = {'error': 'Wrong url pattern!'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    q_params = {'published': True, 'approved_by_admin': True}
    if challenge_time.lower() == "past":
        q_params['end_date__lt'] = timezone.now()

    elif challenge_time.lower() == "present":
        q_params['start_date__lt'] = timezone.now()
        q_params['end_date__gt'] = timezone.now()

    elif challenge_time.lower() == "future":
        q_params['start_date__gt'] = timezone.now()
    # for `all` we dont need any condition in `q_params`

    challenge = Challenge.objects.filter(**q_params)
    paginator, result_page = paginated_queryset(challenge, request)
    serializer = ChallengeSerializer(result_page, many=True, context={'request': request})
    response_data = serializer.data
    return paginator.get_paginated_response(response_data)


@throttle_classes([AnonRateThrottle])
@api_view(['GET'])
def get_challenge_by_pk(request, pk):
    """
    Returns a particular challenge by id
    """
    try:
        challenge = Challenge.objects.get(pk=pk)
        serializer = ChallengeSerializer(challenge, context={'request': request})
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)
    except:
        response_data = {'error': 'Challenge does not exist!'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)


@throttle_classes([UserRateThrottle])
@api_view(['GET', ])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_challenges_based_on_teams(request):
    q_params = {'approved_by_admin': True, 'published': True}
    participant_team_id = request.query_params.get('participant_team', None)
    challenge_host_team_id = request.query_params.get('host_team', None)
    mode = request.query_params.get('mode', None)

    if not participant_team_id and not challenge_host_team_id and not mode:
        response_data = {'error': 'Invalid url pattern!'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    # either mode should be there or one of paricipant team and host team
    if mode and (participant_team_id or challenge_host_team_id):
        response_data = {'error': 'Invalid url pattern!'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if participant_team_id:
        q_params['participant_teams__pk'] = participant_team_id
    if challenge_host_team_id:
        q_params['creator__id'] = challenge_host_team_id

    if mode == 'participant':
        participant_team_ids = get_participant_teams_for_user(request.user)
        q_params['participant_teams__pk__in'] = participant_team_ids

    elif mode == 'host':
        host_team_ids = get_challenge_host_teams_for_user(request.user)
        q_params['creator__id__in'] = host_team_ids

    challenge = Challenge.objects.filter(**q_params)
    paginator, result_page = paginated_queryset(challenge, request)
    serializer = ChallengeSerializer(result_page, many=True, context={'request': request})
    response_data = serializer.data
    return paginator.get_paginated_response(response_data)


@throttle_classes([UserRateThrottle])
@api_view(['GET', 'POST'])
@permission_classes((permissions.IsAuthenticatedOrReadOnly, HasVerifiedEmail, IsChallengeCreator))
@authentication_classes((ExpiringTokenAuthentication,))
def challenge_phase_list(request, challenge_pk):
    try:
        challenge = Challenge.objects.get(pk=challenge_pk)
    except Challenge.DoesNotExist:
        response_data = {'error': 'Challenge does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if request.method == 'GET':
        challenge_phase = ChallengePhase.objects.filter(challenge=challenge, is_public=True)
        paginator, result_page = paginated_queryset(challenge_phase, request)
        serializer = ChallengePhaseSerializer(result_page, many=True)
        response_data = serializer.data
        return paginator.get_paginated_response(response_data)

    elif request.method == 'POST':
        serializer = ChallengePhaseCreateSerializer(data=request.data,
                                                    context={'challenge': challenge})
        if serializer.is_valid():
            serializer.save()
            challenge_phase = get_challenge_phase_model(serializer.instance.pk)
            serializer = ChallengePhaseSerializer(challenge_phase)
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@throttle_classes([UserRateThrottle])
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes((permissions.IsAuthenticatedOrReadOnly, HasVerifiedEmail, IsChallengeCreator))
@authentication_classes((ExpiringTokenAuthentication,))
def challenge_phase_detail(request, challenge_pk, pk):
    try:
        challenge = Challenge.objects.get(pk=challenge_pk)
    except Challenge.DoesNotExist:
        response_data = {'error': 'Challenge does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    try:
        challenge_phase = ChallengePhase.objects.get(pk=pk)
    except ChallengePhase.DoesNotExist:
        response_data = {'error': 'ChallengePhase does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if request.method == 'GET':
        serializer = ChallengePhaseSerializer(challenge_phase)
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)

    elif request.method in ['PUT', 'PATCH']:
        if request.method == 'PATCH':
            serializer = ChallengePhaseCreateSerializer(challenge_phase,
                                                        data=request.data,
                                                        context={'challenge': challenge},
                                                        partial=True)
        else:
            serializer = ChallengePhaseCreateSerializer(challenge_phase,
                                                        data=request.data,
                                                        context={'challenge': challenge})
        if serializer.is_valid():
            serializer.save()
            challenge_phase = get_challenge_phase_model(serializer.instance.pk)
            serializer = ChallengePhaseSerializer(challenge_phase)
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        challenge_phase.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@throttle_classes([AnonRateThrottle])
@api_view(['GET'])
def challenge_phase_split_list(request, challenge_pk):
    """
    Returns the list of Challenge Phase Splits for a particular challenge
    """
    try:
        challenge = Challenge.objects.get(pk=challenge_pk)
    except Challenge.DoesNotExist:
        response_data = {'error': 'Challenge does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    challenge_phase_split = ChallengePhaseSplit.objects.filter(challenge_phase__challenge=challenge)
    serializer = ChallengePhaseSplitSerializer(challenge_phase_split, many=True)
    response_data = serializer.data
    return Response(response_data, status=status.HTTP_200_OK)


@throttle_classes([UserRateThrottle])
@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def create_challenge_using_zip_file(request, challenge_host_team_pk):
    """
    Creates a challenge using a zip file.
    """
    challenge_host_team = get_challenge_host_team_model(challenge_host_team_pk)

    serializer = ChallengeConfigSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        uploaded_zip_file = serializer.save()
        uploaded_zip_file_path = serializer.data['zip_configuration']
    else:
        response_data = serializer.errors
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # All files download and extract location.
    BASE_LOCATION = tempfile.mkdtemp()
    try:
        response = requests.get(uploaded_zip_file_path, stream=True)
        unique_folder_name = ''.join([random.choice(string.ascii_letters + string.digits) for i in xrange(10)])
        CHALLENGE_ZIP_DOWNLOAD_LOCATION = join(BASE_LOCATION, '{}.zip'.format(unique_folder_name))
        try:
            if response and response.status_code == 200:
                with open(CHALLENGE_ZIP_DOWNLOAD_LOCATION, 'w') as zip_file:
                    zip_file.write(response.content)
        except IOError:
            response_data = {
                'error': 'Unable to process the uploaded zip file. Please upload it again!'
                }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    except requests.exceptions.RequestException:
        response_data = {
            'error': 'A server error occured while processing zip file. Please try uploading it again!'
            }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    # Extract zip file
    try:
        zip_ref = zipfile.ZipFile(CHALLENGE_ZIP_DOWNLOAD_LOCATION, 'r')
        zip_ref.extractall(join(BASE_LOCATION, unique_folder_name))
        zip_ref.close()
    except zipfile.BadZipfile:
        response_data = {
            'error': 'The zip file contents cannot be extracted. Please check the format!'
            }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # Search for yaml file
    yaml_file_count = 0
    for name in zip_ref.namelist():
        if name.endswith('.yaml') or name.endswith('.yml'):
            yaml_file = name
            extracted_folder_name = yaml_file.split(basename(yaml_file))[0]
            yaml_file_count += 1

    if not yaml_file_count:
        response_data = {
            'error': 'There is no YAML file in zip configuration you provided!'
            }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if yaml_file_count > 1:
        response_data = {
            'error': 'There are more than one YAML files in zip folder!'
            }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    try:
        with open(join(BASE_LOCATION, unique_folder_name, yaml_file), "r") as stream:
            yaml_file_data = yaml.load(stream)
    except yaml.YAMLError as exc:
        response_data = {
            'error': exc
            }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    # Check for evaluation script path in yaml file.
    evaluation_script = yaml_file_data['evaluation_script']
    if evaluation_script:
        evaluation_script_path = join(BASE_LOCATION,
                                      unique_folder_name,
                                      extracted_folder_name,
                                      evaluation_script)
    else:
        response_data = {
            'error': ('There is no key for evaluation script in yaml file.'
                      'Please add a key and then try uploading it again!')
            }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    # Check for evaluation script file in extracted zip folder.
    if isfile(evaluation_script_path):
        with open(evaluation_script_path, 'rb') as challenge_evaluation_script:
            challenge_evaluation_script_file = ContentFile(challenge_evaluation_script.read(), evaluation_script_path)
    else:
        response_data = {
            'error': ('No evaluation script is present in the zip file.'
                      'Please try uploading again the zip file after adding evaluation script!')
            }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    # Check for test annotation file path in yaml file.
    yaml_file_data_of_challenge_phases = yaml_file_data['challenge_phases']
    for data in yaml_file_data_of_challenge_phases:
        test_annotation_file = data['test_annotation_file']
        if test_annotation_file:
            test_annotation_file_path = join(BASE_LOCATION,
                                             unique_folder_name,
                                             extracted_folder_name,
                                             test_annotation_file)
        else:
            response_data = {
                'error': ('There is no key for test annotation file for'
                          'challenge phase {} in yaml file.'
                          'Please add a key and then try uploading it again!'.format(data['name']))
                }
            return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

        if not isfile(test_annotation_file_path):
            response_data = {
                'error': ('No test annotation file is present in the zip file'
                          'for challenge phase \'{}\'. Please try uploading '
                          'again after adding test annotation file!'.format(data['name']))
            }
            return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    # Check for challenge image in yaml file.
    image = yaml_file_data['image']
    if image.endswith('.jpg') or image.endswith('.jpeg') or image.endswith('.png'):
        challenge_image_path = join(BASE_LOCATION,
                                    unique_folder_name,
                                    extracted_folder_name,
                                    image)
        if isfile(challenge_image_path):
            challenge_image_file = ContentFile(get_file_content(challenge_image_path, 'rb'), image)
        else:
            challenge_image_file = None
    else:
        challenge_image_file = None

    # check for challenge description file
    challenge_description_file_path = join(BASE_LOCATION,
                                           unique_folder_name,
                                           extracted_folder_name,
                                           yaml_file_data['description'])
    if challenge_description_file_path.endswith('.html') and isfile(challenge_description_file_path):
        yaml_file_data['description'] = get_file_content(challenge_description_file_path, 'rb').decode('utf-8')
    else:
        yaml_file_data['description'] = None

    # check for evaluation details file
    challenge_evaluation_details_file_path = join(BASE_LOCATION,
                                                  unique_folder_name,
                                                  extracted_folder_name,
                                                  yaml_file_data['evaluation_details'])

    if (challenge_evaluation_details_file_path.endswith('.html') and
            isfile(challenge_evaluation_details_file_path)):
        yaml_file_data['evaluation_details'] = get_file_content(challenge_evaluation_details_file_path,
                                                                'rb').decode('utf-8')
    else:
        yaml_file_data['evaluation_details'] = None

    # check for terms and conditions file
    challenge_terms_and_cond_file_path = join(BASE_LOCATION,
                                              unique_folder_name,
                                              extracted_folder_name,
                                              yaml_file_data['terms_and_conditions'])
    if challenge_terms_and_cond_file_path.endswith('.html') and isfile(challenge_terms_and_cond_file_path):
        yaml_file_data['terms_and_conditions'] = get_file_content(challenge_terms_and_cond_file_path,
                                                                  'rb').decode('utf-8')
    else:
        yaml_file_data['terms_and_conditions'] = None

    # check for submission guidelines file
    challenge_submission_guidelines_file_path = join(BASE_LOCATION,
                                                     unique_folder_name,
                                                     extracted_folder_name,
                                                     yaml_file_data['submission_guidelines'])
    if (challenge_submission_guidelines_file_path.endswith('.html')
            and isfile(challenge_submission_guidelines_file_path)):
        yaml_file_data['submission_guidelines'] = get_file_content(challenge_submission_guidelines_file_path,
                                                                   'rb').decode('utf-8')
    else:
        yaml_file_data['submission_guidelines'] = None

    try:
        with transaction.atomic():
            serializer = ZipChallengeSerializer(data=yaml_file_data,
                                                context={'request': request,
                                                         'challenge_host_team': challenge_host_team,
                                                         'image': challenge_image_file,
                                                         'evaluation_script': challenge_evaluation_script_file})
            if serializer.is_valid():
                serializer.save()
                challenge = serializer.instance
            else:
                response_data = serializer.errors

            # Create Leaderboard
            yaml_file_data_of_leaderboard = yaml_file_data['leaderboard']
            leaderboard_ids = {}
            for data in yaml_file_data_of_leaderboard:
                serializer = LeaderboardSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                    leaderboard_ids[str(data['id'])] = serializer.instance.pk
                else:
                    response_data = serializer.errors

            # Create Challenge Phase
            yaml_file_data_of_challenge_phases = yaml_file_data['challenge_phases']
            challenge_phase_ids = {}
            for data in yaml_file_data_of_challenge_phases:
                # Check for challenge phase description file
                challenge_phase_description_file_path = join(BASE_LOCATION,
                                                             unique_folder_name,
                                                             extracted_folder_name,
                                                             data['description'])
                if (challenge_phase_description_file_path.endswith('.html')
                        and isfile(challenge_phase_description_file_path)):
                    data['description'] = get_file_content(challenge_phase_description_file_path, 'rb').decode('utf-8')
                else:
                    data['description'] = None

                test_annotation_file = data['test_annotation_file']
                if test_annotation_file:
                    test_annotation_file_path = join(BASE_LOCATION,
                                                     unique_folder_name,
                                                     extracted_folder_name,
                                                     test_annotation_file
                                                     )
                if isfile(test_annotation_file_path):
                    with open(test_annotation_file_path, 'rb') as test_annotation_file:
                        challenge_test_annotation_file = ContentFile(test_annotation_file.read(),
                                                                     test_annotation_file_path)
                serializer = ChallengePhaseCreateSerializer(data=data,
                                                            context={'challenge': challenge,
                                                                     'test_annotation': challenge_test_annotation_file})
                if serializer.is_valid():
                    serializer.save()
                    challenge_phase_ids[str(data['id'])] = serializer.instance.pk
                else:
                    response_data = serializer.errors

            # Create Dataset Splits
            yaml_file_data_of_dataset_split = yaml_file_data['dataset_splits']
            dataset_split_ids = {}
            for data in yaml_file_data_of_dataset_split:
                serializer = DatasetSplitSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                    dataset_split_ids[str(data['id'])] = serializer.instance.pk
                else:
                    # Return error when dataset split name is not unique.
                    response_data = serializer.errors

            # Create Challenge Phase Splits
            yaml_file_data_of_challenge_phase_splits = yaml_file_data['challenge_phase_splits']
            for data in yaml_file_data_of_challenge_phase_splits:
                challenge_phase = challenge_phase_ids[str(data['challenge_phase_id'])]
                leaderboard = leaderboard_ids[str(data['leaderboard_id'])]
                dataset_split = dataset_split_ids[str(data['dataset_split_id'])]
                visibility = data['visibility']

                data = {
                    'challenge_phase': challenge_phase,
                    'leaderboard': leaderboard,
                    'dataset_split': dataset_split,
                    'visibility': visibility
                }

                serializer = ZipChallengePhaseSplitSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    response_data = serializer.errors

        zip_config = ChallengeConfiguration.objects.get(pk=uploaded_zip_file.pk)
        if zip_config:
            zip_config.challenge = challenge
            zip_config.save()
            response_data = {'success': 'Challenge {} has been created successfully and'
                                        ' sent for review to EvalAI Admin.'.format(challenge.title)}
            return Response(response_data, status=status.HTTP_201_CREATED)

    except:
        try:
            if response_data:
                response_data = {'error': response_data.values()[0]}
                return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)
        except:
            response_data = {'error': 'Error in creating challenge. Please check the yaml configuration!'}
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        finally:
            try:
                shutil.rmtree(BASE_LOCATION)
                logger.info('Zip folder is removed')
            except:
                logger.info('Zip folder for challenge {} is not removed from location'.format(challenge.pk,
                                                                                              BASE_LOCATION))
    try:
        shutil.rmtree(BASE_LOCATION)
        logger.info('Zip folder is removed')
    except:
        logger.info('Zip folder for challenge {} is not removed from location'.format(challenge.pk,
                                                                                      BASE_LOCATION))


@throttle_classes([UserRateThrottle])
@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_all_submissions_of_challenge(request, challenge_pk, challenge_phase_pk):
    """
    Returns all the submissions for a particular challenge
    """
    # To check for the corresponding challenge from challenge_pk.
    challenge = get_challenge_model(challenge_pk)

    # To check for the corresponding challenge phase from the challenge_phase_pk and challenge.
    try:
        challenge_phase = ChallengePhase.objects.get(pk=challenge_phase_pk, challenge=challenge)
    except ChallengePhase.DoesNotExist:
        response_data = {'error': 'Challenge Phase {} does not exist'.format(challenge_phase_pk)}
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)

    # To check for the user as a host of the challenge from the request and challenge_pk.
    if is_user_a_host_of_challenge(user=request.user, challenge_pk=challenge_pk):

        # Filter submissions on the basis of challenge for host for now. Later on, the support for query
        # parameters like challenge phase, date is to be added.
        submissions = Submission.objects.filter(challenge_phase=challenge_phase).order_by('-submitted_at')
        paginator, result_page = paginated_queryset(submissions, request)
        try:
            serializer = ChallengeSubmissionManagementSerializer(result_page, many=True, context={'request': request})
            response_data = serializer.data
            return paginator.get_paginated_response(response_data)
        except:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # To check for the user as a participant of the challenge from the request and challenge_pk.
    elif has_user_participated_in_challenge(user=request.user, challenge_id=challenge_pk):

        # get participant team object for the user for a particular challenge.
        participant_team_pk = get_participant_team_id_of_user_for_a_challenge(
                request.user, challenge_pk)

        # Filter submissions on the basis of challenge phase for a participant.
        submissions = Submission.objects.filter(participant_team=participant_team_pk,
                                                challenge_phase=challenge_phase).order_by('-submitted_at')
        paginator, result_page = paginated_queryset(submissions, request)
        try:
            serializer = SubmissionSerializer(result_page, many=True, context={'request': request})
            response_data = serializer.data
            return paginator.get_paginated_response(response_data)
        except:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # when user is neither host not participant of the challenge.
    else:
        response_data = {'error': 'You are neither host nor participant of the challenge!'}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


@throttle_classes([UserRateThrottle])
@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def download_all_submissions(request, challenge_pk, challenge_phase_pk, file_type):

    # To check for the corresponding challenge from challenge_pk.
    challenge = get_challenge_model(challenge_pk)

    # To check for the corresponding challenge phase from the challenge_phase_pk and challenge.
    try:
        challenge_phase = ChallengePhase.objects.get(pk=challenge_phase_pk, challenge=challenge)
    except ChallengePhase.DoesNotExist:
        response_data = {'error': 'Challenge Phase {} does not exist'.format(challenge_phase_pk)}
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)

    if file_type == 'csv':
        if is_user_a_host_of_challenge(user=request.user, challenge_pk=challenge_pk):
            submissions = Submission.objects.filter(challenge_phase__challenge=challenge).order_by('-submitted_at')
            submissions = ChallengeSubmissionManagementSerializer(submissions, many=True, context={'request': request})
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=all_submissions.csv'
            writer = csv.writer(response)
            writer.writerow(['id',
                             'Team Name',
                             'Team Members',
                             'Team Members Email Id',
                             'Challenge Phase',
                             'Status',
                             'Created By',
                             'Execution Time(sec.)',
                             'Submission Number',
                             'Submitted File',
                             'Stdout File',
                             'Stderr File',
                             'Submitted At',
                             'Submission Result File',
                             'Submission Metadata File',
                             ])
            for submission in submissions.data:
                writer.writerow([submission['id'],
                                 submission['participant_team'],
                                 ",".join(username['username'] for username in submission['participant_team_members']),
                                 ",".join(email['email'] for email in submission['participant_team_members']),
                                 submission['challenge_phase'],
                                 submission['status'],
                                 submission['created_by'],
                                 submission['execution_time'],
                                 submission['submission_number'],
                                 submission['input_file'],
                                 submission['stdout_file'],
                                 submission['stderr_file'],
                                 submission['created_at'],
                                 submission['submission_result_file'],
                                 submission['submission_metadata_file'],
                                 ])
            return response

        elif has_user_participated_in_challenge(user=request.user, challenge_id=challenge_pk):

            # get participant team object for the user for a particular challenge.
            participant_team_pk = get_participant_team_id_of_user_for_a_challenge(
                request.user, challenge_pk)

            # Filter submissions on the basis of challenge phase for a participant.
            submissions = Submission.objects.filter(participant_team=participant_team_pk,
                                                    challenge_phase=challenge_phase).order_by('-submitted_at')
            submissions = ChallengeSubmissionManagementSerializer(submissions, many=True, context={'request': request})
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=all_submissions.csv'
            writer = csv.writer(response)
            writer.writerow(['Team Name',
                             'Method Name',
                             'Status',
                             'Execution Time(sec.)',
                             'Submitted File',
                             'Result File',
                             'Stdout File',
                             'Stderr File',
                             'Submitted At',
                             ])
            for submission in submissions.data:
                writer.writerow([submission['participant_team'],
                                 submission['method_name'],
                                 submission['status'],
                                 submission['execution_time'],
                                 submission['input_file'],
                                 submission['submission_result_file'],
                                 submission['stdout_file'],
                                 submission['stderr_file'],
                                 submission['created_at'],
                                 ])
            return response
        else:
            response_data = {'error': 'You are neither host nor participant of the challenge!'}
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    else:
        response_data = {'error': 'The file type requested is not valid!'}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


@throttle_classes([UserRateThrottle])
@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def create_leaderboard(request):
    """
    Creates a leaderboard
    """
    serializer = LeaderboardSerializer(data=request.data, many=True, allow_empty=False)
    if serializer.is_valid():
        serializer.save()
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@throttle_classes([UserRateThrottle])
@api_view(['GET', 'PATCH'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_or_update_leaderboard(request, leaderboard_pk):
    """
    Returns or Updates a leaderboard
    """
    leaderboard = get_leaderboard_model(leaderboard_pk)

    if request.method == 'PATCH':
        serializer = LeaderboardSerializer(leaderboard,
                                           data=request.data,
                                           partial=True)

        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        serializer = LeaderboardSerializer(leaderboard)
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)


@throttle_classes([UserRateThrottle])
@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def create_dataset_split(request):
    """
    Creates a dataset split
    """
    serializer = DatasetSplitSerializer(data=request.data, many=True, allow_empty=False)
    if serializer.is_valid():
        serializer.save()
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_201_CREATED)
    else:
        response_data = serializer.errors
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


@throttle_classes([UserRateThrottle])
@api_view(['GET', 'PATCH'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_or_update_dataset_split(request, dataset_split_pk):
    """
    Returns or Updates a dataset split
    """
    dataset_split = get_dataset_split_model(dataset_split_pk)
    if request.method == 'PATCH':
        serializer = DatasetSplitSerializer(dataset_split,
                                            data=request.data,
                                            partial=True)
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            response_data = serializer.errors
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        serializer = DatasetSplitSerializer(dataset_split)
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)


@throttle_classes([UserRateThrottle])
@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def create_challenge_phase_split(request):
    """
    Create Challenge Phase Split
    """
    serializer = ZipChallengePhaseSplitSerializer(data=request.data, many=True, allow_empty=False)
    if serializer.is_valid():
        serializer.save()
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_201_CREATED)
    else:
        response_data = serializer.errors
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


@throttle_classes([UserRateThrottle])
@api_view(['GET', 'PATCH'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_or_update_challenge_phase_split(request, challenge_phase_split_pk):
    """
    Returns or Updates challenge phase split
    """
    challenge_phase_split = get_challenge_phase_split_model(challenge_phase_split_pk)

    if request.method == 'PATCH':
        serializer = ZipChallengePhaseSplitSerializer(challenge_phase_split,
                                                      data=request.data,
                                                      partial=True)
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.erros, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        serializer = ZipChallengePhaseSplitSerializer(challenge_phase_split)
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)


@throttle_classes([UserRateThrottle])
@api_view(['GET', 'POST'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def star_challenge(request, challenge_pk):
    """
    API endpoint for starring and unstarring
    a challenge.
    """
    challenge = get_challenge_model(challenge_pk)

    if request.method == 'POST':
        try:
            starred_challenge = StarChallenge.objects.get(user=request.user,
                                                          challenge=challenge)
            starred_challenge.is_starred = not starred_challenge.is_starred
            starred_challenge.save()
            serializer = StarChallengeSerializer(starred_challenge)
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        except:
            serializer = StarChallengeSerializer(data=request.data, context={'request': request,
                                                                             'challenge': challenge,
                                                                             'is_starred': True})
            if serializer.is_valid():
                serializer.save()
                response_data = serializer.data
                return Response(response_data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        try:
            starred_challenge = StarChallenge.objects.get(user=request.user,
                                                          challenge=challenge)
            serializer = StarChallengeSerializer(starred_challenge)
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        except:
            starred_challenge = StarChallenge.objects.filter(challenge=challenge)
            if not starred_challenge:
                response_data = {'is_starred': False,
                                 'count': 0}
                return Response(response_data, status=status.HTTP_200_OK)

            serializer = StarChallengeSerializer(starred_challenge, many=True)
            response_data = {'is_starred': False,
                             'count': serializer.data[0]['count']}
            return Response(response_data, status=status.HTTP_200_OK)
