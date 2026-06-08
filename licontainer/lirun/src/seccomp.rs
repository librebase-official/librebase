//! Default seccomp profile for lirun.

use crate::bundle::BundleConfig;
use crate::error::RunResult;

#[cfg(target_os = "linux")]
use crate::bundle::default_seccomp_syscalls;

#[cfg(target_os = "linux")]
use crate::error::RunError;

#[cfg(target_os = "linux")]
pub fn apply(config: &BundleConfig) -> RunResult<()> {
    if std::env::var("LI_CONTAINER_SKIP_SECCOMP").ok().as_deref() == Some("1") {
        return Ok(());
    }

    let syscalls: Vec<&str> = if let Some(linux) = &config.linux {
        if let Some(seccomp) = &linux.seccomp {
            seccomp
                .syscalls
                .iter()
                .flat_map(|s| s.names.iter().map(String::as_str))
                .collect()
        } else {
            default_seccomp_syscalls()
        }
    } else {
        default_seccomp_syscalls()
    };

    if let Err(e) = install_filter(&syscalls) {
        if std::env::var("LI_CONTAINER_STRICT_SECCOMP").ok().as_deref() == Some("1") {
            return Err(RunError::Runtime(format!("seccomp: {e}")));
        }
        eprintln!("lirun: seccomp skipped: {e}");
    }
    Ok(())
}

#[cfg(not(target_os = "linux"))]
pub fn apply(_config: &BundleConfig) -> RunResult<()> {
    Ok(())
}

#[cfg(target_os = "linux")]
fn install_filter(syscalls: &[&str]) -> Result<(), String> {
    use libseccomp::{ScmpAction, ScmpFilterContext, ScmpSyscall};

    let mut ctx =
        ScmpFilterContext::new(ScmpAction::Errno(1)).map_err(|e| e.to_string())?;
    ctx.add_arch(libseccomp::ScmpArch::Native)
        .map_err(|e| e.to_string())?;

    for name in syscalls {
        if let Ok(syscall) = ScmpSyscall::from_name(name) {
            let _ = ctx.add_rule(ScmpAction::Allow, syscall);
        }
    }

    ctx.load().map_err(|e| e.to_string())
}
