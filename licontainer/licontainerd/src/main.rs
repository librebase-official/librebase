mod server;

use clap::Parser;
use licontainer_proto::DEFAULT_SOCKET_PATH;
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use tracing::info;

use server::{DaemonState, SharedState};

#[derive(Parser)]
#[command(name = "licontainerd", about = "licontainer daemon", version)]
struct Cli {
    #[arg(long, default_value = DEFAULT_SOCKET_PATH)]
    socket: PathBuf,
    #[arg(long, env = "LI_CONTAINER_STORE")]
    store: Option<PathBuf>,
}

#[tokio::main]
async fn main() -> std::io::Result<()> {
    tracing_subscriber::fmt::init();
    let cli = Cli::parse();

    let store = cli
        .store
        .unwrap_or_else(|| PathBuf::from("/var/lib/licontainer"));
    let state: SharedState = Arc::new(Mutex::new(DaemonState::load(store)));

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
        // Socket permissions 0600
        use std::os::unix::fs::PermissionsExt;
        std::fs::set_permissions(&cli.socket, std::fs::Permissions::from_mode(0o600))?;

        info!("licontainerd listening on {}", cli.socket.display());

        loop {
            let (mut stream, _) = listener.accept().await?;
            let state = Arc::clone(&state);
            tokio::spawn(async move {
                let mut buf = vec![0u8; 65536];
                match stream.read(&mut buf).await {
                    Ok(n) if n > 0 => {
                        let req: licontainer_proto::ApiRequest =
                            match serde_json::from_slice(&buf[..n]) {
                                Ok(r) => r,
                                Err(e) => {
                                    let err = licontainer_proto::ApiResponse::<()>::err(
                                        "INVALID_REQUEST",
                                        e.to_string(),
                                    );
                                    let _ = stream
                                        .write_all(serde_json::to_string(&err).unwrap().as_bytes())
                                        .await;
                                    return;
                                }
                            };
                        let mut guard = state.lock().unwrap();
                        let resp = server::handle_request(&mut guard, req);
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
        eprintln!("licontainerd requires Unix socket (use WSL2 on Windows)");
        std::process::exit(1);
    }
}
