# Deploy Librebase landing+Studio to IONOS VPS (sail/majico host) and point librebase.xyz
# Requires: PuTTY plink/pscp, keys in sail.black/.env.local + majico/.env.local + klaut.pro/.env.local
$ErrorActionPreference = "Stop"
$LibrebaseRoot = Split-Path $PSScriptRoot -Parent
if (-not (Test-Path (Join-Path $LibrebaseRoot "data-studio-ui\package.json"))) {
  $LibrebaseRoot = "C:\Users\Julian\Documents\Programming\librebase"
}
$SailEnv = "C:\Users\Julian\Documents\Programming\sail.black\.env.local"
$MajEnv = "C:\Users\Julian\Documents\Programming\majico\.env.local"
$KlaEnv = "C:\Users\Julian\Documents\Programming\klaut.pro\.env.local"

function Get-EnvValue([string]$File, [string]$Key) {
  foreach ($line in Get-Content $File -Encoding UTF8) {
    if ($line -match "^\s*#") { continue }
    if ($line -match "^\s*$([regex]::Escape($Key))\s*=\s*(.*)\s*$") {
      return $Matches[1].Trim().Trim('"').Trim("'")
    }
  }
  return $null
}

$VpsHost = Get-EnvValue $MajEnv "VPS_HOST"
$VpsUser = Get-EnvValue $MajEnv "VPS_USER"
$VpsPass = Get-EnvValue $MajEnv "VPS_PASSWORD"
$HostKey = Get-EnvValue $MajEnv "VPS_HOSTKEY"
$IonosKey = Get-EnvValue $KlaEnv "IONOS_API_KEY"
$IonosSecret = Get-EnvValue $KlaEnv "IONOS_API_SECRET"
# Prefer VPS Majico Supabase (supabase.majico.xyz). Do NOT use supabase.majico.d3bu7.com
# for waitlist — that host is a different DB and will 404 the librebase_waitlist table.
$SbUrl = Get-EnvValue $SailEnv "LIBREBASE_SUPABASE_URL"
$SbKey = Get-EnvValue $SailEnv "LIBREBASE_SUPABASE_SERVICE_ROLE_KEY"
if (-not $SbUrl) { $SbUrl = "https://supabase.majico.xyz" }
# Service role is read from the VPS credentials file during deploy if local key missing.

if (-not ($VpsHost -and $VpsUser -and $VpsPass -and $HostKey)) { throw "VPS_* missing in majico/.env.local" }
if (-not ($IonosKey -and $IonosSecret)) { throw "IONOS_* missing" }

$Plink = "C:\Program Files\PuTTY\plink.exe"
$Pscp = "C:\Program Files\PuTTY\pscp.exe"
$RemoteDir = "/opt/librebase"
$UiDir = Join-Path $LibrebaseRoot "data-studio-ui"

Write-Host "1) Upsert DNS librebase.xyz + www -> $VpsHost"
$headers = @{
  "X-API-Key" = "${IonosKey}.${IonosSecret}"
  "Accept" = "application/json"
  "Content-Type" = "application/json"
}
$zoneId = "6da55e19-5fd6-11f1-85a2-0a5864440eb6"
$detail = Invoke-RestMethod -Uri "https://api.hosting.ionos.com/dns/v1/zones/$zoneId" -Headers $headers
function Upsert-A([string]$Name, [string]$Ip) {
  $existing = @($detail.records) | Where-Object { $_.name -eq $Name -and $_.type -eq "A" } | Select-Object -First 1
  $payload = @{ name = $Name; type = "A"; content = $Ip; ttl = 300; disabled = $false }
  if ($existing) {
    Invoke-RestMethod -Method PUT -Uri "https://api.hosting.ionos.com/dns/v1/zones/$zoneId/records/$($existing.id)" -Headers $headers -Body ($payload | ConvertTo-Json -Compress) | Out-Null
    Write-Host "Updated A $Name"
  } else {
    Invoke-RestMethod -Method POST -Uri "https://api.hosting.ionos.com/dns/v1/zones/$zoneId/records" -Headers $headers -Body ((,@($payload) | ConvertTo-Json -Depth 5 -Compress)) | Out-Null
    Write-Host "Created A $Name"
  }
}
Upsert-A "librebase.xyz" $VpsHost
Upsert-A "www.librebase.xyz" $VpsHost

