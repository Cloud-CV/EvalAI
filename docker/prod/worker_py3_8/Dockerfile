# Stage 1: Build stage with all build dependencies
FROM python:3.8-slim-bullseye AS builder

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install all build dependencies with retry logic
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
     git \
     cmake \
     libeigen3-dev \
     libboost-python-dev \
     libopencv-dev \
     python3-opencv \
     libgmp-dev \
     libcgal-qt5-dev \
     swig \
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
         git \
         cmake \
         libeigen3-dev \
         libboost-python-dev \
         libopencv-dev \
         python3-opencv \
         libgmp-dev \
         libcgal-qt5-dev \
         swig)) && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Copy requirements first for better layer caching
COPY requirements/ /code/requirements/

# Install Python dependencies with BuildKit cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --no-compile -U cffi service_identity cython==0.29 numpy==1.18.1 && \
    pip install --no-cache-dir --no-compile -r requirements/prod.txt && \
    pip install --no-cache-dir --no-compile -r requirements/worker_py3_8.txt && \
    # Clean up pip cache and Python bytecode (directories first, then files)
    rm -rf /root/.cache/pip && \
    find /usr/local/lib/python3.8/site-packages -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.8/site-packages \( -name "*.pyc" -o -name "*.pyo" \) -delete 2>/dev/null || true

# Stage 2: Minimal runtime stage (Python 3.8 not available in distroless, use optimized slim)
FROM python:3.8-slim-bullseye

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install only runtime dependencies (no build tools)
# Add retry logic and --fix-missing to handle transient network issues
RUN (apt-get update && \
     apt-get install -y --no-install-recommends --fix-missing \
     libpq5 \
     libcurl4 \
     libjpeg62-turbo \
     zlib1g \
     libpng16-16 \
     libtiff5 \
     libfreetype6 \
     liblcms2-2 \
     libwebp6 \
     libopencv4.5 \
     libgmp10 \
     || (apt-get update && apt-get install -y --no-install-recommends --fix-missing \
         libpq5 \
         libcurl4 \
         libjpeg62-turbo \
         zlib1g \
         libpng16-16 \
         libtiff5 \
         libfreetype6 \
         liblcms2-2 \
         libwebp6 \
         libopencv4.5 \
         libgmp10)) && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apt/*

WORKDIR /code

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.8/site-packages /usr/local/lib/python3.8/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . /code/

CMD ["python", "-m", "scripts.workers.submission_worker"]
