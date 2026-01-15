# Installation

Getting EvalAI up and running on your local machine is straightforward. We offer several ways to set up the environment depending on your operating system and preferences.

## Quick Start (Docker)

The fastest way to get started is using Docker. Ensure you have [Docker](https://docs.docker.com/install/) and [Docker Compose](https://docs.docker.com/compose/install/) installed.

```shell
git clone https://github.com/Cloud-CV/EvalAI.git evalai && cd evalai
docker-compose up --build
```

## Platform-Specific Guides

For detailed prerequisites and step-by-step instructions for your specific environment, please refer to the following guides:

- [Docker Setup](setup/docker-setup.md): Comprehensive guide for Docker-based installation.
- [Linux Setup](setup/linux-setup.md): Best practices for Ubuntu and other Linux distributions.
- [Windows Setup](setup/windows-setup.md): Instructions for WSL2 and Docker Desktop on Windows.
- [macOS Setup](setup/macos-setup.md): Setup for Intel and Apple Silicon Macs.
- [Manual Setup](setup/manual-setup.md): For developers who want to run components natively.

## Default User Credentials

Once the system is running at [http://127.0.0.1:8888](http://127.0.0.1:8888), you can use these accounts:

| User Type | Username | Password |
| :--- | :--- | :--- |
| **Superuser** | `admin` | `password` |
| **Host User** | `host` | `password` |
| **Participant** | `participant` | `password` |

## Troubleshooting

If you encounter any issues during installation, please see our [Common Errors](../07-troubleshooting/index.md) page or visit the [FAQ](../08-reference/faq(developers).md).
