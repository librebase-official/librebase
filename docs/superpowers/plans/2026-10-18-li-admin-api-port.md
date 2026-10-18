# Pure-Li Admin API Port Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the interim Python Admin API (`admin-api/scripts/admin_server.py`) with a pure-Li control plane (`admin-api/li/`) that is byte-compatible on HTTP JSON, proven by shared contract tests, and gated in CI — while Studio/frontend stays Next.js.

**Architecture:** Keep one **HTTP contract** (paths + status + JSON fields) as the source of truth. Both runtimes (Python shim, Li binary) implement it. A Python **contract harness** starts whichever backend `LIBREBASE_ADMIN_RUNTIME=python|li` selects and runs the same cases. Port by route family; each family unlocks when its contract suite is green on Li. Cut over production only when `LIBREBASE_ADMIN_REQUIRE_LI=1` smoke passes.

**Tech Stack:** Li (`def` only) + lic runtime `tcp_*` / crypto externs + lidb embed seam; Python unittest contract harness; GitHub Actions (`ghcr.io/li-langverse/lic-ci` or sibling `lic` checkout, mirroring `licontainer-build.yml`).

**Linear:** Parent [LIB-133](https://linear.app/librebase/issue/LIB-133); children LIB-135 (setup), LIB-136 (auth); extend with CRUD / MCP / billing / cutover issues as tasks land.

## Global Constraints

- Frontend stays JS/Next — do not rewrite Studio in Li.
- Pure Li under `admin-api/li/` — no Python/C/Rust sources in that tree; trusted FFI only in `admin-api/li/src/seam.li`.
- HTTP path + JSON field names must match Python handlers (Studio/MCP clients unchanged).
- Never commit live `lb_mcp_*` / Stripe secrets (`tests/test_no_secrets_in_docs.py` must stay green).
- Branch + PR; reference `LIB-133` (and child ids) in commits.
- Python remains default serve path until Task 9 cutover; do not delete `admin_server.py` before then.
- Default JWT secret for tests: `contract-test-secret`; bind `127.0.0.1` only.

---

## File map (target)

| Path | Responsibility |
|------|----------------|
| `admin-api/li/src/seam.li` | `extern def` tcp + lidb + crypto helpers |
| `admin-api/li/src/routes.li` | Request path/method → route id |
| `admin-api/li/src/health.li` | `GET /health` body |
| `admin-api/li/src/db.li` | Open DB, migrate, exec JSON rows |
| `admin-api/li/src/auth.li` | Password hash verify, JWT, sessions |
| `admin-api/li/src/handlers_setup.li` | `POST /org/v1/setup` |
| `admin-api/li/src/handlers_auth.li` | `/org/v1/auth/*` |
| `admin-api/li/src/handlers_org.li` | projects/instances/hosts/members |
| `admin-api/li/src/handlers_mcp.li` | MCP keys + usage |
| `admin-api/li/src/handlers_billing.li` | Stripe session/portal/webhook |
| `admin-api/li/src/admin_server.li` | Listen loop + dispatch |
| `admin-api/li/scripts/build-li.sh` | Build + optional run |
| `admin-api/li/scripts/run-contract.sh` | Start Li binary for harness |
| `tests/admin_contract/__init__.py` | Shared HTTP helpers |
| `tests/admin_contract/harness.py` | Start/stop python\|li server |
| `tests/admin_contract/test_health.py` | Health contracts |
| `tests/admin_contract/test_setup.py` | Setup contracts |
| `tests/admin_contract/test_auth.py` | Auth contracts |
| `tests/admin_contract/test_org_crud.py` | Org CRUD contracts |
| `tests/admin_contract/test_mcp_keys.py` | MCP key contracts |
| `tests/admin_contract/test_billing.py` | Billing contracts (Stripe mocked) |
| `.github/workflows/admin-api-li.yml` | Li build + contract matrix |
| `docs/li-dependency-pins.md` | Pin lic/lidb SHAs used by CI |

---

### Task 1: Contract harness (backend-agnostic)

**Files:**
- Create: `tests/admin_contract/__init__.py`
- Create: `tests/admin_contract/harness.py`
- Create: `tests/admin_contract/test_health.py`
- Modify: `.github/workflows/test.yml` (discover still picks up `tests/test_*.py`; new package is opt-in via env — do not break default CI)

**Interfaces:**
- Produces: `AdminServer` context manager with `.base_url`, `.runtime` (`"python"` \| `"li"`)
- Produces: `http_json(method, url, body=None, token=None) -> tuple[int, dict]`

- [ ] **Step 1: Write harness + failing health contract for Li**

```python
# tests/admin_contract/harness.py
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "admin-api" / "scripts"
PY_SERVER = SCRIPTS / "admin_server.py"
LI_BIN = ROOT / "admin-api" / "li" / "build" / "admin_server"


def http_json(method: str, url: str, body: dict | None = None, token: str | None = None):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            raw = res.read().decode()
            return res.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"raw": raw}
        return e.code, payload


class AdminServer:
    def __init__(self, runtime: str | None = None, port: int = 54341):
        self.runtime = (runtime or os.environ.get("LIBREBASE_ADMIN_RUNTIME", "python")).lower()
        self.port = port
        self.base_url = f"http://127.0.0.1:{port}"
        self._proc: subprocess.Popen | None = None
        self._tmpdir: tempfile.TemporaryDirectory | None = None

    def __enter__(self) -> "AdminServer":
        self._tmpdir = tempfile.TemporaryDirectory(prefix="lb-admin-contract-")
        db = Path(self._tmpdir.name) / "org.db"
        env = {
            **os.environ,
            "LIBREBASE_ADMIN_BIND": "127.0.0.1",
            "LIBREBASE_ADMIN_PORT": str(self.port),
            "LIBREBASE_ADMIN_DB_PATH": str(db),
            "LIBREBASE_ADMIN_JWT_SECRET": "contract-test-secret",
        }
        if self.runtime == "python":
            cmd = [sys.executable, str(PY_SERVER)]
        elif self.runtime == "li":
            if not LI_BIN.is_file():
                raise unittest_skip_li()
            cmd = [str(LI_BIN)]
        else:
            raise ValueError(f"unknown runtime {self.runtime!r}")
        self._proc = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        deadline = time.time() + 8
        while time.time() < deadline:
            try:
                st, body = http_json("GET", f"{self.base_url}/health")
                if st == 200 and body.get("ok") is True:
                    return self
            except Exception:
                time.sleep(0.1)
        err = self._proc.stderr.read().decode() if self._proc.stderr else ""
        raise RuntimeError(f"admin {self.runtime} failed to become healthy: {err}")

    def __exit__(self, *args) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        if self._tmpdir:
            self._tmpdir.cleanup()


def unittest_skip_li():
    import unittest

    raise unittest.SkipTest("Li admin_server binary missing; build admin-api/li first")
```

```python
# tests/admin_contract/test_health.py
from __future__ import annotations

import os
import unittest

from tests.admin_contract.harness import AdminServer, http_json


class TestHealthContract(unittest.TestCase):
    def test_health_ok_python(self) -> None:
        with AdminServer(runtime="python", port=54341) as srv:
            st, body = http_json("GET", f"{srv.base_url}/health")
            self.assertEqual(st, 200)
            self.assertTrue(body.get("ok"))
            self.assertEqual(body.get("service"), "librebase-admin")

    @unittest.skipUnless(os.environ.get("LIBREBASE_ADMIN_CONTRACT_LI") == "1", "set LIBREBASE_ADMIN_CONTRACT_LI=1")
    def test_health_ok_li(self) -> None:
        with AdminServer(runtime="li", port=54342) as srv:
            st, body = http_json("GET", f"{srv.base_url}/health")
            self.assertEqual(st, 200)
            self.assertTrue(body.get("ok"))
            self.assertEqual(body.get("service"), "librebase-admin")
            self.assertEqual(body.get("runtime"), "li")
```

Also create empty `tests/admin_contract/__init__.py`.

- [ ] **Step 2: Run Python health contract (must pass)**

```bash
cd /path/to/librebase
python -m unittest tests.admin_contract.test_health.TestHealthContract.test_health_ok_python -v
```

Expected: `ok`

- [ ] **Step 3: Run Li health contract without binary (must skip or fail closed)**

```bash
LIBREBASE_ADMIN_CONTRACT_LI=1 python -m unittest tests.admin_contract.test_health.TestHealthContract.test_health_ok_li -v
```

Expected: `skipped` (no binary) **or** FAIL until Task 2 builds the binary — do not mark Task 1 done if Python contract fails.

- [ ] **Step 4: Commit**

```bash
git add tests/admin_contract/
git commit -m "test: admin HTTP contract harness (python health)"
```

---

### Task 2: Li build script + CI workflow

**Files:**
- Create: `admin-api/li/scripts/build-li.sh`
- Create: `.github/workflows/admin-api-li.yml`
- Modify: `admin-api/li/README.md` (build/CI section)
- Modify: `docs/li-dependency-pins.md` (add `librebase-admin` CI pin row)

**Interfaces:**
- Produces: `admin-api/li/build/admin_server` executable when `LIC_ROOT` resolves
- Consumes: same lic checkout pattern as `.github/workflows/licontainer-build.yml`

- [ ] **Step 1: Write `build-li.sh`**

```bash
#!/usr/bin/env bash
# admin-api/li/scripts/build-li.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
LI_ROOT="$ROOT/admin-api/li"
OUT="$LI_ROOT/build"
mkdir -p "$OUT"
LIC_ROOT="${LIC_ROOT:-$ROOT/../lic}"
if [[ ! -x "$LIC_ROOT/scripts/resolve-lic.sh" && ! -x "$LIC_ROOT/build/lic" && ! -x "$LIC_ROOT/build-mac/lic" ]]; then
  echo "lic unavailable at LIC_ROOT=$LIC_ROOT — syntax listing only"
  find "$LI_ROOT" -name '*.li' | sort
  exit 0
fi
export LI_NATIVE_RT="${LI_NATIVE_RT:-1}"
# Prefer packaged build; fall back to compiling main entry
if command -v lic >/dev/null 2>&1; then
  lic build "$LI_ROOT/src/admin_server.li" -o "$OUT/admin_server"
else
  echo "lic not on PATH; set LIC_ROOT and ensure resolve-lic.sh"
  exit 1
fi
chmod +x "$OUT/admin_server"
echo "built $OUT/admin_server"
```

- [ ] **Step 2: Write workflow**

```yaml
# .github/workflows/admin-api-li.yml
name: admin-api-li

on:
  push:
    branches: [main]
    paths:
      - "admin-api/li/**"
      - "tests/admin_contract/**"
      - ".github/workflows/admin-api-li.yml"
  pull_request:
    branches: [main]
    paths:
      - "admin-api/li/**"
      - "tests/admin_contract/**"
      - ".github/workflows/admin-api-li.yml"

jobs:
  li-build-contract:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Checkout lic compiler
        uses: actions/checkout@v4
        with:
          repository: li-langverse/lic
          path: lic
        continue-on-error: true

      - name: Build Li admin_server
        env:
          LIC_ROOT: ${{ github.workspace }}/lic
        run: |
          chmod +x admin-api/li/scripts/build-li.sh
          admin-api/li/scripts/build-li.sh

      - name: Contract tests (python always)
        run: python -m unittest tests.admin_contract.test_health -v

      - name: Contract tests (li when binary exists)
        env:
          LIBREBASE_ADMIN_CONTRACT_LI: "1"
        run: |
          if [[ -x admin-api/li/build/admin_server ]]; then
            python -m unittest discover -s tests/admin_contract -p "test_*.py" -v
          else
            echo "Li binary not built — python contracts only (lic unavailable)"
          fi
```

- [ ] **Step 3: Local dry-run**

```bash
chmod +x admin-api/li/scripts/build-li.sh
LIC_ROOT=/path/to/lic admin-api/li/scripts/build-li.sh
python -m unittest tests.admin_contract.test_health -v
```

Expected: script exits 0; Python health `ok`.

- [ ] **Step 4: Commit**

```bash
git add admin-api/li/scripts/build-li.sh .github/workflows/admin-api-li.yml admin-api/li/README.md docs/li-dependency-pins.md
git commit -m "ci: build admin-api/li and run HTTP contracts"
```

---

### Task 3: Health parity on Li (LIB-133 scaffold → green)

**Files:**
- Modify: `admin-api/li/src/admin_server.li` (infinite serve loop or env-capped; keep port 54330 default, honor later)
- Modify: `admin-api/li/src/health.li` if JSON keys diverge from Python
- Test: `tests/admin_contract/test_health.py`

**Interfaces:**
- Consumes: Task 1 harness, Task 2 binary
- Produces: Li `/health` → `{"ok":true,"service":"librebase-admin","runtime":"li"}` status 200

Python today returns roughly `{"ok": true, ...}` — Li must keep `ok` + `service`; `runtime` is Li-only additive (Studio ignores unknown fields).

- [ ] **Step 1: Align Li health JSON with contract**

Ensure `fill_health_body` emits exactly the keys asserted in `test_health_ok_li`. If Python omits `runtime`, that is fine — contract only requires it on Li.

- [ ] **Step 2: Change listen loop to serve until SIGTERM**

Replace the fixed `while n < 64` accept loop with a long-running loop (or `while 1`) so the harness does not race a premature exit. Keep `tcp_close` per connection.

- [ ] **Step 3: Build + run Li contract**

```bash
LIC_ROOT=/path/to/lic admin-api/li/scripts/build-li.sh
LIBREBASE_ADMIN_CONTRACT_LI=1 python -m unittest tests.admin_contract.test_health.TestHealthContract.test_health_ok_li -v
```

Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add admin-api/li/src/ tests/admin_contract/test_health.py
git commit -m "feat(li-admin): long-running server + health contract green"
```

---

### Task 4: DB seam + migrations (LIB-135)

**Files:**
- Create: `admin-api/li/src/db.li`
- Modify: `admin-api/li/src/seam.li` (ensure `lidb_open_i` / `lidb_exec_json_i` / `lidb_close_i`)
- Create: `tests/admin_contract/test_setup.py`
- Create: `admin-api/li/src/handlers_setup.li`
- Modify: `admin-api/li/src/admin_server.li` (dispatch route id 2 → setup)

**Interfaces:**
- Consumes: `lidb_open_i(path) -> db`, `lidb_exec_json_i(db, sql, out, cap) -> n`
- Produces: `POST /org/v1/setup` body shape matching Python:

```json
{
  "email": "a@b.co",
  "password": "long-enough-password",
  "orgName": "Acme"
}
```

Response (200/201): includes `accessToken` or `token`, `org` with `id`, user email — **copy exact keys from a live Python smoke response** before coding Li (run `python admin-api/scripts/smoke_admin.py` and record one golden JSON in `tests/admin_contract/goldens/setup_response.keys.json` as an ordered key list).

- [ ] **Step 1: Capture Python golden keys**

```bash
python admin-api/scripts/smoke_admin.py
# Manually write tests/admin_contract/goldens/setup_response.keys.json
# e.g. ["accessToken","refreshToken","org","user"] — exact names from response
```

- [ ] **Step 2: Write failing setup contract**

```python
# tests/admin_contract/test_setup.py
from __future__ import annotations

import os
import unittest

from tests.admin_contract.harness import AdminServer, http_json


class TestSetupContract(unittest.TestCase):
    def _assert_setup(self, runtime: str, port: int) -> None:
        with AdminServer(runtime=runtime, port=port) as srv:
            st, body = http_json(
                "POST",
                f"{srv.base_url}/org/v1/setup",
                {
                    "email": "owner@example.com",
                    "password": "correct-horse-battery",
                    "orgName": "Example Org",
                },
            )
            self.assertIn(st, (200, 201))
            self.assertTrue(body.get("accessToken") or body.get("token"))
            org = body.get("org") or {}
            self.assertTrue(org.get("id", "").startswith("org_"))

    def test_setup_python(self) -> None:
        self._assert_setup("python", 54343)

    @unittest.skipUnless(os.environ.get("LIBREBASE_ADMIN_CONTRACT_LI") == "1", "li opt-in")
    def test_setup_li(self) -> None:
        self._assert_setup("li", 54344)
```

- [ ] **Step 3: Run — Python pass, Li fail/skip**

```bash
python -m unittest tests.admin_contract.test_setup.TestSetupContract.test_setup_python -v
LIBREBASE_ADMIN_CONTRACT_LI=1 python -m unittest tests.admin_contract.test_setup.TestSetupContract.test_setup_li -v
```

Expected: Python `ok`; Li FAIL (501) or skip if no binary.

- [ ] **Step 4: Implement `db.li` + `handlers_setup.li`**

Apply the same SQL files under `admin-api/migrations/*.sql` in lexical order via `lidb_exec_json_i` (or file-read + exec). Create user + personal org + membership mirroring Python `POST /org/v1/setup` in `admin_server.py` (search `if path == "/org/v1/setup"`).

Wire `route_id == 2` in `admin_server.li` to the setup handler.

- [ ] **Step 5: Re-run Li setup contract → pass**

```bash
LIC_ROOT=/path/to/lic admin-api/li/scripts/build-li.sh
LIBREBASE_ADMIN_CONTRACT_LI=1 python -m unittest tests.admin_contract.test_setup -v
```

Expected: both cases `ok`.

- [ ] **Step 6: Commit**

```bash
git add admin-api/li/src/db.li admin-api/li/src/handlers_setup.li admin-api/li/src/admin_server.li admin-api/li/src/seam.li tests/admin_contract/test_setup.py tests/admin_contract/goldens/
git commit -m "feat(li-admin): setup + migrations (LIB-135)"
```

---

### Task 5: Auth family (LIB-136)

**Files:**
- Create: `admin-api/li/src/auth.li`
- Create: `admin-api/li/src/handlers_auth.li`
- Create: `tests/admin_contract/test_auth.py`
- Modify: `admin-api/li/src/seam.li` (HMAC/SHA256 or Argon2 externs as provided by lic — prefer matching Python: Argon2id when available, scrypt fallback)
- Modify: `admin-api/li/src/routes.li` (login/refresh/logout/mfa path ids)

**Interfaces:**
- Produces handlers for at least:
  - `POST /org/v1/auth/login`
  - `POST /org/v1/auth/refresh`
  - `POST /org/v1/auth/logout`
  - `GET /org/v1/me` (Bearer)
- OAuth (`/org/v1/auth/oauth/start|callback`) may return 501 until a follow-up child issue; contract marks them `@unittest.skip` until implemented — do not fake green.

- [ ] **Step 1: Write auth contract (login → me)**

```python
# tests/admin_contract/test_auth.py
from __future__ import annotations

import os
import unittest

from tests.admin_contract.harness import AdminServer, http_json


def _bootstrap(srv):
    st, body = http_json(
        "POST",
        f"{srv.base_url}/org/v1/setup",
        {
            "email": "auth@example.com",
            "password": "correct-horse-battery",
            "orgName": "Auth Org",
        },
    )
    assert st in (200, 201), body
    return body


class TestAuthContract(unittest.TestCase):
    def _flow(self, runtime: str, port: int) -> None:
        with AdminServer(runtime=runtime, port=port) as srv:
            setup = _bootstrap(srv)
            token = setup.get("accessToken") or setup.get("token")
            st, me = http_json("GET", f"{srv.base_url}/org/v1/me", token=token)
            self.assertEqual(st, 200)
            self.assertEqual(me.get("email") or (me.get("user") or {}).get("email"), "auth@example.com")

            st, login = http_json(
                "POST",
                f"{srv.base_url}/org/v1/auth/login",
                {"email": "auth@example.com", "password": "correct-horse-battery"},
            )
            self.assertEqual(st, 200)
            self.assertTrue(login.get("accessToken") or login.get("token"))

            st, bad = http_json(
                "POST",
                f"{srv.base_url}/org/v1/auth/login",
                {"email": "auth@example.com", "password": "wrong-password-here"},
            )
            self.assertIn(st, (401, 403))

    def test_auth_python(self) -> None:
        self._flow("python", 54345)

    @unittest.skipUnless(os.environ.get("LIBREBASE_ADMIN_CONTRACT_LI") == "1", "li opt-in")
    def test_auth_li(self) -> None:
        self._flow("li", 54346)
```

- [ ] **Step 2: TDD — Python pass, Li fail**

```bash
python -m unittest tests.admin_contract.test_auth.TestAuthContract.test_auth_python -v
LIBREBASE_ADMIN_CONTRACT_LI=1 python -m unittest tests.admin_contract.test_auth.TestAuthContract.test_auth_li -v
```

- [ ] **Step 3: Implement JWT + password verify in Li**

Port `sign_jwt` / `verify_jwt` / `hash_password` / `verify_password` semantics from `admin_server.py`. Store password hashes in the same `argon2id$…` or `scrypt$…` wire format so a DB created by Python can be opened by Li (and vice versa) for one migration window.

- [ ] **Step 4: Li contract green**

```bash
LIC_ROOT=/path/to/lic admin-api/li/scripts/build-li.sh
LIBREBASE_ADMIN_CONTRACT_LI=1 python -m unittest tests.admin_contract.test_auth -v
```

- [ ] **Step 5: Commit**

```bash
git add admin-api/li/src/auth.li admin-api/li/src/handlers_auth.li admin-api/li/src/routes.li admin-api/li/src/seam.li admin-api/li/src/admin_server.li tests/admin_contract/test_auth.py
git commit -m "feat(li-admin): auth login/me/refresh contract (LIB-136)"
```

---

### Task 6: Org CRUD (projects / instances / hosts / members)

**Files:**
- Create: `admin-api/li/src/handlers_org.li`
- Create: `tests/admin_contract/test_org_crud.py`
- Modify: `admin-api/li/src/routes.li`, `admin-api/li/src/admin_server.li`

**Interfaces:**
- Minimum green set (mirror `smoke_admin.py`):
  - `POST /org/v1/orgs/{org}/projects`
  - `GET /org/v1/orgs/{org}/projects`
  - `POST /org/v1/orgs/{org}/instances`
  - `GET /org/v1/orgs/{org}/instances`
  - `GET /org/v1/orgs/{org}/members`
- Entitlement gates: reuse Python `entitlement_for_edition` / `plan_instance_limit` rules (encode as Li functions with identical tables).

- [ ] **Step 1: Write org CRUD contract from smoke_admin sequence**

```python
# tests/admin_contract/test_org_crud.py  (abbreviated — expand asserts to match smoke_admin.py)
from __future__ import annotations

import os
import unittest

from tests.admin_contract.harness import AdminServer, http_json
from tests.admin_contract.test_auth import _bootstrap


class TestOrgCrudContract(unittest.TestCase):
    def _flow(self, runtime: str, port: int) -> None:
        with AdminServer(runtime=runtime, port=port) as srv:
            setup = _bootstrap(srv)
            token = setup.get("accessToken") or setup.get("token")
            org_id = (setup.get("org") or {}).get("id")
            self.assertTrue(org_id)

            st, proj = http_json(
                "POST",
                f"{srv.base_url}/org/v1/orgs/{org_id}/projects",
                {"name": "demo"},
                token=token,
            )
            self.assertIn(st, (200, 201))
            self.assertTrue((proj.get("id") or "").startswith("proj_"))

            st, plist = http_json("GET", f"{srv.base_url}/org/v1/orgs/{org_id}/projects", token=token)
            self.assertEqual(st, 200)
            self.assertGreaterEqual(len(plist.get("projects") or plist.get("items") or []), 1)

    def test_org_python(self) -> None:
        self._flow("python", 54347)

    @unittest.skipUnless(os.environ.get("LIBREBASE_ADMIN_CONTRACT_LI") == "1", "li opt-in")
    def test_org_li(self) -> None:
        self._flow("li", 54348)
```

Adjust list key (`projects` vs `items`) to match Python exactly after one recorded response.

- [ ] **Step 2: Implement handlers → Li green**

```bash
LIBREBASE_ADMIN_CONTRACT_LI=1 python -m unittest tests.admin_contract.test_org_crud -v
```

- [ ] **Step 3: File Linear child + commit**

```bash
git add admin-api/li/src/handlers_org.li admin-api/li/src/routes.li admin-api/li/src/admin_server.li tests/admin_contract/test_org_crud.py
git commit -m "feat(li-admin): projects/instances/members CRUD contracts"
```

---

### Task 7: MCP keys + usage

**Files:**
- Create: `admin-api/li/src/handlers_mcp.li`
- Create: `tests/admin_contract/test_mcp_keys.py`

**Interfaces:**
- `POST /org/v1/orgs/{org}/mcp-keys/rotate` → returns `lb_mcp_…` once
- `GET /org/v1/orgs/{org}/mcp-keys` → never returns full secret after create (match Python redaction)
- `POST /org/v1/mcp/usage` + `GET /org/v1/orgs/{org}/mcp/stats`

- [ ] **Step 1: Contract — rotate returns key once; list redacts**

```python
# tests/admin_contract/test_mcp_keys.py
from __future__ import annotations

import os
import unittest

from tests.admin_contract.harness import AdminServer, http_json
from tests.admin_contract.test_auth import _bootstrap


class TestMcpKeysContract(unittest.TestCase):
    def _flow(self, runtime: str, port: int) -> None:
        with AdminServer(runtime=runtime, port=port) as srv:
            setup = _bootstrap(srv)
            token = setup.get("accessToken") or setup.get("token")
            org_id = (setup.get("org") or {}).get("id")
            st, rotated = http_json(
                "POST",
                f"{srv.base_url}/org/v1/orgs/{org_id}/mcp-keys/rotate",
                {},
                token=token,
            )
            self.assertIn(st, (200, 201))
            key = rotated.get("key") or rotated.get("mcpKey")
            self.assertTrue(str(key).startswith("lb_mcp_"))

            st, listed = http_json(
                "GET",
                f"{srv.base_url}/org/v1/orgs/{org_id}/mcp-keys",
                token=token,
            )
            self.assertEqual(st, 200)
            blob = str(listed)
            self.assertNotIn(key, blob)  # full secret must not reappear

    def test_mcp_python(self) -> None:
        self._flow("python", 54349)

    @unittest.skipUnless(os.environ.get("LIBREBASE_ADMIN_CONTRACT_LI") == "1", "li opt-in")
    def test_mcp_li(self) -> None:
        self._flow("li", 54350)
```

- [ ] **Step 2: Implement + green + commit**

```bash
git commit -m "feat(li-admin): MCP key rotate/list redaction contracts"
```

---

### Task 8: Stripe billing (mocked HTTP)

**Files:**
- Create: `admin-api/li/src/handlers_billing.li`
- Create: `tests/admin_contract/test_billing.py`
- Modify: harness to accept `LIBREBASE_STRIPE_API_URL` pointing at a tiny Python mock server in-process (reuse patterns from `tests/test_stripe_e2e.py`)

**Interfaces:**
- `POST /org/v1/orgs/{org}/billing/session`
- `POST /org/v1/orgs/{org}/billing/portal`
- `POST /org/v1/billing/webhook` with valid HMAC header

- [ ] **Step 1: Port signature verify first (unit-level Li selftest optional)**

Mirror `stripe_verify_signature` from Python. Contract: invalid signature → 400; valid → 200 and plan flip.

- [ ] **Step 2: Write billing contract using existing Stripe test helpers**

Read `tests/test_stripe_e2e.py` and extract the minimal webhook payload + signing into `tests/admin_contract/test_billing.py` parameterized by runtime.

- [ ] **Step 3: Implement Li handlers + commit**

```bash
git commit -m "feat(li-admin): Stripe session/portal/webhook contracts"
```

---

### Task 9: Cutover gate + deploy

**Files:**
- Modify: `admin-api/Dockerfile` (multi-stage: build Li binary when `LIC_ROOT` present; else Python)
- Modify: `admin-api/README.md`
- Create: `admin-api/li/scripts/run-contract.sh`
- Modify: `docs/sdd/specs/cloud-ga/PLAN.md` progress row for control plane
- Modify: staging compose / deploy docs only if already in-repo (do not invent VPS secrets)

**Interfaces:**
- Env `LIBREBASE_ADMIN_REQUIRE_LI=1` → container entrypoint refuses to start Python shim
- Env `LIBREBASE_ADMIN_RUNTIME=li` → prefer Li binary on PATH/`/usr/local/bin/librebase-admin`

- [ ] **Step 1: Entrypoint script**

```bash
#!/usr/bin/env bash
# admin-api/li/scripts/entrypoint.sh
set -euo pipefail
if [[ "${LIBREBASE_ADMIN_REQUIRE_LI:-}" == "1" ]]; then
  exec /usr/local/bin/librebase-admin
fi
if [[ "${LIBREBASE_ADMIN_RUNTIME:-python}" == "li" && -x /usr/local/bin/librebase-admin ]]; then
  exec /usr/local/bin/librebase-admin
fi
exec python /app/scripts/admin_server.py
```

- [ ] **Step 2: CI job `cutover-smoke` (on workflow_dispatch or main)**

Run full `tests/admin_contract` with `LIBREBASE_ADMIN_CONTRACT_LI=1` and fail the job if any skip remains for core modules (`test_health`, `test_setup`, `test_auth`, `test_org_crud`).

- [ ] **Step 3: Update HANDOFF open items — Li control plane ready behind flag**

- [ ] **Step 4: Commit + open cutover PR**

```bash
git commit -m "feat(li-admin): REQUIRE_LI cutover entrypoint + CI gate"
```

- [ ] **Step 5: Staging bake**

Deploy staging with `LIBREBASE_ADMIN_RUNTIME=li` (not REQUIRE yet). Run Studio login + MCP `org_whoami`. Only then flip `LIBREBASE_ADMIN_REQUIRE_LI=1` on staging, then prod.

---

## CI matrix (summary)

| Workflow | When | What |
|----------|------|------|
| `test.yml` | every PR | Python unittest incl. existing admin tests + secrets guard |
| `admin-api-li.yml` | paths under `admin-api/li/**`, `tests/admin_contract/**` | `build-li.sh` + contract suite (Li when binary exists) |
| `licontainer-build.yml` | unchanged | licontainer only |

Optional later: merge Li contract job into `test.yml` once lic is reliably available on runners (homelab runners per `.cursor/rules/homelab-github-actions-runners.mdc`).

---

## Definition of done

- [ ] All `tests/admin_contract/test_{health,setup,auth,org_crud,mcp_keys,billing}.py` pass on **both** `python` and `li`
- [ ] `.github/workflows/admin-api-li.yml` green on PR
- [ ] `LIBREBASE_ADMIN_REQUIRE_LI=1` documented and proven on staging
- [ ] Python shim retained only as emergency fallback (or deleted in a follow-up PR after 1+ week stable)
- [ ] LIB-133 closed with evidence links (CI run + staging note)

---

## Self-review

1. **Spec coverage:** cloud-ga Li-first control plane → Tasks 1–9; LIB-135 → Task 4; LIB-136 → Task 5; security no-secrets → Global Constraints + existing test.
2. **Placeholders:** none intentional; OAuth left explicitly skipped with contract `@unittest.skip` until a child issue.
3. **Type consistency:** harness `AdminServer` / `http_json` used uniformly; route families dispatch via `route_id` extensions.
