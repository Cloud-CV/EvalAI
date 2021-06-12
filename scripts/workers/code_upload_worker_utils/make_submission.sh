#!/bin/sh
echo "File Submission Started."
submission_url="$EVALAI_API_SERVER/api/jobs/challenge/$CHALLENGE_PK/challenge_phase/$PHASE_PK/submission/$SUBMISSION_PK"
submission_curl_base_request="curl --location --request PATCH '$submission_url' --header 'Authorization: Bearer $AUTH_TOKEN'"
if [ -f "$SUBMISSION_PATH/submission.csv" ]
then
    file_path="submission.csv"
    curl_request="$submission_curl_base_request -F \"submission_input_file=@$SUBMISSION_PATH/$file_path\""
elif [ -f "$SUBMISSION_PATH/submission.json" ]
then
    file_path="submission.json"
    curl_request="$submission_curl_base_request -F \"submission_input_file=@$SUBMISSION_PATH/$file_path\""
else
    echo "submission.json/submission.csv not found."
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
fi
echo $curl_request
eval $curl_request
echo "\nFile Submission Ended"
