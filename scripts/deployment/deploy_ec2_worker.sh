#!/bin/bash

# Step 1: Updating package repository
echo "Step 1/10: Updating package repository"
sudo apt-get update

# Step 2: Cloning EvalAI repository at /home/ubuntu
echo "Step 2/10: Cloning EvalAI repository"
cd /home/ubuntu
git clone https://github.com/Cloud-CV/EvalAI.git
cd EvalAI

# Step 3: Installing awscli
echo "Step 3/10: Installing awscli"
sudo apt install awscli -y

# Step 4: Installing docker-compose
echo "Step 4/10: Installing docker-compose"
sudo apt install docker-compose -y
sudo groupadd docker

# Step 5: Adding user to docker group
echo "Step 5/10: Adding user to docker group"
sudo apt -V install gnupg2 pass -y
sudo usermod -aG docker $USER
newgrp docker

# Step 6: Configuring AWS credentials
echo "Step 6/10: Configuring AWS credentials"
aws configure set aws_access_key_id ${AWS_ACCESS_KEY_ID}
aws configure set aws_secret_access_key ${AWS_SECRET_ACCESS_KEY}
aws configure set default.region ${AWS_REGION}
export AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID}
export COMMIT_ID="latest"
export AWS_DEFAULT_REGION=${AWS_REGION}
export TRAVIS_BRANCH=${ENVIRONMENT}
eval $(aws ecr get-login --no-include-email)

# Step 7: Copying Docker environment file
echo "Step 7/10: Copying Docker environment file"
aws s3 cp s3://cloudcv-secrets/evalai/${ENVIRONMENT}/docker_${ENVIRONMENT}.env ./docker/prod/docker_${ENVIRONMENT}.env

if [ "${CUSTOM_WORKER_IMAGE}" = "" ]; 
then
    # Step 8: Pulling worker Docker image
    echo "Step 8/10: Pulling worker Docker image"
    docker-compose -f docker-compose-${ENVIRONMENT}.yml pull worker
else
    # if using custom image from worker_image_url
    echo "Step 8/10: Pulling worker Docker image"
    echo "Using custom worker image: ${CUSTOM_WORKER_IMAGE}"
    docker pull ${CUSTOM_WORKER_IMAGE}
fi

# Step 9: Running worker Docker container
echo "Step 9/10: Running worker Docker container"
if [ "${CUSTOM_WORKER_IMAGE}" = "" ]; 
then
    # If using default image from Step 8
    docker-compose -f docker-compose-${ENVIRONMENT}.yml run --name=worker_${QUEUE} -e CHALLENGE_QUEUE=${QUEUE} -e CHALLENGE_PK=${PK} -d worker
else
    # If using custom image from worker_image_url
    docker run --name=worker_${QUEUE} -e CHALLENGE_QUEUE=${QUEUE} -e CHALLENGE_PK=${PK} -d ${CUSTOM_WORKER_IMAGE}
fi

# Step 10: Setting up crontab
echo "Step 10/10: Setting up crontab"
echo "@reboot docker restart worker_${QUEUE}" >> workercron
crontab workercron
rm workercron

