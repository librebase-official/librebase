#!/usr/bin/env bash
# Librebase VPS setup — two containers (landing + studio) + nginx + certbot.
#
# Prereqs (one-time):
#   - DNS: A record app.librebase.xyz -> <VPS IP>  (librebase.xyz already exists)
#   - A GitHub token with repo scope exported as GITHUB_TOKEN (private landing repo)
#
# Run on the VPS as root:  GITHUB_TOKEN=... bash setup-vps.sh

set -euo pipefail

: "${GITHUB_TOKEN:?set GITHUB_TOKEN (repo scope) to clone the private landing repo}"
CERT_EMAIL="${CERT_EMAIL:-julian.kleber@sail.black}"

# --- 0. preserve existing Supabase env from the old tar-deployed studio ---
if [ -f /opt/librebase/.env ] && [ ! -f /opt/librebase/data-studio-ui/.env ]; then
  cp /opt/librebase/.env /tmp/librebase-supabase.env
fi

# --- 1. clone / update repos ---
if [ -d /opt/librebase-landing/.git ]; then
  git -C /opt/librebase-landing pull --ff-only
else
  git clone "https://${GITHUB_TOKEN}@github.com/librebase-official/librebase-landing.git" \
    /opt/librebase-landing
fi

if [ -d /opt/librebase/.git ]; then
  git -C /opt/librebase pull --ff-only
else
  rm -rf /opt/librebase
  git clone https://github.com/librebase-official/librebase.git /opt/librebase
fi

# --- 2. studio env (Supabase creds) ---
if [ -f /tmp/librebase-supabase.env ] && [ ! -f /opt/librebase/data-studio-ui/.env ]; then
  cp /tmp/librebase-supabase.env /opt/librebase/data-studio-ui/.env
fi

# --- 3. studio (:3005 -> app.librebase.xyz) ---
cd /opt/librebase/data-studio-ui
docker compose up -d --build

# --- 4. landing (:3006 -> librebase.xyz) ---
cd /opt/librebase-landing
docker compose up -d --build

# --- 5. nginx: two server blocks (landing=apex, studio=app subdomain) ---
cp /opt/librebase/deploy/nginx-librebase.xyz.conf /etc/nginx/conf.d/librebase.xyz.conf
nginx -t && systemctl reload nginx

# --- 6. certbot (existing apex cert + new app subdomain cert) ---
if [ ! -d /etc/letsencrypt/live/app.librebase.xyz ]; then
  certbot --nginx -d app.librebase.xyz --non-interactive --agree-tos -m "$CERT_EMAIL" || true
fi
if [ ! -d /etc/letsencrypt/live/librebase.xyz ]; then
  certbot --nginx -d librebase.xyz -d www.librebase.xyz --non-interactive --agree-tos \
    -m "$CERT_EMAIL" --redirect || true
fi
certbot renew --quiet || true

# --- 7. smoke check ---
docker ps --filter name=librebase --format '{{.Names}}  {{.Status}}'
curl -sS -o /dev/null -w 'landing :3006 -> %{http_code}\n' http://127.0.0.1:3006/ || true
curl -sS -o /dev/null -w 'studio  :3005 -> %{http_code}\n' http://127.0.0.1:3005/ || true
