# librebase-todo — self-contained Librebase todo app: lis backend (mock auth, in-memory
# REST) + @librebase/librebase todo-app HTTP server. Sideloaded into k3s (imagePullPolicy: Never).
FROM docker.io/library/python:3.12-slim AS lis
WORKDIR /opt/lis
COPY --from=lis-src / ./
RUN find /opt/lis -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

FROM docker.io/library/node:22-bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*
WORKDIR /opt

# Place SDK where the todo-app's file:../../packages/sdk dependency resolves
COPY packages/sdk /opt/packages/sdk
COPY apps/todo-app/package.json /opt/todo/package.json
COPY apps/todo-app/src /opt/todo/src
COPY apps/todo-app/public /opt/todo/public

WORKDIR /opt/todo
RUN npm install --omit=dev --no-audit --no-fund

# npm creates a relative symlink for the file: SDK dep that node can't resolve
# from /opt/todo at runtime — replace it with a real copy.
RUN rm -rf node_modules/@librebase/librebase && \
    mkdir -p node_modules/@librebase && \
    cp -r /opt/packages/sdk node_modules/@librebase/librebase

# lis backend (pure stdlib python)
COPY --from=lis /opt/lis /opt/lis
ENV PYTHONPATH=/opt/lis

COPY apps/todo-app/entrypoint-lis.sh /opt/todo/entrypoint-lis.sh
RUN chmod +x /opt/todo/entrypoint-lis.sh

ENV PORT=8787
EXPOSE 8787 54321

CMD ["node", "/opt/todo/src/server.mjs"]
