FROM python:3.10-slim AS builder

WORKDIR /app

COPY domain/ /app/domain/
COPY trainer/ /app/trainer/
COPY trainer/scripts/entrypoint.sh /app/scripts/entrypoint.sh

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
COPY --from=builder /app/scripts/entrypoint.sh /scripts/entrypoint.sh

RUN chmod +x /scripts/entrypoint.sh

ENV PYTHONPATH=/app
RUN mkdir -p /app/data

CMD ["/scripts/entrypoint.sh"]
