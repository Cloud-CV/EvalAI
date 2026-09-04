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
# deb.debian.org (Fastly) intermittently resets connections and 404s pool files;
# Acquire::Retries makes apt retry the fetch instead of failing the build.
# Fix any broken dependencies first (from partial installs)
RUN apt-get -o Acquire::Retries=5 update && \
    apt --fix-broken install -y || true && \
    (apt-get -o Acquire::Retries=5 install -y --no-install-recommends \
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
     git \
     cmake \
     libeigen3-dev \
     libboost-python-dev \
     libopencv-dev \
     python3-opencv \
     libgmp-dev \
     libcgal-qt5-dev \
     swig \
     curl \
     || (apt-get -o Acquire::Retries=5 update && \
         apt --fix-broken install -y || true && \
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
         git \
         cmake \
         libeigen3-dev \
         libboost-python-dev \
         libopencv-dev \
         python3-opencv \
         libgmp-dev \
         libcgal-qt5-dev \
         swig \
         curl)) && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Copy requirements first for better layer caching
COPY requirements/ /code/requirements/

# Install Python dependencies with BuildKit cache mount
# Note: BuildKit cache mount persists outside container, but we clean internal cache for final image size
# Install prerequisite packages first (needed for compiling native extensions)
RUN --mount=type=cache,target=/root/.cache/pip \
    /uv pip install --system --no-cache -U cffi service_identity cython==0.29.36 && \
    /uv pip install --system --no-cache -r requirements/prod.txt && \
    /uv pip install --system --no-cache -r requirements/worker_py3_9.txt

# Best-effort bytecode cleanup; keep separate so pip failures fail the build.
RUN rm -rf /root/.cache/pip && \
    find /usr/local/lib/python3.9/site-packages -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.9/site-packages \( -name "*.pyc" -o -name "*.pyo" \) -delete 2>/dev/null || true

# Verify worker runtime imports required by submission_worker.py.
RUN python -c "import boto3, botocore, django, requests, yaml"

# Collect OpenCV runtime libraries to architecture-independent location
# This allows multi-arch builds (amd64/arm64)
RUN mkdir -p /runtime-libs && \
    cp -P /usr/lib/*/libopencv* /runtime-libs/ 2>/dev/null || true && \
    cp -P /usr/lib/*/libilmbase* /runtime-libs/ 2>/dev/null || true && \
    cp -P /usr/lib/*/libopenexr* /runtime-libs/ 2>/dev/null || true && \
    cp -P /usr/lib/*/libImath* /runtime-libs/ 2>/dev/null || true && \
    cp -P /usr/lib/*/libIex* /runtime-libs/ 2>/dev/null || true && \
    cp -P /usr/lib/*/libIlmThread* /runtime-libs/ 2>/dev/null || true && \
    cp -P /usr/lib/*/libHalf* /runtime-libs/ 2>/dev/null || true

# Stage 2: Runtime stage - minimal dependencies only
FROM python:3.9.21-slim-bullseye

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install runtime dependencies (apt-get handles multi-arch automatically)
# Note: We copy OpenCV libs from builder to avoid python3-opencv dependency issues
# deb.debian.org (Fastly) intermittently resets connections and 404s pool files;
# Acquire::Retries makes apt retry the fetch instead of failing the build.
# Fix any broken dependencies first (from partial installs)
RUN apt-get -o Acquire::Retries=5 update && \
    apt --fix-broken install -y || true && \
    (apt-get -o Acquire::Retries=5 install -y --no-install-recommends \
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
    libgmp10 \
    libgl1 \
    libglib2.0-0 \
    || (apt-get -o Acquire::Retries=5 update && \
        apt --fix-broken install -y || true && \
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
        libgmp10 \
        libgl1 \
        libglib2.0-0)) && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apt/*

WORKDIR /code

# Compare with Django API deployments: CI should inject the same git SHA via
#   docker build ... --build-arg EVALAI_GIT_REVISION="$(git rev-parse HEAD)"
ARG EVALAI_GIT_REVISION=unknown
ENV EVALAI_GIT_REVISION=${EVALAI_GIT_REVISION}

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy OpenCV libraries from builder (architecture-independent path)
COPY --from=builder /runtime-libs/ /usr/local/lib/
RUN ldconfig

# Force every runtime pip invocation (challenge requirements.txt and the
# evaluation_script __init__.py install() helper) to honor the worker's pinned
# core dependency stack, preventing numpy/scipy ABI breakage.
ENV PIP_CONSTRAINT=/code/requirements/worker_py3_9.txt \
    PIP_BUILD_CONSTRAINT=/code/requirements/worker_py3_9.txt

# Copy application code
COPY . /code/

CMD ["python", "-m", "scripts.workers.submission_worker"]
