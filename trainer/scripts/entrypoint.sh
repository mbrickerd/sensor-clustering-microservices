#!/bin/bash

if [ "$API_MODE" = "true" ]; then
    exec uvicorn trainer.app:app --host 0.0.0.0 --port 8000
elif [ "$WORKER_MODE" = "true" ]; then
    exec celery -A trainer.tasks.train worker --loglevel=info
else
    exec python -m trainer.app
fi
