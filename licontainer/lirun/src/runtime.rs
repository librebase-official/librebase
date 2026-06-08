//! Linux OCI runtime implementation.

#[cfg(target_os = "linux")]
mod imp {
    use std::fs;
    use std::path::{Path, PathBuf};

    use nix::mount::{mount, MsFlags};
    use nix::sched::{unshare, CloneFlags};
    use nix::sys::signal::{kill, Signal};
    use nix::unistd::{
        chdir, execve, fork, pivot_root, setgid, setgroups, setuid, ForkResult, Gid, Pid, Uid,
    };

    use crate::bundle::{
        self, cgroup_limits, BundleConfig, ContainerState,
    };
    use crate::error::{RunError, RunResult};
    use crate::seccomp;

    const DEFAULT_NAMESPACES: &[&str] = &["pid", "net", "mnt", "uts", "ipc"];

    pub fn create(container_id: &str, bundle_path: &Path) -> RunResult<()> {
        if bundle::load_state(container_id).is_ok() {
            return Err(RunError::ContainerExists(container_id.into()));
        }

        let config = BundleConfig::load(bundle_path)?;
        let rootfs = bundle_path.join(&config.root.path);
        if !rootfs.is_dir() {
            return Err(RunError::InvalidConfig(format!(
                "rootfs missing: {}",
                rootfs.display()
            )));
        }

        let state = ContainerState {
            ociVersion: config.ociVersion.clone(),
            id: container_id.into(),
            status: "created".into(),
            pid: None,
            bundle: Some(bundle_path.display().to_string()),
            exitCode: None,
        };
        bundle::save_state(&state)?;

        let cgroup_path = cgroup_dir(container_id);
        fs::create_dir_all(&cgroup_path)?;
        apply_cgroup_limits(&cgroup_path, &config)?;

        Ok(())
    }

    pub fn start(container_id: &str) -> RunResult<()> {
        let mut state = bundle::load_state(container_id)?;
        if state.status == "running" {
            return Err(RunError::InvalidState(format!(
                "container {container_id} already running"
            )));
        }
        let bundle_path = state
            .bundle
            .as_ref()
            .ok_or_else(|| RunError::InvalidState("missing bundle path".into()))?;
        let config = BundleConfig::load(Path::new(bundle_path))?;

        match unsafe { fork() } {
            Ok(ForkResult::Parent { child }) => {
                state.status = "running".into();
                state.pid = Some(child.as_raw() as u32);
                bundle::save_state(&state)?;
                Ok(())
            }
            Ok(ForkResult::Child) => {
                if let Err(e) = child_setup(container_id, Path::new(bundle_path), &config) {
                    eprintln!("{}", e.to_json());
                    std::process::exit(1);
                }
                unreachable!();
            }
            Err(e) => Err(RunError::Runtime(format!("fork failed: {e}"))),
        }
    }

    pub fn delete(container_id: &str, force: bool) -> RunResult<()> {
        let state = bundle::load_state(container_id)?;
        if state.status == "running" {
            if force {
                kill_container(&state)?;
            } else {
                return Err(RunError::InvalidState(format!(
                    "container {container_id} is running; use --force"
                )));
            }
        }
        cleanup_cgroup(container_id);
        bundle::delete_state(container_id)?;
        Ok(())
    }

    pub fn kill(container_id: &str, signal: Signal) -> RunResult<()> {
        let state = bundle::load_state(container_id)?;
        if let Some(pid) = state.pid {
            kill(Pid::from_raw(pid as i32), signal)
                .map_err(|e| RunError::Runtime(format!("kill failed: {e}")))?;
        }
        Ok(())
    }

    pub fn state(container_id: &str) -> RunResult<ContainerState> {
        let mut state = bundle::load_state(container_id)?;
        if state.status == "running" {
            if let Some(pid) = state.pid {
                if kill(Pid::from_raw(pid as i32), None).is_err() {
                    state.status = "stopped".into();
                    bundle::save_state(&state)?;
                }
            }
        }
        Ok(state)
    }

    fn kill_container(state: &ContainerState) -> RunResult<()> {
        if let Some(pid) = state.pid {
            let _ = kill(Pid::from_raw(pid as i32), Signal::SIGKILL);
        }
        Ok(())
    }

