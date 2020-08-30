#!/bin/bash

read -p "Skip reading variable (not for first time usage)? (y/N) " skip_input
if [ "$skip_input" != "Y" ] && [ "$skip_input" != "y" ]; then
    touch .env

    read -p "Enter AWS Access key ID : " AWS_ACCESS_KEY_ID
    echo "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID" > .env

    read -p "Enter AWS Account ID : " AWS_ACCOUNT_ID
    echo "AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID" >> .env

    read -p "Enter AWS Default Region (eg: us-east-1) : " AWS_DEFAULT_REGION
    echo "AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION" >> .env

    read -p "Enter AWS secret access key : " AWS_SECRET_ACCESS_KEY
    echo "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY" >> .env

    read -p "Enter your domain name (example.com) : " DOMAIN_NAME
    echo "DOMAIN_NAME=$DOMAIN_NAME" >> .env

    read -p "Enter RDS Hostname : " RDS_HOSTNAME
    echo "RDS_HOSTNAME=$RDS_HOSTNAME" >> .env

    read -p "Enter RDS DB Name : " RDS_DB_NAME
    echo "RDS_DB_NAME=$RDS_DB_NAME" >> .env

    read -p "Enter RDS Username : " RDS_USERNAME
    echo "RDS_USERNAME=$RDS_USERNAME" >> .env

    read -p "Enter RDS Password : " RDS_PASSWORD
    echo "RDS_PASSWORD=$RDS_PASSWORD" >> .env

    read -p "Enter AWS S3 Bucket Name: " AWS_STORAGE_BUCKET_NAME
    echo "AWS_STORAGE_BUCKET_NAME=$AWS_STORAGE_BUCKET_NAME" >> .env

    read -p "Enter AWS SES Region Name (eg : us-east-1): " AWS_SES_REGION_NAME
    echo "AWS_SES_REGION_NAME=$AWS_SES_REGION_NAME" >> .env

    read -p "Enter AWS SES Region Endpoint (eg : email.us-east-1.amazonaws.com): " AWS_SES_REGION_ENDPOINT
    echo "AWS_SES_REGION_ENDPOINT=$AWS_SES_REGION_ENDPOINT" >> .env

    read -p "Enter Email Host (eg : email-smtp.us-east-1.amazonaws.com) : " EMAIL_HOST
    echo "EMAIL_HOST=$EMAIL_HOST" >> .env

    read -p "Enter Email Host User : " EMAIL_HOST_USER
    echo "EMAIL_HOST_USER=$EMAIL_HOST_USER" >> .env

    read -p "Enter Email Host Password : " EMAIL_HOST_PASSWORD
    echo "EMAIL_HOST_PASSWORD=$EMAIL_HOST_PASSWORD" >> .env

    read -p "Enter Sentry URL : " SENTRY_URL
    echo "SENTRY_URL=$SENTRY_URL" >> .env

    read -p "Enter ECS Cluster Name : " CLUSTER
    echo "CLUSTER=$CLUSTER" >> .env

    read -p "Enter ECS Execution Role ARN (eg : arn:aws:iam::{account_id}:role/ecsTaskExecutionRole) : " EXECUTION_ROLE_ARN
    echo "EXECUTION_ROLE_ARN=$EXECUTION_ROLE_ARN" >> .env

    read -p "Enter Subnet 1 ID : " SUBNET_1
    echo "SUBNET_1=$SUBNET_1" >> .env

    read -p "Enter Subnet 2 ID : " SUBNET_2
    echo "SUBNET_2=$SUBNET_2" >> .env

    read -p "Enter Subnet Security Group ID : " SUBNET_SECURITY_GROUP
    echo "SUBNET_SECURITY_GROUP=$SUBNET_SECURITY_GROUP" >> .env

    read -p "Enter Worker Image (yashdusing/evalai-aws-worker:latest) : " WORKER_IMAGE
    echo "WORKER_IMAGE=$WORKER_IMAGE" >> .env

    DJANGO_SERVER="evalapi.${DOMAIN_NAME}"
    echo "DJANGO_SERVER=$DJANGO_SERVER" >> .env

    HOSTNAME="evalai.${DOMAIN_NAME}"
    echo "HOSTNAME=$HOSTNAME" >> .env

    DOCKER_COMPOSE_FILE="scripts/ec2_deployment/docker-compose-aws.yml"
    echo "DOCKER_COMPOSE_FILE=$DOCKER_COMPOSE_FILE" >> .env

fi