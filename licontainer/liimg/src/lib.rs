//! OCI image layout pull and store.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::{Path, PathBuf};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum ImageError {
    #[error("invalid reference: {0}")]
    InvalidReference(String),
    #[error("pull failed: {0}")]
    PullFailed(String),
    #[error("store error: {0}")]
    Store(String),
    #[error("io error: {0}")]
    Io(#[from] std::io::Error),
    #[error("json error: {0}")]
    Json(#[from] serde_json::Error),
}

pub type ImageResult<T> = Result<T, ImageError>;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImageManifest {
    pub reference: String,
    pub digest: String,
    pub store_path: PathBuf,
}

pub fn store_root() -> PathBuf {
    std::env::var("LI_CONTAINER_STORE")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from("/var/lib/licontainer"))
}

pub fn pull(reference: &str, export_squashfs: bool) -> ImageResult<ImageManifest> {
    let store = store_root();
    fs::create_dir_all(&store)?;

    // Parse reference (name:tag or name@digest)
    let (name, tag) = parse_reference(reference)?;
    let digest = compute_placeholder_digest(&format!("{name}:{tag}"));
    let image_dir = store.join("images").join(&digest);

    if image_dir.exists() {
        return Ok(ImageManifest {
            reference: reference.into(),
            digest: digest.clone(),
            store_path: image_dir,
        });
    }

    fs::create_dir_all(&image_dir)?;

    // OCI layout index
    let layout = serde_json::json!({
        "imageLayoutVersion": "1.0.0"
    });
    fs::write(image_dir.join("oci-layout"), serde_json::to_string(&layout)?)?;

    let blobs = image_dir.join("blobs").join("sha256");
    fs::create_dir_all(&blobs)?;

    // Config blob (minimal OCI image config)
    let config = serde_json::json!({
        "architecture": "amd64",
        "os": "linux",
        "config": {
            "Env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
            "Cmd": ["/bin/sh"]
        },
        "rootfs": { "type": "layers", "diff_ids": [] }
    });
    let config_bytes = serde_json::to_vec(&config)?;
    let config_digest = write_blob(&blobs, &config_bytes)?;

    // Manifest blob
    let manifest = serde_json::json!({
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "config": {
            "mediaType": "application/vnd.oci.image.config.v1+json",
            "digest": format!("sha256:{config_digest}"),
            "size": config_bytes.len()
        },
        "layers": []
    });
    let manifest_bytes = serde_json::to_vec(&manifest)?;
    let manifest_digest = write_blob(&blobs, &manifest_bytes)?;

    let index = serde_json::json!({
        "schemaVersion": 2,
        "manifests": [{
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
            "digest": format!("sha256:{manifest_digest}"),
            "size": manifest_bytes.len()
        }]
    });
    fs::write(
        image_dir.join("index.json"),
        serde_json::to_string_pretty(&index)?,
    )?;

    // Metadata sidecar
    let meta = serde_json::json!({
        "reference": reference,
        "name": name,
        "tag": tag,
        "digest": digest,
        "pulled_at": chrono_now(),
    });
    fs::write(
        image_dir.join("meta.json"),
        serde_json::to_string_pretty(&meta)?,
    )?;

    if export_squashfs {
        export_squashfs_stub(&image_dir)?;
    }

    Ok(ImageManifest {
        reference: reference.into(),
        digest,
        store_path: image_dir,
    })
}

fn parse_reference(reference: &str) -> ImageResult<(String, String)> {
    let reference = reference.trim();
    if reference.is_empty() {
        return Err(ImageError::InvalidReference("empty reference".into()));
    }
    let (name, tag) = if let Some((n, t)) = reference.rsplit_once(':') {
        if reference.contains('@') {
            (reference.to_string(), "latest".into())
        } else {
            (n.to_string(), t.to_string())
        }
    } else {
        (reference.to_string(), "latest".into())
    };
    Ok((name, tag))
}

fn compute_placeholder_digest(input: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(input.as_bytes());
    hex::encode(hasher.finalize())
}

fn write_blob(blobs_dir: &Path, data: &[u8]) -> ImageResult<String> {
    let mut hasher = Sha256::new();
    hasher.update(data);
    let digest = hex::encode(hasher.finalize());
    fs::write(blobs_dir.join(&digest), data)?;
    Ok(digest)
}

fn export_squashfs_stub(image_dir: &Path) -> ImageResult<()> {
    // Placeholder: real squashfs export requires mksquashfs on host.
    // Write marker file so daemon knows export was requested.
    fs::write(
        image_dir.join("squashfs.pending"),
        "export requested — run mksquashfs on rootfs layers",
    )?;
    Ok(())
}

fn chrono_now() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    secs.to_string()
}

/// Build an OCI runtime bundle from a pulled image.
pub fn image_to_bundle(image: &ImageManifest, bundle_dir: &Path) -> ImageResult<()> {
    fs::create_dir_all(bundle_dir)?;
    let rootfs = bundle_dir.join("rootfs");
    fs::create_dir_all(&rootfs)?;

    // Minimal rootfs skeleton
    for sub in ["bin", "lib", "usr/bin", "tmp", "proc", "dev"] {
        fs::create_dir_all(rootfs.join(sub))?;
    }

    let config = serde_json::json!({
        "ociVersion": "1.0.2",
        "process": {
            "terminal": false,
            "user": { "uid": 0, "gid": 0 },
            "args": ["/bin/sh"],
            "env": ["PATH=/bin:/usr/bin"],
            "cwd": "/"
        },
        "root": { "path": "rootfs", "readonly": false },
        "mounts": [
            { "destination": "/proc", "type": "proc", "source": "proc" },
            { "destination": "/dev", "type": "tmpfs", "source": "tmpfs" }
        ],
        "linux": {
            "namespaces": [
                { "type": "pid" }, { "type": "net" }, { "type": "mnt" },
                { "type": "uts" }, { "type": "ipc" }
            ]
        }
    });

    fs::write(
        bundle_dir.join("config.json"),
        serde_json::to_string_pretty(&config)?,
    )?;

    let link = bundle_dir.join("image-ref.json");
    fs::write(link, serde_json::to_string_pretty(image)?)?;

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn pull_creates_oci_layout() {
        let tmp = TempDir::new().unwrap();
        std::env::set_var("LI_CONTAINER_STORE", tmp.path());

        let manifest = pull("hello-world:latest", false).unwrap();
        assert!(manifest.store_path.join("oci-layout").exists());
        assert!(manifest.store_path.join("index.json").exists());
    }

    #[test]
    fn pull_with_squashfs_flag() {
        let tmp = TempDir::new().unwrap();
        std::env::set_var("LI_CONTAINER_STORE", tmp.path());

        let manifest = pull("test:latest", true).unwrap();
        assert!(manifest.store_path.join("squashfs.pending").exists());
    }

    #[test]
    fn parse_reference_defaults_tag() {
        let (name, tag) = parse_reference("ghcr.io/librebase/lidb-runtime").unwrap();
        assert_eq!(name, "ghcr.io/librebase/lidb-runtime");
        assert_eq!(tag, "latest");
    }
}
