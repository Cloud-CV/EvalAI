# Stage 1: Build stage with build dependencies
FROM python:3.9.21-slim-bullseye AS builder

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Copy requirements first for better layer caching
COPY requirements/ /code/requirements/

# Install Python dependencies with BuildKit cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --no-compile -r requirements/code_upload_worker.txt && \
    # Clean up pip cache and Python bytecode (directories first, then files)
    rm -rf /root/.cache/pip && \
    find /usr/local/lib/python3.9/site-packages -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.9/site-packages \( -name "*.pyc" -o -name "*.pyo" \) -delete 2>/dev/null || true

# Stage 2: Runtime stage - minimal dependencies
FROM python:3.9.21-slim-bullseye

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /code

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy unzip binary from builder stage (faster than apt-get)
COPY --from=builder /usr/bin/unzip /usr/bin/unzip

# Copy application code
COPY . /code/

# Set execute permission for install script
RUN chmod +x scripts/workers/code_upload_worker_utils/install_dependencies.sh

CMD ["scripts/workers/code_upload_worker_utils/install_dependencies.sh"]
