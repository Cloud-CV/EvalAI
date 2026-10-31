Windows Setup Guide
====================

EvalAI setup on Windows is officially supported using Docker Desktop.

Prerequisites
--------------

- Docker Desktop
- Git

Install Docker Desktop from:

https://www.docker.com/products/docker-desktop

After installing Docker, restart your system.

Verify installation using:

docker --version  
docker-compose --version  

Setup Steps
------------

1. Clone the EvalAI repository:

git clone https://github.com/Cloud-CV/EvalAI.git  
cd EvalAI  

2. Start the platform using:

docker-compose up --build  

3. Open your browser and go to:

http://localhost:8080  

Notes
------

Manual non-Docker installation is not officially supported on Windows.
