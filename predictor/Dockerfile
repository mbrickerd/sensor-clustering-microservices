FROM python:3.10-slim AS builder

WORKDIR /app

# Copy domain package first
COPY domain/ /app/domain/

# Copy predictor package
COPY predictor/ /app/predictor/

# Ensure proper directory structure for packaging
RUN mkdir -p /app/domain/domain /app/predictor/predictor
RUN touch /app/domain/domain/__init__.py /app/predictor/predictor/__init__.py 

# Install both packages
RUN pip install uv
RUN cd /app/domain && uv pip install --system -e .
RUN cd /app/predictor && uv pip install --system -e .

FROM python:3.10-slim

WORKDIR /app

# Copy domain and predictor packages
COPY --from=builder /app/domain ./domain
COPY --from=builder /app/predictor ./predictor
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

ENV PYTHONPATH=/app
RUN mkdir -p /app/data

EXPOSE 8001

CMD ["python", "-m", "predictor.app"]