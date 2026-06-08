FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/librebase

COPY scripts/lidb_engine.py scripts/dev_runtime_stub.py /opt/librebase/scripts/
COPY deploy/docker/lidb-runtime/entrypoint.sh /opt/librebase/entrypoint.sh

RUN chmod +x /opt/librebase/entrypoint.sh \
    /opt/librebase/scripts/lidb_engine.py \
    /opt/librebase/scripts/dev_runtime_stub.py \
    && mkdir -p /data

ENV LI_DATA_DIR=/data \
    LIDB_RUNTIME_MODE=dev \
    LIBREBASE_API_PORT=54320 \
    LIBREBASE_PG_PORT=54322

EXPOSE 54320 54322

ENTRYPOINT ["/usr/bin/tini", "--", "/opt/librebase/entrypoint.sh"]
