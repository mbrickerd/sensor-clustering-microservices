FROM python:3.10-slim AS builder

WORKDIR /app

COPY domain/ /app/domain/
COPY trainer/ /app/trainer/

RUN pip install uv
RUN cd /app/domain && uv pip install --system -e .
RUN cd /app/trainer && uv pip install --system -e .

FROM python:3.10-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/domain ./domain
COPY --from=builder /app/trainer ./trainer
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

ENV PYTHONPATH=/app
RUN mkdir -p /app/data

CMD ["bash", "-c", "if [ \"$API_MODE\" = \"true\" ]; then uvicorn trainer.app:app --host 0.0.0.0 --port 8000; elif [ \"$WORKER_MODE\" = \"true\" ]; then celery -A trainer.tasks.train worker --loglevel=info; else python -m trainer.app; fi"]