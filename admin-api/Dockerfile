# Librebase Admin API — product management backend (not a linative lip package)
FROM alpine:3.21
RUN apk add --no-cache python3 py3-argon2-cffi py3-psycopg2 wget
WORKDIR /app
COPY migrations/ ./migrations/
COPY scripts/admin_server.py ./scripts/admin_server.py
COPY scripts/hcloud.py ./scripts/hcloud.py
COPY host-agent/ ./host-agent/
ENV LIBREBASE_ADMIN_BIND=0.0.0.0
ENV LIBREBASE_ADMIN_PORT=54330
ENV LIBREBASE_ADMIN_DB_PATH=/data/admin.db
EXPOSE 54330
VOLUME ["/data"]
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1:54330/health || exit 1
CMD ["python3", "scripts/admin_server.py"]
