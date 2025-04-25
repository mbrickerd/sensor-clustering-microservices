FROM ghcr.io/mlflow/mlflow:v2.21.3 AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev \
        curl && \
    rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir psycopg2-binary gunicorn

FROM ghcr.io/mlflow/mlflow:v2.21.3

COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000"]
