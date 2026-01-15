# Windows Setup

Setting up EvalAI on Windows is easiest using Docker Desktop. We highly recommend using **WSL2 (Windows Subsystem for Linux)** for a better experience.

## Prerequisites

1. **Install Git for Windows**: Download and install from [git-scm.com](https://git-scm.com/download/win).
2. **Install Docker Desktop**: 
   - Download from [Docker Hub](https://www.docker.com/products/docker-desktop).
   - During installation, ensure the **"Use WSL 2 instead of Hyper-V"** option is selected.
3. **WSL2**:
   - Install a Linux distribution (like Ubuntu) from the Microsoft Store.
   - Set up Docker Desktop to integrate with your WSL2 distro in **Settings > Resources > WSL Integration**.

## Setup Instructions

### Option 1: Using WSL2 (Highly Recommended)

1. Open your WSL2 terminal (e.g., Ubuntu).
2. Follow the [Linux Setup Guide](linux-setup.md).

### Option 2: Using PowerShell/Command Prompt

1. **Clone the Repository**:
   ```powershell
   git clone https://github.com/Cloud-CV/EvalAI.git evalai
   cd evalai
   ```

2. **Initialize Environment Variables**:
   In PowerShell:
   ```powershell
   copy docker/dev/docker.env .env
   ```

3. **Run with Docker Compose**:
   ```powershell
   docker-compose up --build
   ```

## Troubleshooting Windows Specifics

### WSL2 Memory Usage
WSL2 can sometimes consume a lot of RAM. You can limit it by creating a `.wslconfig` file in your `%UserProfile%` folder:
```ini
[wsl2]
memory=4GB
```

### Path Length Issues
If you encounter errors related to long file paths during `git clone`, run this command in an elevated PowerShell:
```powershell
git config --global core.longpaths true
```

### CRLF vs LF
Windows uses different line endings (CRLF) than Linux (LF). This can cause issues with scripts inside Docker containers. Ensure your git is configured to handle this:
```powershell
git config --global core.autocrlf input
```

For more detailed Docker instructions, see the [Docker Setup](docker-setup.md) page.
