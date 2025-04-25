# syntax=docker/dockerfile:1
FROM ghcr.io/mlflow/mlflow:v2.21.3 AS builder

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies with caching
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir psycopg2-binary gunicorn

FROM ghcr.io/mlflow/mlflow:v2.21.3

# Copy only the necessary files from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the default command to start MLflow server with gunicorn
CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000"]
