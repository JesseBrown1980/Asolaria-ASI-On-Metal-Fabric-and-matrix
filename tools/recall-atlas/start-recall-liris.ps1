$ErrorActionPreference = 'Stop'

$keyFile = Join-Path $env:USERPROFILE '.asolaria\recall.key'
if (!(Test-Path -LiteralPath $keyFile)) {
  $dir = Split-Path -Parent $keyFile
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $bytes = New-Object byte[] 32
  [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
  [Convert]::ToBase64String($bytes) | Set-Content -LiteralPath $keyFile -NoNewline -Encoding ASCII
}

$env:ASOLARIA_RECALL_BIND = if ($env:ASOLARIA_RECALL_BIND) { $env:ASOLARIA_RECALL_BIND } else { '0.0.0.0' }
$env:ASOLARIA_RECALL_COLONY = if ($env:ASOLARIA_RECALL_COLONY) { $env:ASOLARIA_RECALL_COLONY } else { 'liris' }
$env:ASOLARIA_RECALL_OWNER_PID = if ($env:ASOLARIA_RECALL_OWNER_PID) { $env:ASOLARIA_RECALL_OWNER_PID } else { 'OP-RAYSSA-PID' }
$env:ASOLARIA_RECALL_ALLOWED_OWNER_PIDS = if ($env:ASOLARIA_RECALL_ALLOWED_OWNER_PIDS) { $env:ASOLARIA_RECALL_ALLOWED_OWNER_PIDS } else { 'OP-JESSE-PID,OP-RAYSSA-PID' }
$env:ASOLARIA_RECALL_KEY_FILE = if ($env:ASOLARIA_RECALL_KEY_FILE) { $env:ASOLARIA_RECALL_KEY_FILE } else { $keyFile }

node (Join-Path $PSScriptRoot 'serve-recall.cjs')
