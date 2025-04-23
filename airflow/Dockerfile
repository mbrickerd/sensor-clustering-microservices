FROM apache/airflow:2.8.4-python3.10

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY domain/ /opt/airflow/domain/
COPY trainer/ /opt/airflow/trainer/
COPY trainer/pyproject.toml /opt/airflow/

WORKDIR /opt/airflow

RUN mkdir -p /opt/airflow/domain/sensor_domain.egg-info \
    && mkdir -p /opt/airflow/trainer/sensor_trainer.egg-info \
    && chmod -R 777 /opt/airflow/domain \
    && chmod -R 777 /opt/airflow/trainer

USER airflow

RUN pip install --user uv psycopg2-binary pendulum
RUN cd domain && python -m pip install --user -e .
RUN sed -i 's|/app/domain|/opt/airflow/domain|g' /opt/airflow/trainer/pyproject.toml
RUN cd trainer && python -m pip install --user -e .

ENV PYTHONPATH=/opt/airflow:${PYTHONPATH}