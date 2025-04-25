FROM python:3.10-slim AS builder

WORKDIR /app

COPY domain/ /app/domain/
COPY predictor/ /app/predictor/

RUN mkdir -p /app/domain/domain /app/predictor/predictor
RUN touch /app/domain/domain/__init__.py /app/predictor/predictor/__init__.py

RUN pip install uv
RUN cd /app/domain && uv pip install --system -e .
RUN cd /app/predictor && uv pip install --system -e .

FROM python:3.10-slim

WORKDIR /app

COPY --from=builder /app/domain ./domain
COPY --from=builder /app/predictor ./predictor
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

ENV PYTHONPATH=/app
RUN mkdir -p /app/data

EXPOSE 8001

CMD ["python", "-m", "predictor.app"]
