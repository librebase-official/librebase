mod bundle;
mod error;
mod runtime;
mod seccomp;

pub use bundle::ContainerState;
pub use error::{RunError, VERSION};

use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "lirun", about = "OCI runtime for licontainer", version = VERSION)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Print version
    Version,
    /// Create a container from an OCI bundle
    Create {
        #[arg(long)]
        bundle: PathBuf,
        #[arg(long)]
        id: String,
    },
    /// Start a created container
    Start {
        #[arg(long)]
        id: String,
    },
    /// Delete a container
    Delete {
        #[arg(long)]
        id: String,
        #[arg(long, default_value_t = false)]
        force: bool,
    },
    /// Send a signal to a container
    Kill {
        #[arg(long)]
        id: String,
        #[arg(default_value = "SIGKILL")]
        signal: String,
    },
    /// Query container state (JSON on stdout)
    State {
        #[arg(long)]
        id: String,
    },
}

fn main() {
    let cli = Cli::parse();
    let result = match cli.command {
        Commands::Version => {
            println!("lirun {}", VERSION);
            Ok(())
        }
        Commands::Create { bundle, id } => runtime::create(&id, &bundle),
        Commands::Start { id } => runtime::start(&id),
        Commands::Delete { id, force } => runtime::delete(&id, force),
        Commands::Kill { id, signal } => {
            #[cfg(target_os = "linux")]
            {
                use nix::sys::signal::Signal;
                let sig = parse_signal(&signal);
                runtime::kill(&id, sig)
            }
            #[cfg(not(target_os = "linux"))]
            {
                runtime::kill(&id, &signal)
            }
        }
        Commands::State { id } => match runtime::state(&id) {
            Ok(state) => {
                println!("{}", serde_json::to_string(&state).unwrap());
                Ok(())
            }
            Err(e) => Err(e),
        },
    };

    if let Err(e) = result {
        error::emit_error(&e);
        std::process::exit(1);
    }
}

#[cfg(target_os = "linux")]
fn parse_signal(s: &str) -> nix::sys::signal::Signal {
    use nix::sys::signal::Signal;
    match s.to_uppercase().as_str() {
        "SIGTERM" | "TERM" | "15" => Signal::SIGTERM,
        "SIGINT" | "INT" | "2" => Signal::SIGINT,
        "SIGHUP" | "HUP" | "1" => Signal::SIGHUP,
        _ => Signal::SIGKILL,
    }
}
