# Manual Setup

While Docker is recommended, you can set up EvalAI manually on your host machine. This is useful for deep debugging of specific components.

## Prerequisites

Ensure the following are installed and configured:

- **Python 3.9**: [Download Python](https://www.python.org/downloads/)
- **Node.js 18**: [Download Node.js](https://nodejs.org/en/download/)
- **PostgreSQL**: [Download PostgreSQL](https://www.postgresql.org/download/)
- **AWS CLI**: Required for SQS/ElasticMQ interactions.
- **Bower & Gulp**: Install globally via npm:
  ```bash
  npm install -g bower gulp gulp-cli
  ```

## Backend Setup (Django)

1. **Create a Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements/dev.txt
   ```

3. **Database Configuration**:
   - Create a PostgreSQL database named `evalai`.
   - Setup environment variables:
     ```bash
     export POSTGRES_NAME=evalai
     export POSTGRES_USER=your_user
     export POSTGRES_PASSWORD=your_password
     export POSTGRES_HOST=localhost
     export POSTGRES_PORT=5432
     ```

4. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Start Django Server**:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

## Frontend Setup (Node.js)

1. **Install NPM Packages**:
   ```bash
   npm install
   ```

2. **Install Bower Components**:
   ```bash
   bower install --allow-root
   ```

3. **Start Development Server**:
   ```bash
   gulp dev:runserver
   ```
   The frontend will be available at [http://localhost:8888](http://localhost:8888).

## Additional Components

### SQS / ElasticMQ
EvalAI uses SQS for managing submission queues. For local development, you should run [ElasticMQ](https://github.com/softwaremill/elasticmq) which provides an SQS-compatible interface.

### Workers
To process submissions manually, you need to run the worker scripts located in `scripts/workers/`.

> [!WARNING]
> Manual setup is complex and prone to environment-specific issues. If you encounter difficulties, we strongly recommend using the [Docker Setup](docker-setup.md).
