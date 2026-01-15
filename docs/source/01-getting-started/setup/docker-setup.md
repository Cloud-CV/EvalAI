# Docker Setup

Setting up EvalAI on your local machine using Docker is the recommended approach. This ensures that all dependencies are correctly configured and avoids version conflicts with your host system.

## Prerequisites

Before you begin, ensure you have the following installed on your machine:

1. **Docker**: Follow the [official Docker installation guide](https://docs.docker.com/get-docker/) for your operating system.
2. **Docker Compose**: Usually included with Docker Desktop for Windows and macOS. Linux users might need to [install it separately](https://docs.docker.com/compose/install/).
3. **Git**: Required to clone the repository.

## Installation Steps

1. **Clone the Repository**:
   Open your terminal and run:
   ```shell
   git clone https://github.com/Cloud-CV/EvalAI.git evalai && cd evalai
   ```

2. **Build and Run Containers**:
   To start the core services (Database, SQS, and Django), run:
   ```shell
   docker-compose up --build
   ```
   > [!NOTE]
   > The first build might take a significant amount of time as it downloads base images and installs all dependencies.

3. **Using Docker Profiles**:
   EvalAI uses Docker profiles to manage optional services. You can include them as needed:
   
   - **Worker Services**: Necessary for processing submissions.
     ```shell
     docker-compose --profile worker up --build
     ```
   - **Statsd Exporter**: For monitoring metrics.
     ```shell
     docker-compose --profile statsd up --build
     ```
   - **Multiple Profiles**: Combined usage.
     ```shell
     docker-compose --profile worker --profile statsd up --build
     ```

## Accessing the Application

Once the containers are up and running, you can access the application at:
[http://127.0.0.1:8888](http://127.0.0.1:8888)

### Default User Credentials

For development, the following users are pre-created:

| User Type | Username | Password |
| :--- | :--- | :--- |
| **Superuser** | `admin` | `password` |
| **Host User** | `host` | `password` |
| **Participant** | `participant` | `password` |

## Common Commands

- **Stop Services**: Press `Ctrl + C` in the terminal where Docker Compose is running, or run `docker-compose stop`.
- **Remove Containers**: `docker-compose down`.
- **View Logs**: `docker-compose logs -f [service_name]`.
- **Run Django Commands**: `docker-compose exec django python manage.py [command]`.

If you encounter any errors, please refer to the [Common Errors during installation](../07-troubleshooting/index.md) page.
