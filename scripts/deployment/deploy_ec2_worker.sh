#!/bin/bash

# Step 1: Updating package repository
echo "Step 1/X: Updating package repository"
sudo apt-get update

# Step 2: Cloning EvalAI repository
echo "Step 2/X: Cloning EvalAI repository"
git clone https://github.com/Cloud-CV/EvalAI.git
sudo mv /EvalAI/ ~
cd ~/EvalAI

# Step 3: Installing awscli
echo "Step 3/X: Installing awscli"
sudo apt install awscli -y

# Step 4: Installing docker-compose
echo "Step 4/X: Installing docker-compose"
sudo apt install docker-compose -y

# Step 5: Adding user to docker group
echo "Step 5/X: Adding user to docker group"
sudo apt -V install gnupg2 pass -y
sudo usermod -aG docker $USER
newgrp docker

# Step 6: Configuring AWS credentials
echo "Step 6/X: Configuring AWS credentials"
aws configure set aws_access_key_id ${AWS_ACCESS_KEY_ID}
aws configure set aws_secret_access_key ${AWS_SECRET_ACCESS_KEY}
aws configure set default.region ${AWS_REGION}
export AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID}
export COMMIT_ID="latest"
export AWS_DEFAULT_REGION=${AWS_REGION}
export TRAVIS_BRANCH=${ENVIRONMENT}
eval $(aws ecr get-login --no-include-email)

# Step 7: Copying Docker environment file
echo "Step 7/X: Copying Docker environment file"
aws s3 cp s3://cloudcv-secrets/evalai/${ENVIRONMENT}/docker_${ENVIRONMENT}.env ./docker/prod/docker_${ENVIRONMENT}.env

# Step 8: Pulling worker Docker image
echo "Step 8/X: Pulling worker Docker image"
echo "Deploying worker for queue: " ${QUEUE}
docker-compose -f docker-compose-${ENVIRONMENT}.yml pull worker

# Step 9: Running worker Docker container
echo "Step 9/X: Running worker Docker container"
docker-compose -f docker-compose-${ENVIRONMENT}.yml run --name=worker_${QUEUE} -e CHALLENGE_QUEUE=${QUEUE} -e CHALLENGE_PK=${PK} -d worker
echo "Deployed worker docker container for queue: " ${QUEUE}

# Step 10: Setting up crontab
echo "Step 10/X: Setting up crontab"
crontab -l > workercron
echo "@reboot docker restart worker_${QUEUE}" >> workercron
crontab workercron
rm workercron

