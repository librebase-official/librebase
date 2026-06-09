# Build Li Container Engine via WSL (Linux lic toolchain).
param(
  [string]$LicRoot = "$env:USERPROFILE\Documents\Programming\li\lic"
)
function ConvertTo-WslPath([string]$WinPath) {
  $full = (Resolve-Path $WinPath).Path
  $drive = $full.Substring(0, 1).ToLower()
  $rest = $full.Substring(2).Replace("\", "/")
  return "/mnt/$drive$rest"
}
$ContainerRoot = Split-Path $PSScriptRoot -Parent
if (-not (Test-Path $LicRoot)) {
  Write-Error "LIC_ROOT not found: $LicRoot - pass -LicRoot to your lic checkout"
}
$wslContainer = ConvertTo-WslPath $ContainerRoot
$wslLic = ConvertTo-WslPath $LicRoot
$cmd = "export LIC_ROOT=$wslLic; cd $wslContainer; sed -i 's/\r`$//' scripts/*.sh; bash scripts/build-li.sh"
wsl bash -lc $cmd
