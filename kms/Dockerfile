# Librebase KMS — key management service
FROM alpine:3.21
RUN apk add --no-cache python3 py3-cryptography
WORKDIR /app
COPY kms/ ./kms/
ENV LIBREBASE_KMS_BIND=0.0.0.0
ENV LIBREBASE_KMS_PORT=54340
ENV LIBREBASE_KMS_DB_PATH=/data/kms.db
EXPOSE 54340
VOLUME ["/data"]
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1:54340/health || exit 1
CMD ["python3", "-m", "kms.server"]
