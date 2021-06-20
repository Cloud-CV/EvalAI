#!/bin/sh
echo "Monitoring submission..."
time_elapsed=0
time_delta=3600
while [ $time_elapsed -le $SUBMISSION_TIME_LIMIT ]
do
    echo "Checking for submission file after $time_elapsed secs.."
    if [ -f "$SUBMISSION_PATH/completed.txt" ]
    then
        echo "Submission Complete, Exiting."
        exit 0
    elif [ -f "$SUBMISSION_PATH/failed.txt" ]
    then
        echo "Submission File not found."
        break
    fi
    if [ $time_elapsed -lt $SUBMISSION_TIME_LIMIT -a $(( $time_elapsed + $time_delta )) -gt $SUBMISSION_TIME_LIMIT ]
    then
        next_checkpoint=$SUBMISSION_TIME_LIMIT
    else
        next_checkpoint=$(( $time_elapsed + $time_delta ))
    fi
    if [ $next_checkpoint -le $SUBMISSION_TIME_LIMIT ]
    then
        sleep $(( $next_checkpoint - $time_elapsed ))
    fi
    time_elapsed=$next_checkpoint
done
url="$EVALAI_API_SERVER/api/jobs/challenge/$CHALLENGE_PK/update_submission/"
submission_data="{\
    \"challenge_phase\": $PHASE_PK,\
    \"submission\": $SUBMISSION_PK,\
    \"stdout\": \"\",\
    \"stderr\": \"submission.json/submission.csv not found.\",\
    \"submission_status\": \"failed\",\
    \"result\": \"[]\",\
    \"metadata\": \"\"\
}"
curl_request="curl --location --request PUT '$url' -H 'Content-Type: application/json' --header 'Authorization: Bearer $AUTH_TOKEN' -d '$submission_data'"
eval $curl_request
echo "\nMonitoring submission completed."
