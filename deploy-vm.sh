#!/bin/bash
 
# Install requirements (docker)

echo "Step 1"
sudo apt-get remove docker docker-engine docker.io containerd runc -y

echo "Step 2"
sudo apt-get update -y

echo "Step 3"
sudo apt-get install \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common -y

echo "Step 4"
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

echo "Step 5"
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"

echo "Step 7"
sudo apt-get update -y

echo "Step 8"
sudo apt-get install docker-ce docker-ce-cli containerd.io -y

echo "Finished installing docker. Check docker version"
sudo docker --version


echo "Step 1"
sudo curl -L "https://github.com/docker/compose/releases/download/1.26.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

echo "Step 2"
sudo chmod +x /usr/local/bin/docker-compose

echo "Step 3"
sudo docker-compose --version 

# Pull images & run containers 
sudo docker-compose -f docker-compose-local.yml up --build 