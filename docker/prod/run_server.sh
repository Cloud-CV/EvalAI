#!/bin/bash
# Server setup script
# Author: Deshraj

echo "Running the image and starting redis server."
if [ "$1" == "run" ] 
then
    sudo docker create -v $PWD/..:/evalai --name evalai_code evalai/code /bin/true

    sudo docker $1 -d --name evalai_redis redis

    # echo "Running the image and starting rabbitmq server."
    # sudo docker $1 -d --name evalai_rabbitmq rabbitmq

    echo "Running the image and starting django server"
    sudo docker $1 -d --volumes-from evalai_code --link evalai_redis:redis --name evalai_django evalai/django uwsgi --emperor /evalai/

    echo "Running the image and starting celery worker"
    docker run --link evalai_redis:redis -e CELERY_BROKER_URL=redis://redis --name evalai_celery -d celery

    echo "Running the image and starting nginx server"
    sudo docker $1 -d -p $2:80 -p $3:443 --volumes-from evalai_code --name evalai_nginx --link evalai_node:node --link evalai_redis:redis --link evalai_django:django evalai/nginx
else
    echo "Restarting redis server"
    sudo docker restart evalai_redis
    echo "Restarting celery server"
    sudo docker restart evalai_celery
    echo "Restarting django server"
    sudo docker restart evalai_django
    echo "Restarting nginx server"
    sudo docker restart evalai_nginx 
fi