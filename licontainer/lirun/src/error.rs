//! OCI runtime error types and JSON stderr output.

use serde::Serialize;
use thiserror::Error;

pub const VERSION: &str = env!("CARGO_PKG_VERSION");

pub type RunResult<T> = Result<T, RunError>;

#[derive(Debug, Error)]
pub enum RunError {
    #[error("bundle not found: {0}")]
    BundleNotFound(String),
    #[error("invalid bundle config: {0}")]
    InvalidConfig(String),
    #[error("container {0} not found")]
    ContainerNotFound(String),
    #[error("container {0} already exists")]
    ContainerExists(String),
    #[error("invalid state transition: {0}")]
    InvalidState(String),
    #[error("platform unsupported: {0}")]
    Unsupported(String),
    #[error("runtime error: {0}")]
    Runtime(String),
    #[error("io error: {0}")]
    Io(#[from] std::io::Error),
    #[error("json error: {0}")]
    Json(#[from] serde_json::Error),
}

#[derive(Debug, Serialize)]
pub struct ErrorPayload {
    pub ok: bool,
    pub code: String,
    pub message: String,
}

impl RunError {
    pub fn code(&self) -> &'static str {
        match self {
            RunError::BundleNotFound(_) => "BUNDLE_NOT_FOUND",
            RunError::InvalidConfig(_) => "INVALID_CONFIG",
            RunError::ContainerNotFound(_) => "CONTAINER_NOT_FOUND",
            RunError::ContainerExists(_) => "CONTAINER_EXISTS",
            RunError::InvalidState(_) => "INVALID_STATE",
            RunError::Unsupported(_) => "UNSUPPORTED",
            RunError::Runtime(_) => "RUNTIME_ERROR",
            RunError::Io(_) => "IO_ERROR",
            RunError::Json(_) => "JSON_ERROR",
        }
    }

    pub fn to_json(&self) -> String {
        let payload = ErrorPayload {
            ok: false,
            code: self.code().into(),
            message: self.to_string(),
        };
        serde_json::to_string(&payload).unwrap_or_else(|_| {
            r#"{"ok":false,"code":"SERIALIZE_ERROR","message":"failed to serialize error"}"#
                .into()
        })
    }
}

pub fn emit_error(err: &RunError) {
    eprintln!("{}", err.to_json());
}