    fn child_setup(container_id: &str, bundle_path: &Path, config: &BundleConfig) -> RunResult<()> {
        unshare_namespaces(config)?;
        join_cgroup(container_id)?;
        setup_rootfs(bundle_path, config)?;
        drop_capabilities(config)?;
        seccomp::apply(config)?;
        exec_process(config)
    }

    fn unshare_namespaces(config: &BundleConfig) -> RunResult<()> {
        let mut flags = CloneFlags::empty();
        let ns_list: Vec<&str> = config
            .linux
            .as_ref()
            .map(|l| l.namespaces.iter().map(|n| n.ns_type.as_str()).collect())
            .unwrap_or_else(|| DEFAULT_NAMESPACES.to_vec());

        for ns in ns_list {
            match ns {
                "pid" => flags.insert(CloneFlags::CLONE_NEWPID),
                "net" => flags.insert(CloneFlags::CLONE_NEWNET),
                "mnt" => flags.insert(CloneFlags::CLONE_NEWNS),
                "uts" => flags.insert(CloneFlags::CLONE_NEWUTS),
                "ipc" => flags.insert(CloneFlags::CLONE_NEWIPC),
                "user" => flags.insert(CloneFlags::CLONE_NEWUSER),
                _ => {}
            }
        }
        unshare(flags).map_err(|e| RunError::Runtime(format!("unshare: {e}")))?;
        Ok(())
    }

    fn cgroup_dir(container_id: &str) -> PathBuf {
        let base = std::env::var("LI_CONTAINER_CGROUP_ROOT")
            .unwrap_or_else(|_| "/sys/fs/cgroup/licontainer".into());
        PathBuf::from(base).join(container_id)
    }

    fn join_cgroup(container_id: &str) -> RunResult<()> {
        let cgroup_path = cgroup_dir(container_id);
        fs::create_dir_all(&cgroup_path)?;
        let procs = cgroup_path.join("cgroup.procs");
        let pid = std::process::id();
        fs::write(procs, pid.to_string())?;
        Ok(())
    }

    fn apply_cgroup_limits(cgroup_path: &Path, config: &BundleConfig) -> RunResult<()> {
        for (key, value) in cgroup_limits(config) {
            let path = cgroup_path.join(&key);
            let _ = fs::write(path, value);
        }
        Ok(())
    }

    fn cleanup_cgroup(container_id: &str) {
        let path = cgroup_dir(container_id);
        let _ = fs::remove_dir_all(path);
    }

    fn setup_rootfs(bundle_path: &Path, config: &BundleConfig) -> RunResult<()> {
        let rootfs = bundle_path.join(&config.root.path);

        for m in &config.mounts {
            let dest = rootfs.join(m.destination.trim_start_matches('/'));
            if let Some(parent) = dest.parent() {
                let _ = fs::create_dir_all(parent);
            }
            match m.mount_type.as_str() {
                "proc" => {
                    let _ = fs::create_dir_all(&dest);
                    mount(
                        Some("proc"),
                        &dest,
                        Some("proc"),
                        MsFlags::empty(),
                        None::<&str>,
                    )
                    .map_err(|e| RunError::Runtime(format!("mount proc: {e}")))?;
                }
                "tmpfs" => {
                    let _ = fs::create_dir_all(&dest);
                    mount(
                        Some(&m.source),
                        &dest,
                        Some("tmpfs"),
                        MsFlags::empty(),
                        Some("mode=1777"),
                    )
                    .map_err(|e| RunError::Runtime(format!("mount tmpfs: {e}")))?;
                }
                "bind" => {
                    let src = Path::new(&m.source);
                    if src.exists() {
                        let _ = fs::create_dir_all(&dest);
                        let flags = MsFlags::MS_BIND | MsFlags::MS_REC;
                        mount(
                            Some(&m.source),
                            &dest,
                            None::<&str>,
                            flags,
                            None::<&str>,
                        )
                        .map_err(|e| RunError::Runtime(format!("bind mount: {e}")))?;
                    }
                }
                _ => {}
            }
        }

        for sub in ["/tmp", "/run"] {
            let dest = rootfs.join(sub.trim_start_matches('/'));
            if !dest.exists() {
                let _ = fs::create_dir_all(&dest);
                let _ = mount(
                    Some("tmpfs"),
                    &dest,
                    Some("tmpfs"),
                    MsFlags::empty(),
                    Some("mode=1777"),
                );
            }
        }

        let old_root = rootfs.join(".old_root");
        fs::create_dir_all(&old_root)?;
        chdir(&rootfs).map_err(|e| RunError::Runtime(format!("chdir rootfs: {e}")))?;
        pivot_root(".", ".old_root")
            .map_err(|e| RunError::Runtime(format!("pivot_root: {e}")))?;
        chdir("/").map_err(|e| RunError::Runtime(format!("chdir /: {e}")))?;
        let _ = fs::remove_dir_all("/.old_root");

        if config.root.readonly {
            mount(
                None::<&str>,
                "/",
                None::<&str>,
                MsFlags::MS_RDONLY | MsFlags::MS_REMOUNT,
                None::<&str>,
            )
            .map_err(|e| RunError::Runtime(format!("remount ro: {e}")))?;
        }

        if let Some(hostname) = &config.hostname {
            let _ = fs::write("/etc/hostname", hostname);
            let _ = nix::unistd::sethostname(hostname);
        }

        Ok(())
    }

