# ==============================================================================
# Production Dockerfile for Hybrid ECC IoT Authentication & Benchmark
# Supports:
#   - Native x86_64 and ARM emulation (linux/arm/v7, linux/arm64)
#   - Embedded IoT network link simulation (Zigbee / BLE / LoRaWAN via tc/netem)
#   - Non-root user security with granular NET_ADMIN capabilities
# ==============================================================================

ARG PYTHON_VERSION=3.12-slim-bookworm

FROM python:${PYTHON_VERSION} AS base

# Install system dependencies for cryptography, build toolchain, and network emulation (tc/netem)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    iproute2 \
    iputils-ping \
    sudo \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Optimize Python runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Create unprivileged user with sudo permissions for volume ownership and tc (traffic control)
RUN useradd -m -s /bin/bash iotuser && \
    echo "iotuser ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# Layer caching: Install core dependencies
COPY pyproject.toml /app/

RUN pip install --no-cache-dir --default-timeout=1000 --prefer-binary "setuptools>=68" "wheel" && \
    pip install --no-cache-dir --default-timeout=1000 --prefer-binary "cryptography>=41.0" "pytest>=7.4" "pytest-cov>=4.1" "hypothesis>=6.90" "matplotlib>=3.7"

# Copy project source and metadata
COPY hybrid_ecc_auth/ /app/hybrid_ecc_auth/
COPY docs/ /app/docs/
COPY README.md LICENSE NOTICE /app/

# Install package with all extras
RUN pip install --no-cache-dir --default-timeout=1000 --prefer-binary -e ".[dev,bench]"

# Copy and configure entrypoint
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh && \
    chown -R iotuser:iotuser /app

# Switch to non-root user
USER iotuser

# Default port for hea-server
EXPOSE 8443

# Volumes for output persistence and credentials
VOLUME ["/app/bench_output", "/app/creds"]

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["bench"]

