mod cri;

use clap::Parser;
use cri::{handle_cri, CriRequest, CriState, SharedCriState};
use std::sync::{Arc, Mutex};
use tracing::info;

const DEFAULT_CRI_SOCKET: &str = "/run/licontainer/licri.sock";

#[derive(Parser)]
#[command(name = "licri", about = "Kubernetes CRI shim for licontainer", version)]
struct Cli {
    #[arg(long, default_value = DEFAULT_CRI_SOCKET)]
    socket: std::path::PathBuf,
}

#[tokio::main]
async fn main() -> std::io::Result<()> {
    tracing_subscriber::fmt::init();
    let cli = Cli::parse();

    let state: SharedCriState = Arc::new(Mutex::new(CriState::new()));

    if let Some(parent) = cli.socket.parent() {
        std::fs::create_dir_all(parent)?;
    }
    if cli.socket.exists() {
        std::fs::remove_file(&cli.socket)?;
    }

    #[cfg(unix)]
    {
        use tokio::io::{AsyncReadExt, AsyncWriteExt};
        use tokio::net::UnixListener;

        let listener = UnixListener::bind(&cli.socket)?;
        use std::os::unix::fs::PermissionsExt;
        std::fs::set_permissions(&cli.socket, std::fs::Permissions::from_mode(0o600))?;

        info!("licri CRI shim listening on {}", cli.socket.display());

        loop {
            let (mut stream, _) = listener.accept().await?;
            let state = Arc::clone(&state);
            tokio::spawn(async move {
                let mut buf = vec![0u8; 65536];
                match stream.read(&mut buf).await {
                    Ok(n) if n > 0 => {
                        let req: CriRequest = match serde_json::from_slice(&buf[..n]) {
                            Ok(r) => r,
                            Err(e) => {
                                let resp = cri::CriResponse {
                                    ok: false,
                                    data: None,
                                    error: Some(e.to_string()),
                                };
                                let _ = stream
                                    .write_all(serde_json::to_string(&resp).unwrap().as_bytes())
                                    .await;
                                return;
                            }
                        };
                        let mut guard = state.lock().unwrap();
                        let resp = handle_cri(&mut guard, req);
                        let _ = stream
                            .write_all(serde_json::to_string(&resp).unwrap().as_bytes())
                            .await;
                    }
                    _ => {}
                }
            });
        }
    }

    #[cfg(not(unix))]
    {
        eprintln!("licri requires Unix (Linux nodes only)");
        std::process::exit(1);
    }
}
