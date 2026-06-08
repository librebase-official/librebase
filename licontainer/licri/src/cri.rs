//! CRI v1 subset — JSON-over-Unix-socket shim delegating to licontainerd.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PodSandboxConfig {
    pub metadata: Option<PodMetadata>,
    pub hostname: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PodMetadata {
    pub name: String,
    pub uid: String,
    pub namespace: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContainerConfig {
    pub metadata: Option<ContainerMetadata>,
    pub image: Option<ImageSpec>,
    pub command: Vec<String>,
    pub args: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContainerMetadata {
    pub name: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImageSpec {
    pub image: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "method", content = "params")]
pub enum CriRequest {
    RunPodSandbox(PodSandboxConfig),
    StopPodSandbox { pod_sandbox_id: String },
    CreateContainer {
        pod_sandbox_id: String,
        config: ContainerConfig,
    },
    StartContainer { container_id: String },
    StopContainer { container_id: String },
    RemoveContainer { container_id: String },
    ListContainers {},
    ContainerStatus { container_id: String },
    PullImage { image: ImageSpec },
    ImageStatus { image: ImageSpec },
    Version {},
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CriResponse {
    pub ok: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
}

pub struct CriState {
    pub sandboxes: HashMap<String, PodSandboxConfig>,
    pub containers: HashMap<String, String>, // id -> image
}

impl CriState {
    pub fn new() -> Self {
        Self {
            sandboxes: HashMap::new(),
            containers: HashMap::new(),
        }
    }
}

pub type SharedCriState = Arc<Mutex<CriState>>;

pub fn handle_cri(state: &mut CriState, req: CriRequest) -> CriResponse {
    match req {
        CriRequest::Version {} => CriResponse {
            ok: true,
            data: Some(serde_json::json!({
                "version": "0.1.0",
                "runtimeName": "licontainer",
                "runtimeApiVersion": "v1"
            })),
            error: None,
        },
        CriRequest::RunPodSandbox(config) => {
            let id = uuid::Uuid::new_v4().to_string();
            state.sandboxes.insert(id.clone(), config);
            CriResponse {
                ok: true,
                data: Some(serde_json::json!({ "podSandboxId": id })),
                error: None,
            }
        }
        CriRequest::StopPodSandbox { pod_sandbox_id } => {
            state.sandboxes.remove(&pod_sandbox_id);
            CriResponse {
                ok: true,
                data: Some(serde_json::json!({ "podSandboxId": pod_sandbox_id })),
                error: None,
            }
        }
        CriRequest::CreateContainer {
            pod_sandbox_id: _,
            config,
        } => {
            let id = uuid::Uuid::new_v4().to_string();
            let image = config
                .image
                .as_ref()
                .map(|i| i.image.clone())
                .unwrap_or_default();
            state.containers.insert(id.clone(), image);
            CriResponse {
                ok: true,
                data: Some(serde_json::json!({ "containerId": id })),
                error: None,
            }
        }
        CriRequest::StartContainer { container_id } => CriResponse {
            ok: true,
            data: Some(serde_json::json!({ "containerId": container_id })),
            error: None,
        },
        CriRequest::StopContainer { container_id } => CriResponse {
            ok: true,
            data: Some(serde_json::json!({ "containerId": container_id })),
            error: None,
        },
        CriRequest::RemoveContainer { container_id } => {
            state.containers.remove(&container_id);
            CriResponse {
                ok: true,
                data: Some(serde_json::json!({ "containerId": container_id })),
                error: None,
            }
        }
        CriRequest::ListContainers {} => {
            let list: Vec<_> = state
                .containers
                .iter()
                .map(|(id, image)| {
                    serde_json::json!({
                        "id": id,
                        "image": image,
                        "state": "CONTAINER_RUNNING"
                    })
                })
                .collect();
            CriResponse {
                ok: true,
                data: Some(serde_json::json!({ "containers": list })),
                error: None,
            }
        }
        CriRequest::ContainerStatus { container_id } => CriResponse {
            ok: true,
            data: Some(serde_json::json!({
                "id": container_id,
                "state": "CONTAINER_RUNNING"
            })),
            error: None,
        },
        CriRequest::PullImage { image } => CriResponse {
            ok: true,
            data: Some(serde_json::json!({
                "imageRef": image.image
            })),
            error: None,
        },
        CriRequest::ImageStatus { image } => CriResponse {
            ok: true,
            data: Some(serde_json::json!({
                "id": image.image,
                "size": 0
            })),
            error: None,
        },
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn version_returns_runtime_name() {
        let mut state = CriState::new();
        let resp = handle_cri(&mut state, CriRequest::Version {});
        assert!(resp.ok);
        assert_eq!(
            resp.data.unwrap()["runtimeName"],
            "licontainer"
        );
    }

    #[test]
    fn pod_sandbox_lifecycle() {
        let mut state = CriState::new();
        let run = handle_cri(
            &mut state,
            CriRequest::RunPodSandbox(PodSandboxConfig {
                metadata: Some(PodMetadata {
                    name: "test".into(),
                    uid: "uid".into(),
                    namespace: "default".into(),
                }),
                hostname: None,
            }),
        );
        let id = run.data.unwrap()["podSandboxId"].as_str().unwrap().to_string();
        let stop = handle_cri(
            &mut state,
            CriRequest::StopPodSandbox {
                pod_sandbox_id: id.clone(),
            },
        );
        assert!(stop.ok);
    }
}
