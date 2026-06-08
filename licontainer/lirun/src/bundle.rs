//! OCI bundle configuration types (runtime-spec subset).

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::Path;

use crate::error::{RunError, RunResult};

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct BundleConfig {
    pub ociVersion: String,
    pub process: Process,
    pub root: Root,
    #[serde(default)]
    pub mounts: Vec<Mount>,
    #[serde(default)]
    pub linux: Option<Linux>,
    #[serde(default)]
    pub hostname: Option<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Process {
    pub terminal: bool,
    pub user: User,
    pub args: Vec<String>,
    #[serde(default)]
    pub env: Vec<String>,
    #[serde(default)]
    pub cwd: Option<String>,
    #[serde(default)]
    pub capabilities: Option<Capabilities>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct User {
    pub uid: u32,
    pub gid: u32,
    #[serde(default)]
    pub additionalGids: Vec<u32>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Capabilities {
    #[serde(default)]
    pub bounding: Vec<String>,
    #[serde(default)]
    pub effective: Vec<String>,
    #[serde(default)]
    pub inheritable: Vec<String>,
    #[serde(default)]
    pub permitted: Vec<String>,
    #[serde(default)]
    pub ambient: Vec<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Root {
    pub path: String,
    pub readonly: bool,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Mount {
    pub destination: String,
    #[serde(rename = "type")]
    pub mount_type: String,
    pub source: String,
    #[serde(default)]
    pub options: Vec<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Linux {
    #[serde(default)]
    pub namespaces: Vec<Namespace>,
    #[serde(default)]
    pub resources: Option<Resources>,
    #[serde(default)]
    pub seccomp: Option<Seccomp>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Namespace {
    #[serde(rename = "type")]
    pub ns_type: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Resources {
    #[serde(default)]
    pub memory: Option<Memory>,
    #[serde(default)]
    pub cpu: Option<Cpu>,
    #[serde(default)]
    pub pids: Option<Pids>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Memory {
    pub limit: Option<i64>,
    pub reservation: Option<i64>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Cpu {
    pub shares: Option<u64>,
    pub quota: Option<i64>,
    pub period: Option<u64>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Pids {
    pub limit: i64,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Seccomp {
    pub defaultAction: String,
    #[serde(default)]
    pub syscalls: Vec<SeccompSyscall>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct SeccompSyscall {
    pub names: Vec<String>,
    pub action: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ContainerState {
    pub ociVersion: String,
    pub id: String,
    pub status: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub pid: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub bundle: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub exitCode: Option<i32>,
}

impl BundleConfig {
    pub fn load(bundle_path: &Path) -> RunResult<Self> {
        let config_path = bundle_path.join("config.json");
        if !config_path.exists() {
            return Err(RunError::BundleNotFound(config_path.display().to_string()));
        }
        let raw = std::fs::read_to_string(&config_path)?;
        serde_json::from_str(&raw)
            .map_err(|e| RunError::InvalidConfig(format!("{}: {}", config_path.display(), e)))
    }
}

/// Default seccomp whitelist when bundle has no seccomp section.
pub fn default_seccomp_syscalls() -> Vec<&'static str> {
    vec![
        "read", "write", "open", "close", "stat", "fstat", "lstat", "poll", "lseek", "mmap",
        "mprotect", "munmap", "brk", "rt_sigaction", "rt_sigprocmask", "rt_sigreturn",
        "ioctl", "access", "pipe", "select", "sched_yield", "mremap", "msync", "mincore",
        "madvise", "dup", "dup2", "pause", "nanosleep", "getitimer", "alarm", "setitimer",
        "getpid", "sendfile", "socket", "connect", "accept", "sendto", "recvfrom", "sendmsg",
        "recvmsg", "shutdown", "bind", "listen", "getsockname", "getpeername", "socketpair",
        "setsockopt", "getsockopt", "clone", "fork", "vfork", "execve", "exit", "wait4",
        "kill", "uname", "fcntl", "flock", "fsync", "fdatasync", "truncate", "ftruncate",
        "getdents", "getcwd", "chdir", "fchdir", "rename", "mkdir", "rmdir", "creat", "link",
        "unlink", "symlink", "readlink", "chmod", "fchmod", "chown", "fchown", "lchown",
        "umask", "gettimeofday", "getrlimit", "getrusage", "sysinfo", "times", "getuid",
        "getgid", "geteuid", "getegid", "getppid", "getpgrp", "setsid", "setpgid", "getgroups",
        "setgroups", "setresuid", "getresuid", "setresgid", "getresgid", "getpgid", "setuid",
        "setgid", "getsid", "capget", "capset", "rt_sigpending", "rt_sigtimedwait",
        "rt_sigsuspend", "sigaltstack", "utime", "mknod", "statfs", "fstatfs", "syslog",
        "setpriority", "getpriority", "sched_setparam", "sched_getparam", "sched_setscheduler",
        "sched_getscheduler", "sched_get_priority_max", "sched_get_priority_min",
        "sched_rr_get_interval", "mlock", "munlock", "mlockall", "munlockall", "prctl",
        "arch_prctl", "set_tid_address", "set_robust_list", "get_robust_list", "futex",
        "epoll_create", "epoll_ctl", "epoll_wait", "epoll_pwait", "clock_gettime",
        "clock_getres", "clock_nanosleep", "exit_group", "waitid", "set_tid_address",
        "openat", "mkdirat", "mknodat", "fchownat", "futimesat", "newfstatat", "unlinkat",
        "renameat", "linkat", "symlinkat", "readlinkat", "fchmodat", "faccessat", "pselect6",
        "ppoll", "getrandom", "memfd_create", "gettid",
    ]
}

pub fn state_path(container_id: &str) -> std::path::PathBuf {
    let base = std::env::var("LI_CONTAINER_STATE_DIR")
        .unwrap_or_else(|_| "/run/licontainer/containers".into());
    std::path::PathBuf::from(base).join(format!("{container_id}.json"))
}

pub fn load_state(container_id: &str) -> RunResult<ContainerState> {
    let path = state_path(container_id);
    if !path.exists() {
        return Err(RunError::ContainerNotFound(container_id.into()));
    }
    let raw = std::fs::read_to_string(&path)?;
    serde_json::from_str(&raw)
        .map_err(|e| RunError::InvalidConfig(format!("state {}: {}", path.display(), e)))
}

pub fn save_state(state: &ContainerState) -> RunResult<()> {
    let path = state_path(&state.id);
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    let raw = serde_json::to_string_pretty(state)?;
    std::fs::write(path, raw)?;
    Ok(())
}

pub fn delete_state(container_id: &str) -> RunResult<()> {
    let path = state_path(container_id);
    if path.exists() {
        std::fs::remove_file(path)?;
    }
    Ok(())
}

/// Parse cgroup resource limits from bundle into cgroup v2 key/value pairs.
pub fn cgroup_limits(config: &BundleConfig) -> HashMap<String, String> {
    let mut limits = HashMap::new();
    if let Some(linux) = &config.linux {
        if let Some(res) = &linux.resources {
            if let Some(mem) = &res.memory {
                if let Some(limit) = mem.limit {
                    limits.insert("memory.max".into(), limit.to_string());
                }
                if let Some(high) = mem.reservation {
                    limits.insert("memory.high".into(), high.to_string());
                }
            }
            if let Some(cpu) = &res.cpu {
                if let (Some(quota), Some(period)) = (cpu.quota, cpu.period) {
                    limits.insert("cpu.max".into(), format!("{quota} {period}"));
                }
            }
            if let Some(pids) = &res.pids {
                limits.insert("pids.max".into(), pids.limit.to_string());
            }
        }
    }
    // Default pids limit if not specified
    if !limits.contains_key("pids.max") {
        limits.insert("pids.max".into(), "256".into());
    }
    limits
}
