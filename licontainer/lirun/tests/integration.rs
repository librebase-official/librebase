//! Integration tests for lirun on Linux.
//!
//! Builds a minimal busybox OCI bundle and runs create/start/state/delete cycle.
//! Requires root or CAP_SYS_ADMIN; skipped when not available.

#[cfg(target_os = "linux")]
mod linux {
    use std::fs;
    use std::path::{Path, PathBuf};
    use std::process::Command;

    use tempfile::TempDir;

    fn can_run_containers() -> bool {
        std::env::var("LI_CONTAINER_INTEGRATION")
            .ok()
            .as_deref()
            == Some("1")
    }

    fn lirun_bin() -> PathBuf {
        PathBuf::from(env!("CARGO_BIN_EXE_lirun"))
    }

    fn build_busybox_bundle(bundle_dir: &Path) -> std::io::Result<()> {
        let rootfs = bundle_dir.join("rootfs");
        fs::create_dir_all(&rootfs)?;

        // Download static busybox if not cached
        let busybox = rootfs.join("bin").join("busybox");
        fs::create_dir_all(busybox.parent().unwrap())?;

        if !busybox.exists() {
            let url = "https://busybox.net/downloads/binaries/1.35.0-x86_64-linux-musl/busybox";
            let status = Command::new("curl")
                .args(["-fsSL", url, "-o"])
                .arg(&busybox)
                .status()?;
            if !status.success() {
                return Err(std::io::Error::other("failed to download busybox"));
            }
            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;
                fs::set_permissions(&busybox, fs::Permissions::from_mode(0o755))?;
            }
        }

        // Symlink sh -> busybox
        let sh = rootfs.join("bin").join("sh");
        if !sh.exists() {
            #[cfg(unix)]
            std::os::unix::fs::symlink("busybox", &sh)?;
        }

        let config = serde_json::json!({
            "ociVersion": "1.0.2",
            "process": {
                "terminal": false,
                "user": { "uid": 0, "gid": 0 },
                "args": ["/bin/sh", "-c", "echo hello-licontainer > /tmp/out; sleep 0.1"],
                "env": ["PATH=/bin:/usr/bin"],
                "cwd": "/"
            },
            "root": { "path": "rootfs", "readonly": false },
            "hostname": "lirun-test",
            "mounts": [
                { "destination": "/proc", "type": "proc", "source": "proc" },
                { "destination": "/dev", "type": "tmpfs", "source": "tmpfs", "options": ["mode=755"] }
            ],
            "linux": {
                "namespaces": [
                    { "type": "pid" }, { "type": "net" }, { "type": "mnt" },
                    { "type": "uts" }, { "type": "ipc" }
                ],
                "resources": { "pids": { "limit": 64 } }
            }
        });

        fs::write(
            bundle_dir.join("config.json"),
            serde_json::to_string_pretty(&config).unwrap(),
        )?;
        Ok(())
    }

    #[test]
    fn busybox_create_start_state_delete() {
        if !can_run_containers() {
            eprintln!("skip: set LI_CONTAINER_INTEGRATION=1 to run");
            return;
        }

        let tmp = TempDir::new().unwrap();
        let state_dir = tmp.path().join("state");
        let cgroup_root = tmp.path().join("cgroup");
        fs::create_dir_all(&state_dir).unwrap();
        fs::create_dir_all(&cgroup_root).unwrap();

        std::env::set_var("LI_CONTAINER_STATE_DIR", &state_dir);
        std::env::set_var("LI_CONTAINER_CGROUP_ROOT", &cgroup_root);
        std::env::set_var("LI_CONTAINER_SKIP_SECCOMP", "1");

        let bundle_dir = tmp.path().join("bundle");
        fs::create_dir_all(&bundle_dir).unwrap();
        build_busybox_bundle(&bundle_dir).expect("bundle build");

        let id = "test-busybox";
        let lirun = lirun_bin();

        let create = Command::new(&lirun)
            .args(["create", "--bundle", bundle_dir.to_str().unwrap(), "--id", id])
            .output()
            .unwrap();
        assert!(
            create.status.success(),
            "create failed: {}",
            String::from_utf8_lossy(&create.stderr)
        );

        let start = Command::new(&lirun)
            .args(["start", "--id", id])
            .output()
            .unwrap();
        assert!(
            start.status.success(),
            "start failed: {}",
            String::from_utf8_lossy(&start.stderr)
        );

        std::thread::sleep(std::time::Duration::from_millis(200));

        let state = Command::new(&lirun)
            .args(["state", "--id", id])
            .output()
            .unwrap();
        assert!(state.status.success());
        let stdout = String::from_utf8_lossy(&state.stdout);
        assert!(stdout.contains("running") || stdout.contains("stopped"));

        let delete = Command::new(&lirun)
            .args(["delete", "--id", id, "--force"])
            .output()
            .unwrap();
        assert!(
            delete.status.success(),
            "delete failed: {}",
            String::from_utf8_lossy(&delete.stderr)
        );
    }

    #[test]
    fn version_prints() {
        let out = Command::new(lirun_bin())
            .arg("version")
            .output()
            .unwrap();
        assert!(out.status.success());
        let stdout = String::from_utf8_lossy(&out.stdout);
        assert!(stdout.contains("0.1.0"));
    }
}

#[cfg(not(target_os = "linux"))]
mod non_linux {
    #[test]
    fn version_stub_compiles() {
        assert!(true);
    }
}
