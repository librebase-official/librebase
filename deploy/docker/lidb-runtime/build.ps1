$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$Image = if ($env:LIBREBASE_RUNTIME_IMAGE) { $env:LIBREBASE_RUNTIME_IMAGE } else { "librebase/lidb-runtime:dev" }

Write-Host "Building $Image from $Root"
docker build -f (Join-Path $Root "deploy\docker\lidb-runtime\Dockerfile") -t $Image $Root
Write-Host "Built $Image"
Write-Host "Load into kind: kind load docker-image $Image --name librebase"
