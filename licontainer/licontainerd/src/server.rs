//! Container state managed by licontainerd.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::{Arc, Mutex};

use licontainer_proto::{
    check_entitlement, ApiRequest, ApiResponse, ContainerStatusResponse, ContainerSummary,
    CreateContainerResponse, ListContainersResponse, PullImageResponse, StartContainerResponse,
    StopContainerResponse,
};
use liimg::{image_to_bundle, pull, ImageManifest};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ManagedContainer {
    pub id: String,
    pub name: String,
    pub image: String,
    pub state: String,
    pub pid: Option<u32>,
    pub bundle_path: PathBuf,
}

pub struct DaemonState {
    pub containers: HashMap<String, ManagedContainer>,
    pub store_path: PathBuf,
}

impl DaemonState {
    pub fn new(store_path: PathBuf) -> Self {
        Self {
            containers: HashMap::new(),
            store_path,
        }
    }

    pub fn persist(&self) -> std::io::Result<()> {
        fs::create_dir_all(&self.store_path)?;
        let path = self.store_path.join("containers.json");
        let raw = serde_json::to_string_pretty(&self.containers)?;
        fs::write(path, raw)
    }

    pub fn load(store_path: PathBuf) -> Self {
        let path = store_path.join("containers.json");
        let containers = if path.exists() {
            fs::read_to_string(&path)
                .ok()
                .and_then(|raw| serde_json::from_str(&raw).ok())
                .unwrap_or_default()
        } else {
            HashMap::new()
        };
        Self {
            containers,
            store_path,
        }
    }
}

pub type SharedState = Arc<Mutex<DaemonState>>;

fn lirun_binary() -> String {
    std::env::var("LIRUN_BIN").unwrap_or_else(|_| "lirun".into())
}

