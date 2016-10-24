# Server setup script
# Author: Deshraj

echo "Creating base image"
docker build -t evalai/base ./base/

echo "Creating data container"
docker build --no-cache -t evalai/code ./code/

echo "Pulling the image and starting redis server."
docker pull redis:3.0

echo "Pulling the celery image"
docker pull celery

# echo "Pulling the image and starting rabbitmq server."
# docker pull rabbitmq

echo "Pulling the image and starting django server"
docker build -t evalai/django ./django/

echo "Pulling the image and starting nginx server"
docker build -t evalai/nginx ./nginx/