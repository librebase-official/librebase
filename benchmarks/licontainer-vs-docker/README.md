# licontainer vs Docker benchmarks

Compare memory footprint (RSS) and cold-start time between licontainer and Docker for the same OCI image.

## Prerequisites

- Linux host with cgroup v2
- `lictl` and `licontainerd` built (`cargo build --release` in `licontainer/`)
- Docker installed (for comparison only)
- `bc`, `curl`

## Metrics

| Metric | Script | Method |
|--------|--------|--------|
| Idle RSS per container | `measure-rss.sh` | `/proc/<pid>/smaps_rollup` Pss after start |
| Cold start (pull→running) | `cold-start.sh` | timed `lictl run` vs `docker run` |
| Disk + page cache | manual | `du` on store + cgroup `memory.current` |

## Run

```bash
cd benchmarks/licontainer-vs-docker

# RSS comparison (N=3 replicas)
./measure-rss.sh hello-world 3

# Cold start timing
./cold-start.sh ghcr.io/librebase-official/lidb-runtime:dev
```

Set `LI_CONTAINER_SKIP_ENTITLEMENT=1` for local dev.

## CI

Optional nightly job with `continue-on-error: true` — see `.github/workflows/licontainer-build.yml`.

Results are published in `docs/licontainer.md` when run manually.

## Security checklist

Run after benchmarks:

```bash
./security-checklist.sh
```

Verifies: rootless uid, seccomp active, no CAP_SYS_ADMIN, daemon socket 0600, pids.max set.
