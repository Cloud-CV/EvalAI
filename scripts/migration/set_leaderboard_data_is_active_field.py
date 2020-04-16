# Command to run: python manage.py shell < scripts/migration/set_leaderboard_data_is_active_fieleaderboard_data.py
# TODO: Run the code using a function based approach
# Please add the specific challenge phase split ID before launching this script

import traceback

from challenges.models import LeaderboardData

challenge_phase_split_id = None

assert isinstance(
    challenge_phase_split_id, int
), "Challenge Phase Split ID should be an int"

try:
    leaderboard_data_list = LeaderboardData.objects.filter(
        challenge_phase_split=challenge_phase_split_id
    ).order_by("-created_at")
    is_active_ids = []
    leaderboard_data_to_be_changed_false = []
    for leaderboard_data in leaderboard_data_list:
        if leaderboard_data.submission.id not in is_active_ids:
            is_active_ids.append(leaderboard_data.submission.id)
        else:
            leaderboard_data_to_be_changed_false.append(leaderboard_data)

    for leaderboard_data in leaderboard_data_to_be_changed_false:
        leaderboard_data.is_active = False
        leaderboard_data.save()

except Exception as e:
    print(e)
    print(traceback.print_exc())
