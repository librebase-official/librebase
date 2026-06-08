//! Client for licontainerd Unix socket API.

use licontainer_proto::{
    ApiRequest, ApiResponse, ContainerStatusResponse, CreateContainerRequest,
    ListContainersRequest, PullImageRequest, StartContainerRequest, StopContainerRequest,
    DEFAULT_SOCKET_PATH,
};
use std::path::Path;

pub fn socket_path() -> String {
    std::env::var("LI_CONTAINER_SOCKET").unwrap_or_else(|_| DEFAULT_SOCKET_PATH.into())
}

#[cfg(unix)]
pub fn call<T: serde::de::DeserializeOwned>(
    request: ApiRequest,
) -> Result<T, String> {
    use std::io::{Read, Write};
    use std::os::unix::net::UnixStream;

    let mut stream = UnixStream::connect(socket_path())
        .map_err(|e| format!("daemon unreachable at {}: {e}", socket_path()))?;
    let payload = serde_json::to_string(&request).map_err(|e| e.to_string())?;
    stream
        .write_all(payload.as_bytes())
        .map_err(|e| e.to_string())?;
    let mut buf = String::new();
    stream.read_to_string(&mut buf).map_err(|e| e.to_string())?;
    let resp: ApiResponse<T> = serde_json::from_str(&buf).map_err(|e| e.to_string())?;
    if resp.ok {
        resp.data.ok_or_else(|| "empty response data".into())
    } else {
        Err(resp
            .error
            .map(|e| format!("{}: {}", e.code, e.message))
            .unwrap_or_else(|| "unknown error".into()))
    }
}

#[cfg(not(unix))]
pub fn call<T: serde::de::DeserializeOwned>(
    request: ApiRequest,
) -> Result<T, String> {
    let _ = request;
    Err("lictl requires Unix (use WSL2 bridge on Windows)".into())
}

#[cfg(windows)]
pub fn is_windows() -> bool {
    true
}

#[cfg(not(windows))]
pub fn is_windows() -> bool {
    false
}

/// Forward command to WSL2 distro on Windows.
#[cfg(windows)]
pub fn wsl_forward(args: &[&str]) -> Result<String, String> {
    use std::process::Command;

    let distro = std::env::var("LI_CONTAINER_WSL_DISTRO")
        .unwrap_or_else(|_| "LibrebaseContainer".into());

    let mut cmd = Command::new("wsl");
    cmd.args(["-d", &distro, "-e", "lictl"]);
    cmd.args(args);

    let output = cmd
        .output()
        .map_err(|e| format!("wsl forward failed: {e}"))?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).into_owned())
    } else {
        Err(format!(
            "wsl lictl failed: {}",
            String::from_utf8_lossy(&output.stderr)
        ))
    }
}

#[cfg(not(windows))]
pub fn wsl_forward(_args: &[&str]) -> Result<String, String> {
    Err("WSL bridge only available on Windows".into())
}

pub fn pull(reference: &str, squashfs: bool) -> Result<(), String> {
    if is_windows() {
        let out = wsl_forward(&["pull", reference])?;
        print!("{out}");
        return Ok(());
    }
    let _: licontainer_proto::PullImageResponse = call(ApiRequest::PullImage(PullImageRequest {
        reference: reference.into(),
        export_squashfs: squashfs,
    }))?;
    println!("Pulled {reference}");
    Ok(())
}

pub fn run(image: &str, name: Option<&str>, args: &[String]) -> Result<(), String> {
    if is_windows() {
        let mut wsl_args = vec!["run", image];
        if let Some(n) = name {
            wsl_args.push("--name");
            wsl_args.push(n);
        }
        for a in args {
            wsl_args.push(a);
        }
        let out = wsl_forward(&wsl_args)?;
        print!("{out}");
        return Ok(());
    }

    let container_name = name.unwrap_or("default");
    let create: licontainer_proto::CreateContainerResponse =
        call(ApiRequest::CreateContainer(CreateContainerRequest {
            name: container_name.into(),
            image: image.into(),
            args: args.to_vec(),
            env: vec![],
        }))?;

    let start: licontainer_proto::StartContainerResponse =
        call(ApiRequest::StartContainer(StartContainerRequest {
            id: create.id.clone(),
        }))?;

    println!(
        "Started container {} (id={}, pid={})",
        create.name, create.id, start.pid
    );
    Ok(())
}

pub fn ps() -> Result<(), String> {
    if is_windows() {
        let out = wsl_forward(&["ps"])?;
        print!("{out}");
        return Ok(());
    }
    let resp: licontainer_proto::ListContainersResponse =
        call(ApiRequest::ListContainers(ListContainersRequest {}))?;
    if resp.containers.is_empty() {
        println!("No containers");
        return Ok(());
    }
    println!("{:<36} {:<12} {:<20} {}", "ID", "STATE", "NAME", "IMAGE");
    for c in resp.containers {
        println!("{:<36} {:<12} {:<20} {}", c.id, c.state, c.name, c.image);
    }
    Ok(())
}

pub fn stop(id: &str) -> Result<(), String> {
    if is_windows() {
        let out = wsl_forward(&["stop", id])?;
        print!("{out}");
        return Ok(());
    }
    let _: licontainer_proto::StopContainerResponse =
        call(ApiRequest::StopContainer(StopContainerRequest {
            id: id.into(),
            signal: "SIGTERM".into(),
        }))?;
    println!("Stopped {id}");
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn socket_path_default() {
        std::env::remove_var("LI_CONTAINER_SOCKET");
        assert!(socket_path().contains("licontainer"));
    }

    #[cfg(not(windows))]
    #[test]
    fn call_fails_without_daemon() {
        std::env::set_var("LI_CONTAINER_SOCKET", "/tmp/nonexistent-licontainer.sock");
        let result = pull("test:latest", false);
        assert!(result.is_err());
    }
}
