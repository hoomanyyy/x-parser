ARG RSSHUB_IMAGE=diygod/rsshub:latest
FROM ${RSSHUB_IMAGE}

USER root

ENV CACHE_TYPE=memory \
    CACHE_EXPIRE=90 \
    LOGGER_LEVEL=warn \
    TZ=UTC \
    CHECK_INTERVAL=30 \
    RSSHUB_DIR=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-venv \
        mariadb-server \
        mariadb-client \
        tzdata \
        dumb-init \
    && rm -rf /var/lib/apt/lists/* /var/lib/mysql/* \
    && python3 -m venv /opt/venv

WORKDIR /bot

COPY requirements.txt .
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

COPY . .
RUN sed -i 's/\r$//' start.sh

ENTRYPOINT ["dumb-init", "--"]
CMD ["bash", "/bot/start.sh"]