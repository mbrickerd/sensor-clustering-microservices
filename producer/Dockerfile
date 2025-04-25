FROM python:3.10-slim AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY domain/pyproject.toml domain/
COPY producer/pyproject.toml producer/

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir uv && \
    cd domain && uv pip install --system -e . && \
    cd ../producer && uv pip install --system -e .

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

ENV PYTHONPATH=/app

CMD ["python", "-m", "producer.app"]
