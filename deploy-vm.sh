#!/bin/bash
 
# Install requirements (docker)
echo "Removing existing docker libs"
sudo apt-get remove docker docker-engine docker.io containerd runc -y
sudo apt-get update -y

echo "Installing docker requirements"
sudo apt-get install \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common -y
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
sudo apt-get update -y

echo "Installing docker"
sudo apt-get install docker-ce docker-ce-cli containerd.io -y

echo "Finished installing docker. Check docker version"
sudo docker --version


echo "Installing docker-compose"
sudo curl -L "https://github.com/docker/compose/releases/download/1.26.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

echo "Finished installing docker-compose. Check docker-compose version"
sudo docker-compose --version 

# Pull images & run containers 
sudo docker-compose -f docker-compose-local.yml up -d

#Restore database
DOCKER_DB_NAME="$(docker-compose ps -q db)"
LOCAL_DUMP_PATH=$(ls -t backups/* | head -1)

if [ -n "${DUMP_FILE}" ]
then    
    echo "Backup file exists: ${DUMP_FILE}"
    echo "Restoring latest postgres backup"
    sudo docker exec -it "${DOCKER_DB_NAME}" gunzip -c "${LOCAL_DUMP_PATH}" | psql -h db -p 5432 -U postgres -d postgres
else
    echo "No backup file exists"
fi
