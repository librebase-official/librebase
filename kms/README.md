# Librebase KMS

Customer-facing key management service. Envelope encryption (KEK → per-project
DEKs, AES-256-GCM) plus Ed25519 sign/verify, per-project keys with versions and
rotation.

**Interim Python implementation** — mirrors the `admin-api` pattern ("interim
Python until li-httpd + lic + lidb land"). The pure-Li port swaps in once
`li-crypto` exposes high-level seal/open + sign/verify.

## API (service-role bearer)

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/health` | — | `{ok}` |
| POST | `/v1/projects/{project}/keys` | — | key (creates default if absent) |
| GET | `/v1/projects/{project}/keys` | — | `{keys: [...]}` |
| GET | `/v1/projects/{project}/keys/{key}/public` | — | `{publicKey, version}` |
| POST | `.../keys/{key}/encrypt` | `{data}` (base64) | `{ciphertext}` |
| POST | `.../keys/{key}/decrypt` | `{ciphertext}` | `{data}` (base64) |
| POST | `.../keys/{key}/sign` | `{data}` | `{signature}` |
| POST | `.../keys/{key}/verify` | `{data, signature}` | `{valid}` |
| POST | `.../keys/{key}/rotate` | — | new version |
| DELETE | `.../keys/{key}` | — | `{ok}` |
| POST | `/v1/internal/seal` | `{project_id, plaintext}` | `{ciphertext, keyId}` |
| POST | `/v1/internal/unseal` | `{key_id, ciphertext}` | `{plaintext}` |

## Env

- `LIBREBASE_KMS_BIND` (0.0.0.0)
- `LIBREBASE_KMS_PORT` (54340)
- `LIBREBASE_KMS_DB_PATH` (~/.local/share/librebase/kms.db)
- `LIBREBASE_KMS_SERVICE_ROLE` (bearer token)

## Notes

- KEK is bootstrapped on first boot and persisted in the `meta` table
  (interim; move to a key file / HSM before production).
- `ciphertext`, `data`, `signature`, `publicKey` are urlsafe base64.
- `/v1/internal/*` is how `admin-api` will seal provider `client_secret`s.

## Run

```bash
LIBREBASE_KMS_SERVICE_ROLE=dev-kms python3 -m kms.server
```
