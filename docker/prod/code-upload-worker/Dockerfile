# Stage 1: Build stage with build dependencies
FROM python:3.9.21-slim-bullseye AS builder

# Fast dependency installs via uv (drop-in for pip); the binary lives at /uv in
# the builder stage only and is never copied into the runtime image.
COPY --from=ghcr.io/astral-sh/uv:0.12.9@sha256:8b940d3a9d65bed080436972241af2e21c84b5e8c9193f7014ed71479ee795ff /uv /uv

# uv reads its own env, not pip's: match the previous pip timeout and pin the
# build backend so legacy sdists (e.g. django-allauth) build under modern uv.
ENV UV_HTTP_TIMEOUT=100 \
    UV_HTTP_CONNECT_TIMEOUT=100 \
    UV_BUILD_CONSTRAINT=/code/requirements/uv-build-constraints.txt

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install build dependencies
# Add retry logic and --fix-missing to handle transient network issues
# Fix any broken dependencies first (from partial installs)
RUN apt-get update && \
    apt --fix-broken install -y || true && \
    (apt-get install -y --no-install-recommends --fix-missing \
    build-essential \
    unzip \
    || (apt-get update && \
        apt --fix-broken install -y || true && \
        apt-get install -y --no-install-recommends --fix-missing \
        build-essential \
        unzip)) && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Copy requirements first for better layer caching
COPY requirements/ /code/requirements/

# Install Python dependencies with BuildKit cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    /uv pip install --system --no-cache -r requirements/code_upload_worker.txt

# Best-effort bytecode cleanup; keep separate so pip failures fail the build.
RUN find /usr/local/lib/python3.9/site-packages -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.9/site-packages \( -name "*.pyc" -o -name "*.pyo" \) -delete 2>/dev/null || true

# Stage 2: Minimal runtime stage (needs shell for install script, so can't use distroless)
FROM python:3.9.21-slim-bullseye

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install runtime dependencies (apt-get handles multi-arch automatically)
# Note: curl and unzip are needed by install_dependencies.sh; git is required
# for kubectl apply -k with github.com kustomize remote bases.
# Add retry logic and --fix-missing to handle transient network issues
# Fix any broken dependencies first (from partial installs)
RUN apt-get update && \
    apt --fix-broken install -y || true && \
    (apt-get install -y --no-install-recommends --fix-missing \
    curl \
    unzip \
    git \
    ca-certificates \
    || (apt-get update && \
        apt --fix-broken install -y || true && \
        apt-get install -y --no-install-recommends --fix-missing \
        curl \
        unzip \
        git \
        ca-certificates)) && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apt/*

WORKDIR /code

ARG EVALAI_GIT_REVISION=unknown
ENV EVALAI_GIT_REVISION=${EVALAI_GIT_REVISION}

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . /code/

# Set execute permission for install script
RUN chmod +x scripts/workers/code_upload_worker_utils/install_dependencies.sh

CMD ["scripts/workers/code_upload_worker_utils/install_dependencies.sh"]
