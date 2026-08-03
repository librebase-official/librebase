# Wave 0 — self-hosted `lic` spine (parity gate)

**Checkout (this machine):** `C:\Users\Julian\Documents\Programming\li\lic-parity-w0`  
**Pin SHA:** `1a466a6` (`main` shallow clone from GitLab `li-langverse/lic`)  
**Env:** `LIC_ROOT` / `LI_REPO_ROOT` → that path

## Why

Broken `lic` junction/worktrees blocked Li-coupled waves. Wave 0 restores a **self-hosted** compiler tree and a documented gate before any new Supabase surface.

## Gate commands

```bash
# From LIC_ROOT (Linux / WSL / homelab runner)
export LI_REPO_ROOT="$PWD"
# Prefer existing stage0 binary, else build
test -x build/compiler/lic/lic || cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
test -x build/compiler/lic/lic || cmake --build build --target lic -j"$(nproc)"
# Self-host smoke subset (stage0 dump parity)
bash li-tests/self_host_parity/run_token_parity.sh
```

Windows coordinator: use WSL against `/mnt/c/.../lic-parity-w0`, or a GitLab runner with the same SHA.

## Librebase pin

See `docs/li-dependency-pins.md` — `lic` row must list this SHA. Later waves require **self-host `lic` ≥ pin**.

## Honesty

- Seed (`bootstrap/lic`) ≠ full stage2 self-host (see `packages/li-lic/AGENTS.md`).
- Wave 0 DoD = checkout + **stage0 `lic` binary built** + `lic --help` works.
- Evidence (2026-08-03): WSL cmake built `build/compiler/lic/lic` (~8.3 MB) from `1a466a6`.
- `run_token_parity.sh` may FAIL on Windows/CRLF checkouts (golden offsets assume LF). Re-clone with `core.autocrlf=false` or run on Linux runner for that smoke.
