#!/usr/bin/env python3
"""Deploy staging environment for Librebase.

Deploys a full staging stack (Postgres DB + KMS + admin-api + studio) on the
VPS alongside production, on separate ports with isolated data.

Usage:
    python3 deploy/deploy-staging.py [--rebuild]

Set STAGING_SSH_KEY / STAGING_SSH_USER / STAGING_SSH_HOST env vars, or it
defaults to the librebase-vps SSH alias.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VPS = os.environ.get("STAGING_SSH_HOST", "librebase-vps")
ADMIN = "/opt/librebase-admin-staging"
STUDIO = "/opt/librebase-staging"

STAGING_COMPOSE = """
version: "3.9"

services:
  staging-db:
    image: docker.io/postgres:16-alpine
    container_name: supabase-staging-db
    restart: unless-stopped
    ports:
      - "127.0.0.1:54332:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: s3cr3t_staging_db
      POSTGRES_DB: postgres
    volumes:
      - librebase-staging-db-data:/var/lib/postgresql/data
    networks:
      - librebase-net

  staging-kms:
    build:
      context: /opt/librebase-admin-staging
      dockerfile: kms/Dockerfile
    container_name: librebase-staging-kms
    restart: unless-stopped
    environment:
      LIBREBASE_KMS_BIND: 0.0.0.0
      LIBREBASE_KMS_PORT: 54340
      LIBREBASE_KMS_DB_PATH: /data/kms.db
      LIBREBASE_KMS_SERVICE_ROLE: st4g1ng_KMS_s3cr3t_d0_n0t_us3_1n_pr0d
    volumes:
      - librebase-staging-kms-data:/data
    networks:
      - librebase-net

  staging-admin:
    build:
      context: /opt/librebase-admin-staging
      dockerfile: Dockerfile
    container_name: librebase_staging_admin
    restart: unless-stopped
    ports:
      - "127.0.0.1:54331:54330"
    environment:
      LIBREBASE_ADMIN_BIND: 0.0.0.0
      LIBREBASE_ADMIN_PORT: 54330
      LIBREBASE_DB_DSN: postgresql://postgres:s3cr3t_staging_db@staging-db:5432/postgres
      LIBREBASE_ADMIN_JWT_SECRET: st4g1ng_JWT_s3cr3t_d0_n0t_us3_1n_pr0d
      LIBREBASE_CONSOLE_URL: https://app-stage.librebase.xyz
      LIBREBASE_KMS_URL: http://staging-kms:54340
      LIBREBASE_KMS_SERVICE_ROLE: st4g1ng_KMS_s3cr3t_d0_n0t_us3_1n_pr0d
      LIBREBASE_HETZNER_SSH_KEY_ID: ""
      LIBREBASE_HETZNER_IMAGE_ID: ""
      LIBREBASE_HETZNER_SERVER_TYPE: cx23
    env_file:
      - .env.hetzner
    depends_on:
      staging-db:
        condition: service_started
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://127.0.0.1:54330/health"]
      interval: 30s
      timeout: 3s
      retries: 3
    networks:
      - librebase-net

  staging-web:
    build:
      context: /opt/librebase-staging
      dockerfile: Dockerfile
      args:
        NEXT_PUBLIC_SITE_URL: https://app-stage.librebase.xyz
    container_name: librebase_staging_web
    restart: unless-stopped
    ports:
      - "127.0.0.1:3007:3005"
    environment:
      NODE_ENV: production
      PORT: 3005
      LIBREBASE_ADMIN_URL: http://staging-admin:54330
      LIBREBASE_SUPABASE_URL: https://supabase.majico.xyz
      LIBREBASE_SUPABASE_SERVICE_ROLE_KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UiLCJpYXQiOjE3ODQzMTY3NywiZXhwIjoyMjk5NjcwNzcifQ.AS78o7C3KFtmRzggbQssCMVBsD5qW77E3_Y2hZRZr2M
    depends_on:
      staging-admin:
        condition: service_healthy
    mem_limit: 384m
    networks:
      - librebase-net

networks:
  librebase-net:
    external: true

volumes:
  librebase-staging-db-data:
  librebase-staging-kms-data:
"""


def run(ssh: str, cmd: str) -> str:
    import subprocess
    r = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=10", ssh, cmd],
        capture_output=True, text=True, timeout=600,
    )
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        raise SystemExit(f"Remote command failed: {cmd}")
    return r.stdout


def main():
    rebuild = "--rebuild" in sys.argv
    print("=== Sync staging admin-api source ===")
    run(VPS, f"mkdir -p {ADMIN}")
    os.system(f"rsync -az --delete --exclude='__pycache__' --exclude='._*'"
              f" {REPO_ROOT}/admin-api/ {VPS}:{ADMIN}/")
    os.system(f"rsync -az --exclude='__pycache__' --exclude='._*'"
              f" {REPO_ROOT}/kms/ {VPS}:{ADMIN}/kms/")
    os.system(f"rsync -az --exclude='__pycache__' --exclude='._*'"
              f" {REPO_ROOT}/host-agent/ {VPS}:{ADMIN}/host-agent/")

    print("=== Sync staging studio source ===")
    run(VPS, f"mkdir -p {STUDIO}")
    os.system(f"rsync -az --delete --exclude=node_modules --exclude=.next --exclude=.git"
              f" --exclude=.env --exclude='._*' --exclude=__pycache__"
              f" {REPO_ROOT}/data-studio-ui/ {VPS}:{STUDIO}/")

    # Sync .env.hetzner if present (Hetzner API token for VM provisioning)
    hetzner_env = REPO_ROOT / "deploy" / "compose" / ".env.hetzner"
    if hetzner_env.is_file():
        print("=== Sync .env.hetzner ===")
        os.system(f"rsync -az {hetzner_env} {VPS}:{ADMIN}/.env.hetzner")
    else:
        print("WARN: .env.hetzner not found — Hetzner provisioning disabled")

    print("=== Write staging compose file ===")
    run(VPS, f"cat > {ADMIN}/docker-compose.staging.yml << 'STAGINGEOF'\n{STAGING_COMPOSE}\nSTAGINGEOF")

    print("=== Build staging images ===")
    if rebuild:
        run(VPS, f"cd {ADMIN} && podman compose -f docker-compose.staging.yml build --no-cache")
    else:
        run(VPS, f"cd {ADMIN} && podman compose -f docker-compose.staging.yml build")

    print("=== Deploy staging stack ===")
    run(VPS,
        f"cd {ADMIN} && podman compose -f docker-compose.staging.yml "
        f"up -d --force-recreate && "
        f"podman compose -f docker-compose.staging.yml ps")
    print("\n=== Staging stack deployed ===")
    print(f"  Staging studio:   https://app-stage.librebase.xyz")
    print(f"  Staging admin:    http://127.0.0.1:54331 (internal)")
    print(f"  Staging DB:       postgresql://postgres:s3cr3t_staging_db@127.0.0.1:54332/postgres")


if __name__ == "__main__":
    main()
