FROM python:3.10-slim AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy just the dependency definitions first for better caching
COPY domain/pyproject.toml domain/
COPY producer/pyproject.toml producer/

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e ./domain && \
    pip install --no-cache-dir -e ./producer

# Now copy the actual code
COPY domain/ /app/domain/
COPY producer/ /app/producer/

FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/domain ./domain
COPY --from=builder /app/producer ./producer
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose ports for health checks and metrics
EXPOSE 8080 8000

CMD ["python", "-m", "producer.app"]
