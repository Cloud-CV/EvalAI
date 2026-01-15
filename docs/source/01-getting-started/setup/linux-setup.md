# Linux Setup

Running EvalAI on Linux provides the smoothest development experience. Most contributors use Ubuntu or Debian-based distributions.

## Recommendations

For the best experience, we recommend using **Ubuntu 20.04 LTS or newer**.

## Prerequisites

1. **Install Git**:
   ```bash
   sudo apt update
   sudo apt install git
   ```

2. **Install Docker**:
   Follow the [official Docker Engine installation guide for Ubuntu](https://docs.docker.com/engine/install/ubuntu/).
   
   - After installation, add your user to the `docker` group to run docker commands without `sudo`:
     ```bash
     sudo usermod -aG docker $USER
     ```
     *Note: You may need to logout and log back in for this to take effect.*

3. **Install Docker Compose**:
   ```bash
   sudo apt install docker-compose-plugin
   ```

## Setup Instructions

1. **Clone and Navigate**:
   ```bash
   git clone https://github.com/Cloud-CV/EvalAI.git evalai
   cd evalai
   ```

2. **Initialize Environment Variables**:
   Copy the example environment file:
   ```bash
   cp docker/dev/docker.env .env
   ```

3. **Run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

## Troubleshooting Linux Specifics

### Permissions Issue
If you see `Permission Denied` when running `docker-compose`, ensure your user is in the `docker` group and you have restarted your session.

### Firewall (UFW)
If you cannot access `localhost:8888`, ensure your firewall isn't blocking the ports:
```bash
sudo ufw allow 8000/tcp
sudo ufw allow 8888/tcp
```

For more detailed Docker instructions, see the [Docker Setup](docker-setup.md) page.
