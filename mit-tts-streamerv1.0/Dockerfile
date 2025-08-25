# MIT-TTS-Streamer Docker Image
# Multi-stage build for optimized production image
# Autor: Beler Nolasco Almonte

# Build stage
FROM python:3.9-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    wget \
    ffmpeg \
    portaudio19-dev \
    libasound2-dev \
    libsndfile1-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt requirements-tts.txt ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Install TTS dependencies (optional, can be skipped for smaller image)
ARG INSTALL_TTS_DEPS=true
RUN if [ "$INSTALL_TTS_DEPS" = "true" ]; then \
        pip install --no-cache-dir -r requirements-tts.txt; \
    fi

# Production stage
FROM python:3.9-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    portaudio19-dev \
    libasound2-dev \
    libsndfile1-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r tts && useradd -r -g tts -d /app -s /bin/bash tts

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=tts:tts src/ ./src/
COPY --chown=tts:tts config/ ./config/
COPY --chown=tts:tts examples/ ./examples/
COPY --chown=tts:tts docs/ ./docs/

# Create directories for logs and models
RUN mkdir -p /app/logs /app/models /app/cache \
    && chown -R tts:tts /app

# Switch to non-root user
USER tts

# Expose ports
EXPOSE 8000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV TTS_CONFIG_PATH=/app/config/default.json

# Default command
CMD ["python", "-m", "src.main", "--config", "/app/config/default.json"]

# Labels
LABEL maintainer="MIT-TTS-Streamer Team"
LABEL version="1.0.0"
LABEL description="Low-latency TTS streaming server"
LABEL org.opencontainers.image.source="https://github.com/your-org/mit-tts-streamer"
LABEL org.opencontainers.image.documentation="https://github.com/your-org/mit-tts-streamer/blob/main/README.md"
LABEL org.opencontainers.image.licenses="MIT"