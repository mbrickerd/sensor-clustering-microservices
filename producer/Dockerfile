FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock /app/

RUN uv pip install --system -e .

COPY producer/ /app/producer/

ENV PYTHONPATH=/app

RUN mkdir -p /app/data

CMD ["python", "producer/app.py"]
