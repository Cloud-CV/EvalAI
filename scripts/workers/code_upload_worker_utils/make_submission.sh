#!/bin/sh
submission_url="$EVALAI_API_SERVER/api/jobs/challenge/$CHALLENGE_PK/update_submission/"
submission_curl_base_request="curl --location --request PATCH '$submission_url' --header 'Authorization: Bearer $AUTH_TOKEN' -F 'submission=$SUBMISSION_PK'"
if [ -f "$SUBMISSION_PATH/submission.csv" ]
then
    file_path="submission.csv"
    curl_request="$submission_curl_base_request -F \"submission_input_file=@$SUBMISSION_PATH/$file_path\""
elif [ -f "$SUBMISSION_PATH/submission.json" ]
then
    file_path="submission.json"
    curl_request="$submission_curl_base_request -F \"submission_input_file=@$SUBMISSION_PATH/$file_path\""
else
    echo "Submission not complete"
    exit 0
fi
echo "Submitting file to EvalAI..."
eval $curl_request
echo "\nFile submitted successfully"
echo $(date) > "$SUBMISSION_PATH/completed.txt"
