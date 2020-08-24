#!/bin/bash


if ! [[ $(sudo which docker) && $(sudo docker --version) ]]; then   #[ -x "$(command -v docker)" ];
    # Install requirements (docker)
    echo "### Removing existing docker libs"
    sudo apt-get remove docker docker-engine docker.io containerd runc -y
    sudo apt-get update -y

    echo "### Installing docker requirements"
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

    echo "### Installing docker"
    sudo apt-get install docker-ce docker-ce-cli containerd.io -y

    echo "### Finished installing docker. Check docker version"
    sudo docker --version

fi

if ! [[ $(sudo which docker-compose) && $(sudo docker-compose --version) ]]; then   #[ -x "$(command -v docker)" ];

    echo "### Installing docker-compose"
    sudo curl -L "https://github.com/docker/compose/releases/download/1.26.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose

    echo "### Finished installing docker-compose. Check docker-compose version"
    sudo docker-compose --version 

fi

touch .env

read -p "Enter domain name (evalai.example.com) : " DOMAIN_NAME

echo "DOMAIN_NAME=$DOMAIN_NAME" > .env

DOCKER_COMPOSE_FILE=""

read -p "Do you want to enable automatic HTTPs with certbot ? (y/N) " decision
if [ "$decision" != "Y" ] && [ "$decision" != "y" ]; then

    # Normal HTTP
    DOCKER_COMPOSE_FILE="docker-compose-vm-http.yml"

else

    # HTTPs
    echo "### Initiating letsencrypt with certbot"
    chmod +x init-letsencrypt.sh
    ./init-letsencrypt.sh

    DOCKER_COMPOSE_FILE="docker-compose-vm.yml"
    
fi

# Pull images & run containers 
sudo docker-compose -f ${DOCKER_COMPOSE_FILE} up -d --build

# Restore database
sudo mkdir backups
DOCKER_DB_NAME="$(sudo docker-compose -f ${DOCKER_COMPOSE_FILE} ps -q db)"
LOCAL_DUMP_PATH=$(ls -t backups/* | head -1)

if [ -n "${DUMP_FILE}" ]
then    
    echo "# Backup file exists: ${DUMP_FILE}"
    echo "# Restoring latest postgres backup"
    sudo docker exec -it "${DOCKER_DB_NAME}" gunzip -c "${LOCAL_DUMP_PATH}" | psql -h db -p 5432 -U postgres -d postgres
else
    echo "# No backup file exists"
fi
