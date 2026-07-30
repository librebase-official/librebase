# `@librebase/cli`

Thin orchestrator over Librebase Admin API + Studio helpers.

## Usage

```bash
node packages/cli/src/index.js --help
# or after npm link / npx:
npx @librebase/cli --help
```

| Command | What it does |
|---------|----------------|
| `version` | Print CLI version |
| `admin:health` | `GET` Admin API `/health` |
| `admin:setup` | First-run org (`NAME` / `EMAIL` / `PASSWORD` env) |
| `start:admin` | Launch `admin-api/scripts/admin_server.py` |
| `start:studio` | `npm run dev` in `data-studio-ui` |
| `matrix` | Capability matrix path + last harness report |
| `parity` | Run `scripts/parity_runner.py` |
| `pins` | Print `docs/li-dependency-pins.md` path |

## Env

| Variable | Default |
|----------|---------|
| `LIBREBASE_ROOT` | Detected from package location |
| `LIBREBASE_ADMIN_URL` | `http://127.0.0.1:54330` |
| `PYTHON` | `python` on Windows, `python3` elsewhere |
| `LIDB_ROOT` | lidb checkout for parity |

## Smoke

```bash
node packages/cli/src/index.js version
node packages/cli/scripts/smoke.mjs
```
