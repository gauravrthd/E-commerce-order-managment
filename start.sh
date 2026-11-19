
#!/bin/sh
set -eu

export PROMETHEUS_MULTIPROC_DIR=/tmp/ecommerce-prometheus

mkdir -p "$PROMETHEUS_MULTIPROC_DIR"

find "$PROMETHEUS_MULTIPROC_DIR" \
    -maxdepth 1 \
    -type f \
    -name '*.db' \
    -delete

exec gunicorn main:app \
    --workers 2 \
    --worker-class uvicorn_worker.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --config gunicorn.conf.py \
    --access-logfile - \
    --error-logfile -
