# Stage 1: Build stage with all build dependencies
FROM python:3.9.21-slim-bullseye AS builder

# Fast dependency installs via uv (drop-in for pip); the binary lives at /uv in
# the builder stage only and is never copied into the runtime image.
COPY --from=ghcr.io/astral-sh/uv:0.12.9 /uv /uv

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install all build dependencies
# Add retry logic and --fix-missing to handle transient network issues
# Fix any broken dependencies first (from partial installs)
RUN apt-get update && \
    apt --fix-broken install -y || true && \
    (apt-get install -y --no-install-recommends --fix-missing \
     build-essential \
     python3-dev \
     libpq-dev \
     libcurl4-openssl-dev \
     libssl-dev \
     libjpeg-dev \
     zlib1g-dev \
     libpng-dev \
     libtiff-dev \
     libfreetype6-dev \
     liblcms2-dev \
     libwebp-dev \
     default-jre-headless \
     curl \
     || (apt-get update && \
         apt --fix-broken install -y || true && \
         apt-get install -y --no-install-recommends --fix-missing \
         build-essential \
         python3-dev \
         libpq-dev \
         libcurl4-openssl-dev \
         libssl-dev \
         libjpeg-dev \
         zlib1g-dev \
         libpng-dev \
         libtiff-dev \
         libfreetype6-dev \
         liblcms2-dev \
         libwebp-dev \
         default-jre-headless \
         curl)) && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Copy requirements first for better layer caching
COPY requirements/ /code/requirements/

# Install Python dependencies with BuildKit cache mount
# Install prerequisite packages first (needed for compiling native extensions)
RUN --mount=type=cache,target=/root/.cache/pip \
    /uv pip install --system --no-cache -U cffi service_identity cython==0.29.36 setuptools==57.5.0 && \
    /uv pip install --system --no-cache -r requirements/dev.txt && \
    /uv pip install --system --no-cache -r requirements/worker_py3_9.txt

# Best-effort bytecode cleanup; keep separate so pip failures fail the build.
RUN rm -rf /root/.cache/pip && \
    find /usr/local/lib/python3.9/site-packages -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.9/site-packages \( -name "*.pyc" -o -name "*.pyo" \) -delete 2>/dev/null || true

# Verify worker runtime imports required by submission_worker.py.
RUN python -c "import boto3, botocore, django, requests, yaml"

# Stage 2: Runtime stage - minimal dependencies only
FROM python:3.9.21-slim-bullseye

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install runtime dependencies (apt-get handles multi-arch automatically)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    default-jre-headless \
    libpq5 \
    libcurl4 \
    libjpeg62-turbo \
    zlib1g \
    libpng16-16 \
    libtiff5 \
    libfreetype6 \
    liblcms2-2 \
    libwebp6 \
    libgl1 \
    libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apt/*

WORKDIR /code

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Force every runtime pip invocation (challenge requirements.txt and the
# evaluation_script __init__.py install() helper) to honor the worker's pinned
# core dependency stack, preventing numpy/scipy ABI breakage.
ENV PIP_CONSTRAINT=/code/requirements/worker_py3_9.txt \
    PIP_BUILD_CONSTRAINT=/code/requirements/worker_py3_9.txt

# Copy application code
COPY . /code/

CMD ["./docker/wait-for-it.sh", "django:8000", "--", "python", "-m", "scripts.workers.submission_worker"]
