#!/bin/bash
sudo apt-get update
git clone https://github.com/Cloud-CV/EvalAI.git
sudo mv /EvalAI/ ~
cd ~/EvalAI
sudo apt install awscli  -y
sudo apt install docker-compose -y
sudo groupadd docker
sudo apt -V install gnupg2 pass -y
sudo usermod -aG docker $USER
newgrp docker
aws configure set aws_access_key_id ${AWS_ACCESS_KEY_ID}
aws configure set aws_secret_access_key ${AWS_SECRET_ACCESS_KEY}
aws configure set default.region ${AWS_REGION}
export AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID}
export COMMIT_ID="latest"
export AWS_DEFAULT_REGION=${AWS_REGION}
export TRAVIS_BRANCH=${ENVIRONMENT}
eval $(aws ecr get-login --no-include-email)
aws s3 cp s3://cloudcv-secrets/evalai/${ENVIRONMENT}/docker_${ENVIRONMENT}.env ./docker/prod/docker_${ENVIRONMENT}.env
echo "Deploying worker for queue: " ${QUEUE}
docker-compose -f docker-compose-${ENVIRONMENT}.yml pull worker
docker-compose -f docker-compose-${ENVIRONMENT}.yml run --name=worker_${QUEUE} -e CHALLENGE_QUEUE=${QUEUE} -e CHALLENGE_PK=${PK} -d worker
echo "Deployed worker docker container for queue: " ${QUEUE}