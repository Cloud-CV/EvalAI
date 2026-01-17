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

WORKDIR /code

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.8/site-packages /usr/local/lib/python3.8/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy runtime libraries from builder stage (faster than apt-get, no network needed)
# PostgreSQL client library
COPY --from=builder /usr/lib/x86_64-linux-gnu/libpq.so* /usr/lib/x86_64-linux-gnu/
# Image processing libraries (for Pillow)
COPY --from=builder /usr/lib/x86_64-linux-gnu/libjpeg.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libpng16.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libtiff.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libfreetype.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/liblcms2.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libwebp.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libwebpdemux.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libwebpmux.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libsharpyuv.so* /usr/lib/x86_64-linux-gnu/
# TIFF dependencies
COPY --from=builder /usr/lib/x86_64-linux-gnu/libjbig.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libzstd.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libLerc.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libdeflate.so* /usr/lib/x86_64-linux-gnu/
# Curl and dependencies
COPY --from=builder /usr/lib/x86_64-linux-gnu/libcurl.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libnghttp2.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libbrotlidec.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libbrotlicommon.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libssh2.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libpsl.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libldap-2.4.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/liblber-2.4.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/librtmp.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libsasl2.so* /usr/lib/x86_64-linux-gnu/
# GMP library
COPY --from=builder /usr/lib/x86_64-linux-gnu/libgmp.so* /usr/lib/x86_64-linux-gnu/
# OpenCV libraries and dependencies
COPY --from=builder /usr/lib/x86_64-linux-gnu/libopencv* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libilmbase* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libopenexr* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libImath* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libIex* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libIlmThread* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libHalf* /usr/lib/x86_64-linux-gnu/
# Update library cache
RUN ldconfig

# Copy application code
COPY . /code/

CMD ["python", "-m", "scripts.workers.submission_worker"]
