$ErrorActionPreference = 'Stop'
$dev = '\\.\PHYSICALDRIVE2'
$sectors = @(
  @{lba=0;            label='MBR'},
  @{lba=1;            label='post-MBR-or-GPT-primary-loc'},
  @{lba=2048;         label='partition-1-boot-sector'},
  @{lba=524289000;    label='mid-visible-500GB'},
  @{lba=1048575999;   label='last-declared-partition-sector'},
  @{lba=1048576001;   label='first-continuity-tail-sector'},
  @{lba=2000000000;   label='mid-continuity-tail'},
  @{lba=4095999999;   label='last-sector-of-2TB-drive'}
)
$out = 'C:\HyperBEHCS\store\substrate-inventory-W113-2026-05-21.hbp'
$prevHash = '0000000000000000'
$rows = @()
foreach ($s in $sectors) {
  $result = & python 'C:\asolaria-acer\tools\usb-raw\usb_raw_io.py' --read $s.lba --device $dev 2>&1
  $sha256Line = $result | Select-String '^sha256'
  if (-not $sha256Line) {
    Write-Host ("  sector {0,-10}  ERROR: no sha256 in output" -f $s.lba)
    Write-Host $result
    continue
  }
  $sha256 = $sha256Line.ToString().Split(':',2)[1].Trim()
  $sha16 = $sha256.Substring(0,16)
  $bootHex = 'n/a'
  $bootValid = 'n/a'
  $bootSigLine = $result | Select-String '^boot sig'
  if ($bootSigLine) {
    $bootSigText = $bootSigLine.ToString()
    if ($bootSigText -match '(0x[0-9a-fA-F]+)\s+valid=(\w+)') {
      $bootHex = $matches[1]
      $bootValid = $matches[2].ToLower()
    }
  }
  $ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  $body = "HBPv1|layer=substrate-sector-attest|wave=W113-TOOL-ADVISOR-WAVE-2026-05-21|vantage=acer|device=PHYSICALDRIVE2|sector_lba=$($s.lba)|label=$($s.label)|size_bytes=512|sha256=$sha256|sha16=$sha16|boot_sig_hex=$bootHex|boot_sig_valid=$bootValid|prev_row_hash=$prevHash|authority=ASOLARIA-HERMES-ARCHITECT-CORRECTION-PID-2026-05-19|json=0|runtime=0|promote=0|ts=$ts"
  $sha256Stream = [System.IO.MemoryStream]::new([System.Text.Encoding]::UTF8.GetBytes($body))
  $rowHash = (Get-FileHash -Algorithm SHA256 -InputStream $sha256Stream).Hash.ToLower().Substring(0,16)
  $rows += "$body|row_hash=$rowHash"
  $prevHash = $rowHash
  Write-Host ("  sector {0,-10}  [{1}]  sha16={2}  boot={3}" -f $s.lba, $s.label, $sha16, $bootHex)
}
[System.IO.File]::WriteAllLines($out, $rows, [System.Text.Encoding]::ASCII)
$fileSha = (Get-FileHash $out -Algorithm SHA256).Hash.ToLower()
Set-Content -Path ($out + '.sha256') -Value "$fileSha  $(Split-Path $out -Leaf)" -Encoding ASCII
Write-Host ''
Write-Host "file: $out"
Write-Host "rows: $($rows.Count)"
Write-Host "file_sha256: $fileSha"
