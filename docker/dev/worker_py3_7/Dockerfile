# Stage 1: Build stage with all build dependencies
FROM python:3.7-slim-bullseye AS builder

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
         default-jre-headless)) && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Copy requirements first for better layer caching
COPY requirements/ /code/requirements/

# Install Python dependencies with BuildKit cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --no-compile -U cffi service_identity cython==0.29 setuptools==57.5.0 && \
    pip install --no-cache-dir --no-compile -r requirements/dev.txt && \
    pip install --no-cache-dir --no-compile -r requirements/worker_py3_7.txt && \
    # Clean up pip cache and Python bytecode (directories first, then files)
    rm -rf /root/.cache/pip && \
    find /usr/local/lib/python3.7/site-packages -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.7/site-packages \( -name "*.pyc" -o -name "*.pyo" \) -delete 2>/dev/null || true

# Stage 2: Runtime stage - minimal dependencies only
FROM python:3.7-slim-bullseye

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install only runtime dependencies (no build tools)
# Add retry logic and --fix-missing to handle transient network issues
RUN (apt-get update && \
     apt-get install -y --no-install-recommends --fix-missing \
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
     || (apt-get update && apt-get install -y --no-install-recommends --fix-missing \
         default-jre-headless \
         libpq5 \
         libcurl4 \
         libjpeg62-turbo \
         zlib1g \
         libpng16-16 \
         libtiff5 \
         libfreetype6 \
         liblcms2-2 \
         libwebp6)) && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apt/*

WORKDIR /code

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.7/site-packages /usr/local/lib/python3.7/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . /code/

CMD ["./docker/wait-for-it.sh", "django:8000", "--", "python", "-m", "scripts.workers.submission_worker"]
