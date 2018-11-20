#!/bin/bash
set -e

opt=${1}
env=${2}
aws configure set default.region us-east-1
eval $(aws ecr get-login --no-include-email)

case $opt in
        pull)
            echo "Pulling docker images from ECR..."
            aws s3 cp s3://cloudcv-secrets/evalai/${env}/docker_${env}.env ./docker/prod/docker_${env}.env
            if [ ${env} == "production" ]; then
                aws s3 cp s3://cloudcv-secrets/evalai/${env}/ssl/ ./ssl/
                aws s3 cp s3://cloudcv-secrets/evalai/${env}/nginx_${env}.conf ./docker/prod/nodejs/nginx_${env}.conf
            fi
            export COMMIT_ID=${3}
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
            echo "Updating and Installing dependencies"
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
            ;;
        locale)
            export LC_ALL="en_US.UTF-8"
            export LC_CTYPE="en_US.UTF-8"
            sudo dpkg-reconfigure locales
            sudo apt-get update
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
