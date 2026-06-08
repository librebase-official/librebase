mod client;

use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "lictl", about = "licontainer CLI", version)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Pull an OCI image
    Pull {
        reference: String,
        #[arg(long)]
        squashfs: bool,
    },
    /// Run a container (pull + create + start)
    Run {
        image: String,
        #[arg(long)]
        name: Option<String>,
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<String>,
    },
    /// List containers
    Ps,
    /// Stop a container
    Stop {
        id: String,
    },
    /// Print version
    Version,
}

fn main() {
    let cli = Cli::parse();
    let result = match cli.command {
        Commands::Pull { reference, squashfs } => client::pull(&reference, squashfs),
        Commands::Run { image, name, args } => {
            client::run(&image, name.as_deref(), &args)
        }
        Commands::Ps => client::ps(),
        Commands::Stop { id } => client::stop(&id),
        Commands::Version => {
            println!("lictl {}", env!("CARGO_PKG_VERSION"));
            Ok(())
        }
    };

    if let Err(e) = result {
        eprintln!("{{\"ok\":false,\"message\":\"{e}\"}}");
        std::process::exit(1);
    }
}
