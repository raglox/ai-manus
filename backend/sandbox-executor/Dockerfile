# Multi-stage build for optimized cold start performance
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Google Cloud SDK dependencies (optimized versions)
RUN pip install --no-cache-dir \
    google-cloud-storage==2.14.0 \
    google-cloud-logging==3.9.0

# Final stage - minimal runtime image
FROM python:3.11-slim

WORKDIR /workspace

# Install only essential runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    wget \
    vim \
    nodejs \
    npm \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy executor script
COPY executor.py /usr/local/bin/executor.py
RUN chmod +x /usr/local/bin/executor.py

# Create non-root user
RUN useradd -m -u 1000 sandbox && \
    chown -R sandbox:sandbox /workspace

# Pre-create common directories
RUN mkdir -p /tmp /workspace && \
    chown -R sandbox:sandbox /tmp /workspace

USER sandbox

# Health check (optional, for monitoring)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

ENTRYPOINT ["python", "/usr/local/bin/executor.py"]