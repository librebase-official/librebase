FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates bash libpq5 tini \
    && rm -rf /var/lib/apt/lists/*
COPY li-mail-gateway /usr/local/bin/li-mail-gateway
COPY li-mail-gateway-selftest /usr/local/bin/li-mail-gateway-selftest
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /usr/local/bin/li-mail-gateway /usr/local/bin/li-mail-gateway-selftest /entrypoint.sh
ENV LI_MAIL_HTTP_HOST=0.0.0.0 \
    LI_MAIL_HTTP_PORT=8080 \
    LI_API_PORT=8080 \
    LI_MAIL_GATEWAY_TOKEN=dev-token \
    LI_MAIL_MSG_STORE_ROOT=/var/lib/li-mail/mailboxes
EXPOSE 8080
ENTRYPOINT ["/usr/bin/tini","--","/usr/local/bin/li-mail-gateway"]
