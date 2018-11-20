#!/bin/bash
set -e

opt=${1}
env=${2}

requirements() {
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

if python3 -c "import awscli" &> /dev/null; then
    aws configure set default.region us-east-1
    eval $(aws ecr get-login --no-include-email)
else
    echo "Updating and Installing dependencies..."
    requirements;
fi

case $opt in
        pull)
            source ~/.bashrc
            echo "Pulling environment variables file..."
            aws s3 cp s3://cloudcv-secrets/evalai/${env}/docker_${env}.env ./docker/prod/docker_${env}.env
            echo "Environment varibles file successfully downloaded."
            if [ ${env} == "production" ]; then
                echo "Pulling ssl certificates and nginx configuration..."
                aws s3 cp s3://cloudcv-secrets/evalai/${env}/ssl/ ./ssl/
                aws s3 cp s3://cloudcv-secrets/evalai/${env}/nginx_${env}.conf ./docker/prod/nodejs/nginx_${env}.conf
            fi
            echo "Pulling docker images from ECR..."
            docker-compose -f docker-compose-${env}.yml pull
            echo "Completed Pull operation."
            ;;
        deploy)
            echo "Deploying docker container..."
            docker-compose -f docker-compose-${env}.yml up -d
            echo "Completed Pull operation."
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
            ;;
        install)
            echo "Updating and Installing dependencies..."
            requirements;
            ;;
        locale)
            export LC_ALL="en_US.UTF-8"
            export LC_CTYPE="en_US.UTF-8"
            sudo apt-get update
            ;;
        aws_config)
            echo "Configuring AWS Account ID and Commit Id..."
            export COMMIT_ID=${3}
            export AWS_ACCOUNT_ID=${4}
            echo COMMIT_ID=${3} >> ~/.bashrc
            if [ ${AWS_ACCOUNT_ID} ]; then
                echo "AWS Account ID is already configured."
            else
                if [ -z "$4" ]; then
                        echo "Add AWS Account Id as an argument"
                        exit 1
                else
                        echo AWS_ACCOUNT_ID=${4} >> ~/.bashrc
                fi
            fi
            if [ -z "$3" ]; then
                echo "Add commit id as an argument or you can use 'latest'"
                exit 1
            fi
            source ~/.bashrc
            echo "AWS Account Id and Commit ID successfully configured."
            ;;
        *)
        echo "EvalAI deployment utility script"
        echo " Usage: $0 {pull|deploy|scale|clean|copy}"
        echo
        echo "	pull  : Pull docker images from ECR."
        echo "		Eg. ./scripts/deployment/deploy.sh pull production"
        echo "	deploy : Deploy containers in the respective environment."
        echo "		Eg. ./scripts/deployment/deploy.sh deploy production"
        echo "	scale  : Scale particular docker service in an environment."
        echo "		Eg. ./scripts/deployment/deploy.sh scale production django 5"
        echo "	clean  : Remove all docker containers and images."
        echo "		Eg. ./scripts/deployment/deploy.sh clean production"
esac
