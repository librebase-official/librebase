#!/usr/bin/env pwsh
# PowerShell wrapper for export-lidb-oci-image.sh (run in WSL or Git Bash).
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
bash "$ScriptDir/export-lidb-oci-image.sh" @args
