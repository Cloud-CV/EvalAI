#!/bin/sh
echo "Monitoring submission..."
time_elapsed=0
while [ $time_elapsed -le $SUBMISSION_TIME_LIMIT ]
do
    echo "Checking for submission file after $time_elapsed secs.."
    sh /evalai_scripts/make_submission.sh
    if [ -f "$SUBMISSION_PATH/completed.txt" ]
    then
        echo "Submission Complete, Exiting."
        exit 0
    fi
    if [ $time_elapsed -lt $SUBMISSION_TIME_LIMIT -a $(( $time_elapsed + $SUBMISSION_TIME_DELTA )) -gt $SUBMISSION_TIME_LIMIT ]
    then
        time_interval=$(( $SUBMISSION_TIME_LIMIT - $time_elapsed ))
    else
        time_interval=$SUBMISSION_TIME_DELTA
    fi
    time_elapsed=$(( $time_elapsed + $time_interval ))
    if [ $time_elapsed -le $SUBMISSION_TIME_LIMIT ]
    then
        sleep $time_interval
    fi
done
url="$EVALAI_API_SERVER/api/jobs/challenge/$CHALLENGE_PK/update_submission/"
submission_data="{\
    \"challenge_phase\": $PHASE_PK,\
    \"submission\": $SUBMISSION_PK,\
    \"stdout\": \"\",\
    \"stderr\": \"Execution time limit exceeded\",\
    \"submission_status\": \"failed\",\
    \"result\": \"[]\",\
    \"metadata\": \"\"\
}"
curl_request="curl --location --request PUT '$url' -H 'Content-Type: application/json' --header 'Authorization: Bearer $AUTH_TOKEN' -d '$submission_data'"
eval $curl_request
echo "\nFile submission failed."
echo "Monitoring submission completed."