    fn drop_capabilities(config: &BundleConfig) -> RunResult<()> {
        let uid = Uid::from_raw(config.process.user.uid);
        let gid = Gid::from_raw(config.process.user.gid);
        if !config.process.user.additionalGids.is_empty() {
            let groups: Vec<Gid> = config
                .process
                .user
                .additionalGids
                .iter()
                .map(|g| Gid::from_raw(*g))
                .collect();
            setgroups(&groups).map_err(|e| RunError::Runtime(format!("setgroups: {e}")))?;
        }
        setgid(gid).map_err(|e| RunError::Runtime(format!("setgid: {e}")))?;
        setuid(uid).map_err(|e| RunError::Runtime(format!("setuid: {e}")))?;
        Ok(())
    }

    fn exec_process(config: &BundleConfig) -> RunResult<()> {
        let cwd = config.process.cwd.as_deref().unwrap_or("/");
        chdir(cwd).map_err(|e| RunError::Runtime(format!("chdir cwd: {e}")))?;

        let args: Vec<std::ffi::CString> = config
            .process
            .args
            .iter()
            .map(|a| std::ffi::CString::new(a.as_str()).unwrap())
            .collect();
        let env: Vec<std::ffi::CString> = config
            .process
            .env
            .iter()
            .map(|e| std::ffi::CString::new(e.as_str()).unwrap())
            .collect();

        let bin = &args[0];
        execve(bin, &args, &env)
            .map_err(|e| RunError::Runtime(format!("execve {}: {e}", bin.to_string_lossy())))?;
        Ok(())
    }
}

#[cfg(not(target_os = "linux"))]
mod imp {
    use std::path::Path;

    use crate::bundle::ContainerState;
    use crate::error::{RunError, RunResult};

    pub fn create(_container_id: &str, _bundle_path: &Path) -> RunResult<()> {
        Err(RunError::Unsupported(
            "lirun requires Linux (use WSL2 bridge on Windows)".into(),
        ))
    }

    pub fn start(_container_id: &str) -> RunResult<()> {
        Err(RunError::Unsupported(
            "lirun requires Linux (use WSL2 bridge on Windows)".into(),
        ))
    }

    pub fn delete(_container_id: &str, _force: bool) -> RunResult<()> {
        Err(RunError::Unsupported(
            "lirun requires Linux (use WSL2 bridge on Windows)".into(),
        ))
    }

    pub fn kill(_container_id: &str, _signal: &str) -> RunResult<()> {
        Err(RunError::Unsupported(
            "lirun requires Linux (use WSL2 bridge on Windows)".into(),
        ))
    }

    pub fn state(_container_id: &str) -> RunResult<ContainerState> {
        Err(RunError::Unsupported(
            "lirun requires Linux (use WSL2 bridge on Windows)".into(),
        ))
    }
}

pub use imp::*;
