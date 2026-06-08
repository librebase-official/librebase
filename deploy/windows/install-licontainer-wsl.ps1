#Requires -RunAsAdministrator
<#
.SYNOPSIS
  Install licontainer inside a WSL2 distro for Windows dev machines.

.DESCRIPTION
  Creates (or reuses) the LibrebaseContainer WSL2 distro, builds licontainer,
  and starts licontainerd. Native Windows containers are out of v1 scope;
  all container workloads run in the Linux engine inside WSL2.
#>
param(
    [string]$DistroName = "LibrebaseContainer",
    [string]$InstallPrefix = "/usr/local"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$LicontainerDir = Join-Path $RepoRoot "licontainer"

Write-Host "==> Checking WSL..."
wsl --status 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "WSL2 is required. Enable WSL and install a Linux distro first."
}

$distros = wsl -l -q
if ($distros -notcontains $DistroName) {
    Write-Host "==> Creating WSL distro '$DistroName' from default Ubuntu..."
    wsl --install -d Ubuntu -n $DistroName
    Write-Host "Complete Ubuntu setup in the new distro, then re-run this script."
    exit 0
}

Write-Host "==> Installing build deps in WSL..."
wsl -d $DistroName -e bash -c "sudo apt-get update && sudo apt-get install -y build-essential libseccomp-dev curl"

Write-Host "==> Copying licontainer sources..."
$WslPath = wsl -d $DistroName -e wslpath -a $LicontainerDir
wsl -d $DistroName -e bash -c "mkdir -p ~/licontainer && cp -r '$WslPath'/* ~/licontainer/ 2>/dev/null || rsync -a '$WslPath/' ~/licontainer/"

Write-Host "==> Building licontainer in WSL..."
wsl -d $DistroName -e bash -c @"
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source `$HOME/.cargo/env
cd ~/licontainer && cargo build --release
sudo install -m 755 target/release/lirun $InstallPrefix/bin/
sudo install -m 755 target/release/licontainerd $InstallPrefix/bin/
sudo install -m 755 target/release/licri $InstallPrefix/bin/
sudo install -m 755 target/release/lictl $InstallPrefix/bin/
sudo mkdir -p /run/licontainer /var/lib/licontainer
"@

Write-Host "==> Starting licontainerd in WSL..."
wsl -d $DistroName -e bash -c "sudo licontainerd --socket /run/licontainer/licontainerd.sock &"

Write-Host @"

Done. Use lictl from Windows — it forwards to WSL distro '$DistroName'.

  `$env:LI_CONTAINER_WSL_DISTRO = '$DistroName'
  lictl run hello-world

Native Windows containers are NOT supported in v1.
"@
