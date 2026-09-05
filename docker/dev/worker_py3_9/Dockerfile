# Stage 1: Build stage with all build dependencies
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

# Install all build dependencies
# deb.debian.org (Fastly) intermittently resets connections, and sporadically
# returns 404 for pool files that do exist -- the same URL serves fine minutes
# later. Acquire::Retries handles the transport errors, but apt treats 404 as
# fatal and will not retry it, so retry the whole update+install with a pause.
# Bounded and guarded with 'exit 1', so a genuinely missing package still fails
# the build rather than silently continuing without it.
# Do not "fix" this by pointing at another mirror: security.debian.org and
# cloudfront.debian.net were each measured, at different times, to 404 on
# bullseye-security pool files that deb.debian.org served correctly, and vice
# versa -- there is no single mirror that is reliably the clean one.
RUN n=0; until [ "$n" -ge 4 ]; do \
        apt-get -o Acquire::Retries=5 update && \
        apt-get -o Acquire::Retries=5 install -y --no-install-recommends \
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
        && break; \
        n=$((n+1)); \
        echo "apt failed (attempt $n), retrying in 20s" >&2; \
        sleep 20; \
    done; \
    [ "$n" -lt 4 ] || exit 1; \
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
RUN n=0; until [ "$n" -ge 4 ]; do \
        apt-get -o Acquire::Retries=5 update && \
        apt-get -o Acquire::Retries=5 install -y --no-install-recommends \
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
        libglib2.0-0 \
        && break; \
        n=$((n+1)); \
        echo "apt failed (attempt $n), retrying in 20s" >&2; \
        sleep 20; \
    done; \
    [ "$n" -lt 4 ] || exit 1; \
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
