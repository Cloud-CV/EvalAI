#!/bin/bash
set -e

opt=${1}
env=${2}

aws_login() {
    aws configure set default.region us-east-1
    eval $(aws ecr get-login --no-include-email)
}

setup() {
    export LC_ALL="en_US.UTF-8"
    export LC_CTYPE="en_US.UTF-8"
    sudo add-apt-repository ppa:deadsnakes/ppa
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    sudo apt-get update
    apt-cache policy docker-ce
    sudo apt-get install -y docker-ce
    sudo apt-get install python3.6
    sudo apt-get install python3-pip
    pip3 install awscli
    pip3 install docker-compose
}

if ! python3 -c "import awscli" &> /dev/null; then
    echo "Installing packages and dependencies..."
    setup;
fi

if [ -z ${AWS_ACCOUNT_ID} ]; then
    echo "AWS_ACCOUNT_ID not set."
    exit 0
fi

if [ -z ${COMMIT_ID} ]; then
    export COMMIT_ID="latest"
fi

case $opt in
        pull)
            aws_login;
            echo "Pulling environment variables file..."
            aws s3 cp s3://cloudcv-secrets/evalai/${env}/docker_${env}.env ./docker/prod/docker_${env}.env
            echo "Environment varibles file successfully downloaded."
            if [ ${env} == "production" ]; then
                echo "Pulling ssl certificates and nginx configuration..."
                aws s3 cp s3://cloudcv-secrets/evalai/${env}/ssl/ ./ssl/ --recursive
                aws s3 cp s3://cloudcv-secrets/evalai/${env}/nginx_${env}.conf ./docker/prod/nodejs/nginx_${env}.conf
            fi
            echo "Pulling docker images from ECR..."
            docker-compose -f docker-compose-${env}.yml pull
            echo "Completed Pull operation."
            ;;
        deploy-django)
            echo "Deploying django docker container..."
            docker-compose -f docker-compose-${env}.yml up -d django
            echo "Completed deploy operation."
            ;;
        deploy-nodejs)
            echo "Deploying nodejs docker container..."
            docker-compose -f docker-compose-${env}.yml up -d nodejs
            echo "Completed deploy operation."
            ;;
        deploy-worker)
            token=${3}
            echo "Pulling queue names for $env server challenges..."
            if [ ${env} == "staging" ]; then
                queue_names=$(curl -L -X GET -H "Authorization: Token $token" http://staging.evalai.cloudcv.org/api/challenges/get_broker_urls) | tr -d '[],'
            elif [ ${env} == "production" ]; then
                queue_names=$(curl -L -X GET -H "Authorization: Token $token" http://evalai.cloudcv.org/api/challenges/get_broker_urls)| tr -d '[],'
            fi
            echo "Completed pulling Queue list"
            for queue_name in $queue_names; do
                echo "Deploying worker for queue...", $queue_name
                CHALLENGE_QUEUE=$queue_name docker-compose -f docker-compose-${env}.yml up -d worker
                echo "Deployed worker docker container"
            done
            ;;
        scale)
            service=${3}
            instances=${4}
            echo "Scaling the containers..."
            docker-compose -f docker-compose-${env}.yml scale ${service}=${instances}
            ;;
        clean)
            {
                docker-compose -f docker-compose-${env}.yml rm -s -v -f
            } || {
                echo "Delete operation skipped since no container or image found!"
            }
            docker rmi $(docker images -a -q)
            echo "Sucessfully cleaned all the images."
            ;;
        *)
        echo "EvalAI deployment utility script"
        echo " Usage: $0 {pull|deploy|scale|clean}"
        echo
        echo "    pull  : Pull docker images from ECR."
        echo "        Eg. ./scripts/deployment/deploy.sh pull production"
        echo "    deploy-django : Deploy django containers in the respective environment."
        echo "        Eg. ./scripts/deployment/deploy.sh deploy-django production"
        echo "    deploy-nodejs : Deploy nodejs containers in the respective environment."
        echo "        Eg. ./scripts/deployment/deploy.sh deploy-nodejs production"
        echo "    deploy-worker : Deploy worker containers in the respective environment."
        echo "        Eg. ./scripts/deployment/deploy.sh deploy production <superuser_auth_token>"
        echo "    scale  : Scale particular docker service in an environment."
        echo "        Eg. ./scripts/deployment/deploy.sh scale production django 5"
        echo "    clean  : Remove all docker containers and images."
        echo "        Eg. ./scripts/deployment/deploy.sh clean production"
esac
