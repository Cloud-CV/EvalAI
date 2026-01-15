# MacOS Setup

EvalAI runs smoothly on macOS using Docker Desktop.

## Prerequisites

1. **Install Git**: Usually pre-installed. You can also install it via [Homebrew](https://brew.sh/):
   ```bash
   brew install git
   ```

2. **Install Docker Desktop**:
   - Download the installer from the [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop) page.
   - Choose the correct version for your chip: **Intel** or **Apple Silicon (M1/M2/M3)**.

## Setup Instructions

1. **Clone and Navigate**:
   ```bash
   git clone https://github.com/Cloud-CV/EvalAI.git evalai
   cd evalai
   ```

2. **Initialize Environment Variables**:
   ```bash
   cp docker/dev/docker.env .env
   ```

3. **Run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

## macOS Specific Tips

### Apple Silicon (M1/M2/M3)
If you are using a Mac with Apple Silicon, Docker Desktop handles architecture translation automatically. However, for better performance, ensure you have **Rosetta 2** installed:
```bash
softwareupdate --install-rosetta
```

### Resource Allocation
You can adjust the CPU and Memory allocated to Docker in **Settings > Resources**. For building EvalAI, allocating at least 4GB of RAM is recommended.

### File Sharing
Ensure the directory where you cloned EvalAI is included in Docker's File Sharing settings (**Settings > Resources > File Sharing**). By default, `/Users` is usually included.

For more detailed Docker instructions, see the [Docker Setup](docker-setup.md) page.