Write-Host "2) Create waitlist table on Majico Supabase"
$sqlPath = Join-Path $LibrebaseRoot "deploy\supabase\001_librebase_waitlist.sql"
& $Pscp -batch -pw $VpsPass -hostkey $HostKey $sqlPath "${VpsUser}@${VpsHost}:/tmp/001_librebase_waitlist.sql"
& $Plink -batch -ssh "$VpsUser@$VpsHost" -pw $VpsPass -hostkey $HostKey "docker exec -i supabase-db psql -U postgres -v ON_ERROR_STOP=1 < /tmp/001_librebase_waitlist.sql"

Write-Host "3) Sync app to $RemoteDir"
& $Plink -batch -ssh "$VpsUser@$VpsHost" -pw $VpsPass -hostkey $HostKey "mkdir -p $RemoteDir"
# rsync-like via tar over ssh for speed
$tar = Join-Path $env:TEMP "librebase-ui.tgz"
Push-Location $UiDir
tar -czf $tar --exclude=node_modules --exclude=.next --exclude=.git .
Pop-Location
& $Pscp -batch -pw $VpsPass -hostkey $HostKey $tar "${VpsUser}@${VpsHost}:/tmp/librebase-ui.tgz"
& $Pscp -batch -pw $VpsPass -hostkey $HostKey (Join-Path $LibrebaseRoot "deploy\nginx-librebase.xyz.conf") "${VpsUser}@${VpsHost}:/tmp/nginx-librebase.xyz.conf"

if ($SbKey) {
  $envFileRemote = @"
LIBREBASE_SUPABASE_URL=$SbUrl
LIBREBASE_SUPABASE_SERVICE_ROLE_KEY=$SbKey
"@
  $envLocal = Join-Path $env:TEMP "librebase.env"
  Set-Content -Path $envLocal -Value $envFileRemote -Encoding ascii
  & $Pscp -batch -pw $VpsPass -hostkey $HostKey $envLocal "${VpsUser}@${VpsHost}:/tmp/librebase.env"
} else {
  Write-Host "No local LIBREBASE_SUPABASE_SERVICE_ROLE_KEY; building .env from VPS majico-supabase-credentials.env"
  & $Plink -batch -ssh "$VpsUser@$VpsHost" -pw $VpsPass -hostkey $HostKey "python3 -c `"from pathlib import Path; v={}; [v.__setitem__(l.split('=',1)[0], l.split('=',1)[1].strip().strip(chr(34))) for l in Path('/root/majico-supabase-credentials.env').read_text().splitlines() if l and not l.startswith('#') and '=' in l]; Path('/tmp/librebase.env').write_text('LIBREBASE_SUPABASE_URL=https://supabase.majico.xyz\nLIBREBASE_SUPABASE_SERVICE_ROLE_KEY='+v['SERVICE_ROLE_KEY']+'\n')`""
}

Write-Host "4) Build + run container, nginx, certbot"
# Write remote script with LF endings — Windows CRLF breaks bash (`build\r`, `nginx\x0d`).
$remoteScript = @"
set -e
mkdir -p $RemoteDir
tar -xzf /tmp/librebase-ui.tgz -C $RemoteDir
cp /tmp/librebase.env $RemoteDir/.env
cp /tmp/nginx-librebase.xyz.conf /etc/nginx/conf.d/librebase.xyz.conf
cd $RemoteDir
docker compose --env-file .env build
docker compose --env-file .env up -d --force-recreate
nginx -t && systemctl reload nginx
if [ ! -d /etc/letsencrypt/live/librebase.xyz ]; then
  certbot --nginx -d librebase.xyz -d www.librebase.xyz --non-interactive --agree-tos -m julian.kleber@sail.black --redirect || true
else
  certbot renew --quiet || true
fi
docker ps --filter name=librebase --format '{{.Names}} {{.Status}}'
curl -sS -o /dev/null -w 'local:%{http_code}\n' http://127.0.0.1:3005/ || true
"@
$remoteScript = $remoteScript -replace "`r`n", "`n"
$remoteScriptPath = Join-Path $env:TEMP "librebase-ionos-remote.sh"
[System.IO.File]::WriteAllText($remoteScriptPath, $remoteScript + "`n", [System.Text.UTF8Encoding]::new($false))
& $Pscp -batch -pw $VpsPass -hostkey $HostKey $remoteScriptPath "${VpsUser}@${VpsHost}:/tmp/librebase-ionos-remote.sh"
& $Plink -batch -ssh "$VpsUser@$VpsHost" -pw $VpsPass -hostkey $HostKey "bash /tmp/librebase-ionos-remote.sh"

Write-Host "Done. https://librebase.xyz (DNS may take a few minutes)"
