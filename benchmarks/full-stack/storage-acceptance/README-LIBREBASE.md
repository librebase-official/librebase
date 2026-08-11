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
For lis (core profile, `tus` on), the suite runs **60 tests**: 9 pass, 11 fail,
40 skip (capabilities lis doesn't implement: admin/cdn/iceberg/render/rls/vector/
wire).

**Passing:** health (status/version), bucket create/upload/read/list/sign/
delete lifecycle, signed-URL scope isolation, list-v2 prefix + underscore keys +
updated_at cursor, LIKE-literal bucket search, empty-bucket delete.

**Failing (remaining lis gaps, tracked in `benchmarks/CATCHUP.md`):**
- list-v2 cursor pagination for `created_at desc` ordering (created_at not
  captured on insert metadata)
- list-v2 `with_delimiter` folder semantics (search_v2 path)
- copy-without-`x-upsert` conflict on existing dest
- legacy auth error shapes on protected routes
- the composite rest-extended tests (bucket metadata, public/info reads, signed
  upload, copy/move/update, bulk delete, list-v1, duplicate protection,
  pagination/search, cross-bucket mutations, cache-control-after-copy,
  file-size limits, special-character keys)

These are deliberate, honest gaps — the suite is the roadmap. Each closed gap
lands with the lis feature + a passing acceptance test.
