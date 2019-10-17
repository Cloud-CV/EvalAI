#!bin/sh
number="[[:digit:]]"
find / -name submission_$number -type d -exec rm -rf {} +