pub fn handle_request(state: &mut DaemonState, req: ApiRequest) -> serde_json::Value {
    match req {
        ApiRequest::PullImage(p) => {
            if !check_entitlement("pull") {
                return serde_json::to_value(ApiResponse::<PullImageResponse>::err(
                    "ENTITLEMENT_DENIED",
                    "image pull requires Librebase entitlement (TODO)",
                ))
                .unwrap();
            }
            match pull(&p.reference, p.export_squashfs) {
                Ok(manifest) => serde_json::to_value(ApiResponse::ok(PullImageResponse {
                    reference: manifest.reference,
                    digest: manifest.digest,
                    store_path: manifest.store_path.display().to_string(),
                }))
                .unwrap(),
                Err(e) => serde_json::to_value(ApiResponse::<PullImageResponse>::err(
                    "PULL_FAILED",
                    e.to_string(),
                ))
                .unwrap(),
            }
        }
        ApiRequest::CreateContainer(p) => {
            if !check_entitlement("create") {
                return serde_json::to_value(ApiResponse::<CreateContainerResponse>::err(
                    "ENTITLEMENT_DENIED",
                    "container create requires Librebase entitlement (TODO)",
                ))
                .unwrap();
            }
            let id = uuid::Uuid::new_v4().to_string();
            let name = p.name.clone();
            let bundle_dir = state.store_path.join("bundles").join(&id);
            let image_manifest = ImageManifest {
                reference: p.image.clone(),
                digest: String::new(),
                store_path: state.store_path.join("images"),
            };
            if let Err(e) = image_to_bundle(&image_manifest, &bundle_dir) {
                return serde_json::to_value(ApiResponse::<CreateContainerResponse>::err(
                    "BUNDLE_FAILED",
                    e.to_string(),
                ))
                .unwrap();
            }

            let lirun = lirun_binary();
            let output = Command::new(&lirun)
                .args([
                    "create",
                    "--bundle",
                    bundle_dir.to_str().unwrap(),
                    "--id",
                    &id,
                ])
                .output();

            match output {
                Ok(out) if out.status.success() => {
                    let container = ManagedContainer {
                        id: id.clone(),
                        name: name.clone(),
                        image: p.image.clone(),
                        state: "created".into(),
                        pid: None,
                        bundle_path: bundle_dir.clone(),
                    };
                    state.containers.insert(id.clone(), container);
                    let _ = state.persist();
                    serde_json::to_value(ApiResponse::ok(CreateContainerResponse {
                        id,
                        name,
                        bundle_path: bundle_dir.display().to_string(),
                    }))
                    .unwrap()
                }
                Ok(out) => serde_json::to_value(ApiResponse::<CreateContainerResponse>::err(
                    "CREATE_FAILED",
                    String::from_utf8_lossy(&out.stderr).into_owned(),
                ))
                .unwrap(),
                Err(e) => serde_json::to_value(ApiResponse::<CreateContainerResponse>::err(
                    "CREATE_FAILED",
                    e.to_string(),
                ))
                .unwrap(),
            }
        }
        ApiRequest::StartContainer(p) => {
            let lirun = lirun_binary();
            let output = Command::new(&lirun)
                .args(["start", "--id", &p.id])
                .output();
            match output {
                Ok(out) if out.status.success() => {
                    if let Some(c) = state.containers.get_mut(&p.id) {
                        c.state = "running".into();
                        let _ = state.persist();
                    }
                    serde_json::to_value(ApiResponse::ok(StartContainerResponse {
                        id: p.id.clone(),
                        pid: state
                            .containers
                            .get(&p.id)
                            .and_then(|c| c.pid)
                            .unwrap_or(0),
                    }))
                    .unwrap()
                }
                Ok(out) => serde_json::to_value(ApiResponse::<StartContainerResponse>::err(
                    "START_FAILED",
                    String::from_utf8_lossy(&out.stderr).into_owned(),
                ))
                .unwrap(),
                Err(e) => serde_json::to_value(ApiResponse::<StartContainerResponse>::err(
                    "START_FAILED",
                    e.to_string(),
                ))
                .unwrap(),
            }
        }
        ApiRequest::StopContainer(p) => {
            let lirun = lirun_binary();
            let signal = p.signal;
            let output = Command::new(&lirun)
                .args(["kill", "--id", &p.id, &signal])
                .output();
            match output {
                Ok(out) if out.status.success() => {
                    if let Some(c) = state.containers.get_mut(&p.id) {
                        c.state = "stopped".into();
                        c.pid = None;
                        let _ = state.persist();
                    }
                    serde_json::to_value(ApiResponse::ok(StopContainerResponse { id: p.id }))
                        .unwrap()
                }
                Ok(out) => serde_json::to_value(ApiResponse::<StopContainerResponse>::err(
                    "STOP_FAILED",
                    String::from_utf8_lossy(&out.stderr).into_owned(),
                ))
                .unwrap(),
                Err(e) => serde_json::to_value(ApiResponse::<StopContainerResponse>::err(
                    "STOP_FAILED",
                    e.to_string(),
                ))
                .unwrap(),
            }
        }
        ApiRequest::ListContainers(_) => {
            let containers: Vec<ContainerSummary> = state
                .containers
                .values()
                .map(|c| ContainerSummary {
                    id: c.id.clone(),
                    name: c.name.clone(),
                    state: c.state.clone(),
                    image: c.image.clone(),
                    pid: c.pid,
                })
                .collect();
            serde_json::to_value(ApiResponse::ok(ListContainersResponse { containers }))
                .unwrap()
        }
        ApiRequest::ContainerStatus(p) => match state.containers.get(&p.id) {
            Some(c) => serde_json::to_value(ApiResponse::ok(ContainerStatusResponse {
                id: c.id.clone(),
                name: c.name.clone(),
                state: c.state.clone(),
                pid: c.pid,
                exit_code: None,
                bundle_path: c.bundle_path.display().to_string(),
            }))
            .unwrap(),
            None => serde_json::to_value(ApiResponse::<ContainerStatusResponse>::err(
                "NOT_FOUND",
                format!("container {} not found", p.id),
            ))
            .unwrap(),
        },
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use licontainer_proto::{CreateContainerRequest, ListContainersRequest, PullImageRequest};
    use tempfile::TempDir;

    #[test]
    fn pull_image_mocked_store() {
        let tmp = TempDir::new().unwrap();
        std::env::set_var("LI_CONTAINER_STORE", tmp.path());
        let mut state = DaemonState::new(tmp.path().join("daemon"));

        let resp = handle_request(
            &mut state,
            ApiRequest::PullImage(PullImageRequest {
                reference: "hello:latest".into(),
                export_squashfs: false,
            }),
        );
        assert!(resp["ok"].as_bool().unwrap_or(false));
    }

    #[test]
    fn list_empty_containers() {
        let tmp = TempDir::new().unwrap();
        let mut state = DaemonState::new(tmp.path().to_path_buf());
        let resp = handle_request(&mut state, ApiRequest::ListContainers(ListContainersRequest {}));
        assert!(resp["ok"].as_bool().unwrap_or(false));
        assert_eq!(resp["data"]["containers"].as_array().unwrap().len(), 0);
    }
}
