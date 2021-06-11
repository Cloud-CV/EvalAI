#!/bin/sh
echo "File Submission Started."
# Submission_folder $1
# Sumbission curl request $2
# File Not found curl request $3
if [ -f "$1/submission.csv" ]
then
    file_path="submission.csv"
    eval $2
elif [ -f "$1/submission.json" ]
then
  file_path="submission.json"
  eval $2
else
    echo "Submission file not found."
    eval $3
fi
echo "File Submission Ended"