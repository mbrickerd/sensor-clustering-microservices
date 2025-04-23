# syntax=docker/dockerfile:1
FROM python:3.10-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy only the necessary files for dependency installation
COPY domain/pyproject.toml domain/
COPY producer/pyproject.toml producer/

# Install dependencies with caching
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir uv && \
    cd domain && uv pip install --system -e . && \
    cd ../producer && uv pip install --system -e .

# Copy the rest of the application code
COPY domain/ /app/domain/
COPY producer/ /app/producer/

FROM python:3.10-slim

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only the necessary files from builder
COPY --from=builder /app/domain ./domain
COPY --from=builder /app/producer ./producer
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

ENV PYTHONPATH=/app

CMD ["python", "-m", "producer.app"]
