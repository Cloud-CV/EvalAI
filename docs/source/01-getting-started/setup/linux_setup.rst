Linux Setup Guide
=================

EvalAI officially supports setup using Docker on all platforms. Manual setup without Docker is not recommended for production environments.

Prerequisites
--------------

- Docker
- Docker Compose
- Git

Install Docker and Docker Compose using:

sudo apt update  
sudo apt install docker.io docker-compose git -y  

Start Docker:

sudo systemctl start docker  
sudo systemctl enable docker  

Verify installation:

docker --version  
docker-compose --version  

Setup Steps
------------

1. Clone the EvalAI repository:

git clone https://github.com/Cloud-CV/EvalAI.git  
cd EvalAI  

2. Run the platform using Docker:

docker-compose up --build  

3. Open your browser and go to:

http://localhost:8080  

Notes
------

Docker-based installation ensures consistent setup across all Linux distributions.
