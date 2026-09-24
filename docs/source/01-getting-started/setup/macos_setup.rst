macOS Setup Guide
=================

EvalAI on macOS works using Docker Desktop.

Prerequisites
--------------

- Docker Desktop
- Git
- Homebrew (optional for installing Docker)

Install Docker Desktop from:

https://www.docker.com/products/docker-desktop

If using Homebrew:

brew install --cask docker

Verify installation:

docker --version  
docker-compose --version  

Setup Steps
------------

1. Clone the EvalAI repository:

git clone https://github.com/Cloud-CV/EvalAI.git  
cd EvalAI  

2. Run the platform using:

docker-compose up --build  

3. Open your browser and go to:

http://localhost:8080  

Notes
------

Docker ensures consistent setup across all macOS versions. Manual installation without Docker is not officially supported.
