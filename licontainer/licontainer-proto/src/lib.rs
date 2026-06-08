//! JSON API types shared between licontainerd, lictl, and licri.

use serde::{Deserialize, Serialize};

pub const DEFAULT_SOCKET_PATH: &str = "/run/licontainer/licontainerd.sock";
pub const DEFAULT_STORE_PATH: &str = "/var/lib/licontainer";

/// API request envelope sent over the Unix socket.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "method", content = "params")]
pub enum ApiRequest {
    PullImage(PullImageRequest),
    CreateContainer(CreateContainerRequest),
    StartContainer(StartContainerRequest),
    StopContainer(StopContainerRequest),
    ListContainers(ListContainersRequest),
    ContainerStatus(ContainerStatusRequest),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PullImageRequest {
    pub reference: String,
    #[serde(default)]
    pub export_squashfs: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateContainerRequest {
    pub name: String,
    pub image: String,
    #[serde(default)]
    pub args: Vec<String>,
    #[serde(default)]
    pub env: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StartContainerRequest {
    pub id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StopContainerRequest {
    pub id: String,
    #[serde(default = "default_signal")]
    pub signal: String,
}

fn default_signal() -> String {
    "SIGTERM".into()
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ListContainersRequest {}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContainerStatusRequest {
    pub id: String,
}

/// API response envelope.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiResponse<T> {
    pub ok: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<T>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<ApiError>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiError {
    pub code: String,
    pub message: String,
}

impl<T> ApiResponse<T> {
    pub fn ok(data: T) -> Self {
        Self {
            ok: true,
            data: Some(data),
            error: None,
        }
    }

    pub fn err(code: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            ok: false,
            data: None,
            error: Some(ApiError {
                code: code.into(),
                message: message.into(),
            }),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PullImageResponse {
    pub reference: String,
    pub digest: String,
    pub store_path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateContainerResponse {
    pub id: String,
    pub name: String,
    pub bundle_path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StartContainerResponse {
    pub id: String,
    pub pid: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StopContainerResponse {
    pub id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContainerSummary {
    pub id: String,
    pub name: String,
    pub state: String,
    pub image: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub pid: Option<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ListContainersResponse {
    pub containers: Vec<ContainerSummary>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContainerStatusResponse {
    pub id: String,
    pub name: String,
    pub state: String,
    pub pid: Option<u32>,
    pub exit_code: Option<i32>,
    pub bundle_path: String,
}

/// Entitlement gate hook — returns true when pull/create is allowed.
/// TODO: wire to Librebase billing / license service before cloud deploy.
pub fn check_entitlement(_action: &str) -> bool {
    if std::env::var("LI_CONTAINER_SKIP_ENTITLEMENT").ok().as_deref() == Some("1") {
        return true;
    }
    // Open-source / local dev: allow by default until billing ships.
    true
}
