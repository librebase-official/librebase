# Librebase — Supabase Storage acceptance suite (vendored)

This directory is a copy of the official [`supabase/storage` acceptance
suite](https://github.com/supabase/storage/tree/master/acceptance) — black-box
HTTP tests that talk to a running storage service through REST, S3, TUS, and
admin endpoints only. We run it **unchanged** against Librebase lis storage.

## Run against lis

Prereq: lis registry server on `:54325` with `LI_JWT_SECRET=change-me` and a
service_role JWT.

```bash
npm install

# build a service token signed with the lis LI_JWT_SECRET (change-me):
SR=$(python3 - <<'PY'
import hmac,hashlib,base64,json,time
b=lambda d: base64.urlsafe_b64encode(json.dumps(d,separators=(',',':')).encode()).rstrip(b'=').decode()
h=b({"alg":"HS256","typ":"JWT"}); n=int(time.time())
p=b({"iss":"lis","sub":"acc","iat":n,"exp":n+3600,"role":"service_role"})
s=base64.urlsafe_b64encode(hmac.new(b"change-me",f"{h}.{p}".encode(),hashlib.sha256).digest()).rstrip(b'=').decode()
print(f"{h}.{p}.{s}")
PY
)

ACCEPTANCE_BASE_URL=http://127.0.0.1:54325/storage/v1 \
ACCEPTANCE_PROFILE=core \
ACCEPTANCE_TARGET=local \
ACCEPTANCE_ENABLE_TUS=true \
ACCEPTANCE_ANON_KEY="$SR" \
ACCEPTANCE_AUTHENTICATED_KEY="$SR" \
ACCEPTANCE_SERVICE_KEY="$SR" \
VITE_CONFIG_NATIVE_IGNORE_WARNING=true \
npx vitest run --config acceptance.vitest.config.ts
```

## Current status vs Supabase

Profiles are capability-gated by `ACCEPTANCE_PROFILE` + `ACCEPTANCE_ENABLE_*`.
For lis (core profile, `tus` on), the suite runs **80 tests**: **29 pass**, 11
fail, 40 skip (capabilities lis doesn't implement: admin/cdn/iceberg/render/
rls/vector/wire).

**Passing (29):** health (status/version); full REST lifecycle (create/upload/
read/list/sign/delete); signed-URL scope isolation; list-v2 cursor pagination
(created_at/updated_at), delimiter folders, underscore/LIKE-literal search;
copy/move/update + x-upsert conflict; bulk delete by prefixes; bucket metadata
+ public/info reads + MIME policy + file-size limits + special-character keys;
cache-control + ETag + x-metadata round-trips; batch signed URLs; duplicate
protection; legacy auth error shapes; **full TUS 1.0** (creation-with-upload,
chunked POST/HEAD/PATCH, offset conflicts, termination, signed TUS).

**Failing (11, all `s3.test.ts`):** the S3 wire-protocol suite (S3 XML
responses, SigV4 request signing, presigned POST forms, multipart XML
ListParts/ListMultipartUploads pagination, conditional GET validators, range
requests). lis exposes REST/S3-*shaped* HTTP, not the S3 XML/SigV4 wire
protocol — a distinct endpoint lis does not yet serve. Tracked as the next
storage surface.
