#!/bin/bash
set -e

opt=${1}

aws_login() {
    aws configure set default.region us-east-1
    eval $(aws ecr get-login --no-include-email)
}

if [ -z ${AWS_ACCOUNT_ID} ]; then
    echo "AWS_ACCOUNT_ID not set."
    exit 0
fi

if [ -z ${COMMIT_ID} ]; then
    export COMMIT_ID="latest"
fi

if [ -z ${TRAVIS_BRANCH} ]; then
    echo "Please set the TRAVIS_BRANCH first."
fi

env=${TRAVIS_BRANCH}
JUMPBOX=${JUMPBOX_INSTANCE}

if [[ ${env} == "production" ]]; then
    INSTANCE=${PRODUCTION_INSTANCE}
elif [[ ${env} == "staging" ]]; then
    INSTANCE=${STAGING_INSTANCE}
else
    echo "Skipping deployment since commit not on staging or production branch."
    exit 0
fi

case $opt in
        auto_deploy)
            chmod 400 scripts/deployment/evalai.pem
            ssh-add scripts/deployment/evalai.pem
			ssh -A ubuntu@${JUMPBOX} -o StrictHostKeyChecking=no INSTANCE=${INSTANCE} AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID} COMMIT_ID=${COMMIT_ID} env=${env} 'bash -s' <<-'ENDSSH'
				ssh ubuntu@${INSTANCE} -o StrictHostKeyChecking=no AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID} COMMIT_ID=${COMMIT_ID} env=${env} 'bash -s' <<-'ENDSSH2'
					source venv/bin/activate
					cd ~/Projects/EvalAI
					export AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID}
					export COMMIT_ID=${COMMIT_ID}
					eval $(aws ecr get-login --no-include-email)
					aws s3 cp s3://cloudcv-secrets/evalai/${env}/docker_${env}.env ./docker/prod/docker_${env}.env
					docker-compose -f docker-compose-${env}.yml rm -s -v -f
					docker-compose -f docker-compose-${env}.yml pull
					docker-compose -f docker-compose-${env}.yml up -d --force-recreate --remove-orphans django nodejs nodejs_v2 celery
				ENDSSH2
			ENDSSH
            ;;
        pull)
            aws_login;
            echo "Pulling environment variables file..."
            aws s3 cp s3://cloudcv-secrets/evalai/${env}/docker_${env}.env ./docker/prod/docker_${env}.env
            echo "Environment varibles file successfully downloaded."
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
        deploy-nodejs-v2)
            echo "Deploying new frontend docker container..."
            docker-compose -f docker-compose-${env}.yml up -d nodejs_v2
            echo "Completed deploy operation."
            ;;
        deploy-celery)
            echo "Deploying celery docker container..."
            docker-compose -f docker-compose-${env}.yml up -d celery
            echo "Completed deploy operation."
            ;;
        deploy-worker)
            token=${3}
            challenge=${4}
            if [ -z "$4" ]; then
               echo "Please input Challenge ID"
               exit 0
            fi
            echo "Pulling queue name for $env server challenge..."
            if [ ${env} == "staging" ]; then
                queue_name=$(curl -k -L -X GET -H "Authorization: Token $token" https://staging.eval.ai/api/challenges/get_broker_url/$challenge/)
            elif [ ${env} == "production" ]; then
                queue_name=$(curl -k -L -X GET -H "Authorization: Token $token" https://eval.ai/api/challenges/get_broker_url/$challenge/)
            fi
            echo "Completed pulling Queue name"
            # preprocess the python list to bash array
            queue_name=($(echo ${queue_name//,/ } | tr -d '[]'))
            queue=$(echo $queue_name | tr -d '"')
            echo "Deploying worker for queue: " $queue
            docker-compose -f docker-compose-${env}.yml run --name=worker_${queue} -e CHALLENGE_QUEUE=$queue -e CHALLENGE_PK=$challenge -d worker
            echo "Deployed worker docker container for queue: " $queue
            ;;
        deploy-remote-worker)
            token=${3}
            broker_url=${4}
            if [ -z "$3" ]; then
               echo "Please input Auth Token"
               exit 0
            fi
            if [ -z "$4" ]; then
               echo "Please input Broker URL"
               exit 0
            fi
            echo "Deploying worker for queue: " $queue
            docker-compose -f docker-compose-${env}.yml run --name=remote_worker_${queue} -e QUEUE_NAME=$queue -e AUTH_TOKEN=$token -d worker
            echo "Deployed worker docker container for queue: " $queue
            ;;
        deploy-workers)
            token=${3}
            echo "Pulling queue names for $env server challenges..."
            if [ ${env} == "staging" ]; then
                queue_names=$(curl -k -L -X GET -H "Authorization: Token $token" https://staging.eval.ai/api/challenges/get_broker_urls/)
            elif [ ${env} == "production" ]; then
                queue_names=$(curl -k -L -X GET -H "Authorization: Token $token" https://eval.ai/api/challenges/get_broker_urls/)
            fi
            echo "Completed pulling Queue list"
            # preprocess the python list to bash array
            queue_names=($(echo ${queue_names//,/ } | tr -d '[]'))
            for queue_name in "${queue_names[@]}"
            do
                queue=$(echo $queue_name | tr -d '"')
                echo "Deploying worker for queue: " $queue
                docker-compose -f docker-compose-${env}.yml run --name=worker_${queue} -e CHALLENGE_QUEUE=$queue -d worker
                echo "Deployed worker docker container for queue: " $queue
             done
            ;;
        deploy-prometheus)
            echo "Deploying prometheus docker container..."
            docker-compose -f docker-compose-${env}.yml up -d prometheus
            echo "Completed deploy operation."
            ;;
        deploy-grafana)
            echo "Deploying grafana docker container..."
            docker-compose -f docker-compose-${env}.yml up -d grafana
            echo "Completed deploy operation."
            ;;
        deploy-statsd)
            echo "Deploying statsd docker container..."
            docker-compose -f docker-compose-${env}.yml up -d statsd-exporter
            echo "Completed deploy operation."
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
        echo "    auto_deploy : Deploy staging or production branch to staging or production server respectively."
        echo "        Eg. ./scripts/deployment/deploy.sh auto_deploy"
        echo "    pull : Pull docker images from ECR."
        echo "        Eg. ./scripts/deployment/deploy.sh pull production"
        echo "    deploy-django : Deploy django containers in the respective environment."
        echo "        Eg. ./scripts/deployment/deploy.sh deploy-django production"
        echo "    deploy-nodejs : Deploy nodejs containers in the respective environment."
        echo "        Eg. ./scripts/deployment/deploy.sh deploy-nodejs production"
        echo "    deploy-nodejs-v2 : Deploy new frontend container in the respective environment."
        echo "        Eg. ./scripts/deployment/deploy.sh deploy-nodejs-v2 production"
        echo "    deploy-celery : Deploy celery containers in the respective environment."
        echo "        Eg. ./scripts/deployment/deploy.sh deploy-celery production"
        echo "    deploy-worker : Deploy worker container for a challenge using challenge pk."
        echo "        Eg. ./scripts/deployment/deploy.sh deploy-worker production <superuser_auth_token> <challenge_pk>"
        echo "    deploy-remote-worker : Deploy remote worker container for a challenge using host auth token and challenge queue name."
        echo "        Eg. ./scripts/deployment/deploy.sh deploy-remote-worker production <auth_token> <queue_name>"   
        echo "    deploy-workers : Deploy worker containers in the respective environment."
        echo "        Eg. ./scripts/deployment/deploy.sh deploy production <superuser_auth_token>"
        echo "    deploy-prometheus : Deploy prometheus container in the respective environment."
        echo "        Eg. ./scripts/deployment/deploy.sh deploy-prometheus production"
        echo "    deploy-grafana : Deploy grafana container in the respective environment."
        echo "        Eg. ./scripts/deployment/deploy.sh deploy-grafana production"
        echo "    deploy-statsd : Deploy statsd container in the respective environment."
        echo "        Eg. ./scripts/deployment/deploy.sh deploy-statsd production"
        echo "    scale  : Scale particular docker service in an environment."
        echo "        Eg. ./scripts/deployment/deploy.sh scale production django 5"
        echo "    clean  : Remove all docker containers and images."
        echo "        Eg. ./scripts/deployment/deploy.sh clean production"
esac
