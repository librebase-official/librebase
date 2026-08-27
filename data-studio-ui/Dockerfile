# syntax=docker/dockerfile:1

FROM docker.io/node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM docker.io/node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
ARG NEXT_PUBLIC_SITE_URL=https://app.librebase.xyz
ENV NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL
ARG LIBREBASE_VERSION=0.1.14
ENV LIBREBASE_VERSION=$LIBREBASE_VERSION
RUN echo "$LIBREBASE_VERSION" > /app/VERSION
RUN npm run build

FROM docker.io/node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3005
ENV HOSTNAME=0.0.0.0

RUN addgroup -S nextjs && adduser -S nextjs -G nextjs

ARG LIBREBASE_VERSION=0.1.14
ENV LIBREBASE_VERSION=$LIBREBASE_VERSION

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nextjs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nextjs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nextjs /app/VERSION ./VERSION

USER nextjs
EXPOSE 3005
CMD ["node", "server.js"]
