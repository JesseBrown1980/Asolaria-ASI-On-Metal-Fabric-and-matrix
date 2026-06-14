# ═══════════════════════════════════════════════════════════════════════════
# Asolaria Tool Advisor — PowerShell $profile wrapper
# ═══════════════════════════════════════════════════════════════════════════
# W113 Tier-1 enforcement layer (per ARCH-INTERCEPT-final.md §3)
# Wave-PID:    W113-TOOL-ADVISOR-WAVE-2026-05-21
# Authority:   ASOLARIA-HERMES-ARCHITECT-CORRECTION-PID-2026-05-19
# Vantage:     acer (acer-Claude orchestrator)
# Install gate: operator-witness (manual paste into $PROFILE on operator approval)
#
# WHAT THIS DOES
# Intercepts 6 risky disk/USB commands in PowerShell sessions:
#   diskpart · Format-Volume · Clear-Disk · Remove-Partition · New-Partition · Initialize-Disk
# Before letting each run, POSTs to http://127.0.0.1:4949/api/tool-advisor and applies the verdict:
#   HARD-DENY        → print reason + substitute_hint, refuse to run
#   DEFER-TO-APEX    → print canonical_tool, require explicit confirmation
#   REDIRECT-TO-X    → print canonical_tool + peer_endpoint, route operator there
#   GUIDED-EXECUTE   → print canonical_tool, allow with operator confirmation
# Fail-mode: if advisor is unreachable, fail-CLOSED on write/format/clear; fail-OPEN on read.
# Per W113 INTERCEPT R3 §4.
# ═══════════════════════════════════════════════════════════════════════════

$ASOLARIA_ADVISOR_URL = if ($env:ACER_ADVISOR_URL)  { $env:ACER_ADVISOR_URL }  else { 'http://127.0.0.1:4949/api/tool-advisor' }
$ASOLARIA_AGENT_PID   = if ($env:ASOLARIA_AGENT_PID) { $env:ASOLARIA_AGENT_PID } else { "PSWRAP-USER-$($env:USERNAME)-H$(([math]::Abs([hashtable]::new().GetHashCode())).ToString('X4'))" }
$ASOLARIA_VANTAGE     = if ($env:ASOLARIA_VANTAGE)   { $env:ASOLARIA_VANTAGE }   else { 'acer' }

function _Asolaria-QueryAdvisor {
    param([string]$Verb, [string]$Target, [string]$Scope = 'core')
    $body = @{
        verb       = $Verb
        target     = $Target
        agent_pid  = $ASOLARIA_AGENT_PID
        scope      = $Scope
        vantage    = $ASOLARIA_VANTAGE
        intent     = 'powershell-wrapper-interception'
    } | ConvertTo-Json -Compress
    try {
        $resp = Invoke-RestMethod -Uri $ASOLARIA_ADVISOR_URL -Method POST -Body $body -ContentType 'application/json' -TimeoutSec 4 -ErrorAction Stop
        return $resp
    } catch {
        # Fail-CLOSED on writes/destructive; fail-OPEN on read-only.
        $failClosedVerbs = @('format', 'diskpart-clean', 'repartition', 'raw-write')
        if ($failClosedVerbs -contains $Verb) {
            return @{ verdict = 'HARD-DENY'; reason = "advisor unreachable AND verb=$Verb in fail-closed set"; canonical_tool = $null; substitute_hint = @() }
        }
        return @{ verdict = 'GUIDED-EXECUTE'; reason = "advisor unreachable, fail-open on read-only"; canonical_tool = $null; substitute_hint = @() }
    }
}

function _Asolaria-PrintVerdict {
    param($Verdict, [string]$OriginalCmd)
    Write-Host ""
    Write-Host "═══════ ASOLARIA TOOL ADVISOR ═══════" -ForegroundColor Cyan
    Write-Host "  Intercepted: $OriginalCmd" -ForegroundColor Yellow
    Write-Host "  Verdict:     $($Verdict.verdict)" -ForegroundColor $(if ($Verdict.verdict -eq 'HARD-DENY') { 'Red' } elseif ($Verdict.verdict -eq 'GUIDED-EXECUTE') { 'Green' } else { 'Yellow' })
    Write-Host "  Reason:      $($Verdict.reason)"
    if ($Verdict.canonical_tool) { Write-Host "  Canonical:   $($Verdict.canonical_tool)" -ForegroundColor Green }
    if ($Verdict.substitute_hint -and $Verdict.substitute_hint.Count -gt 0) {
        Write-Host "  Substitutes: $($Verdict.substitute_hint -join ', ')" -ForegroundColor Magenta
    }
    if ($Verdict.peer_endpoint) { Write-Host "  Peer:        $($Verdict.peer_endpoint)" }
    Write-Host "  Authority:   $($Verdict.auth_anchor_pid)"
    Write-Host "  Audit row:   $($Verdict.audit_row_hash)" -ForegroundColor DarkGray
    Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
}

function diskpart {
    param([Parameter(ValueFromRemainingArguments=$true)]$args)
    $v = _Asolaria-QueryAdvisor -Verb 'diskpart-clean' -Target ($args -join ' ')
    _Asolaria-PrintVerdict $v 'diskpart'
    if ($v.verdict -eq 'HARD-DENY') { Write-Host "  → BLOCKED. Override requires apex cosign + operator-witness." -ForegroundColor Red; return }
    if ($v.verdict -eq 'DEFER-TO-APEX') { Write-Host "  → DEFERRED. Operator must explicitly authorize." -ForegroundColor Yellow; return }
    $confirm = Read-Host "  → Proceed with original diskpart? [y/N]"
    if ($confirm -eq 'y') { & "$env:SystemRoot\System32\diskpart.exe" @args } else { Write-Host "  Canceled." }
}

function Format-Volume {
    param([Parameter(ValueFromRemainingArguments=$true)]$args)
    $v = _Asolaria-QueryAdvisor -Verb 'format' -Target ($args -join ' ')
    _Asolaria-PrintVerdict $v 'Format-Volume'
    if ($v.verdict -eq 'HARD-DENY') { return }
    if ($v.verdict -eq 'DEFER-TO-APEX') { return }
    $confirm = Read-Host "  → Proceed with original Format-Volume? [y/N]"
    if ($confirm -eq 'y') { Microsoft.PowerShell.Management\Format-Volume @args }
}

function Clear-Disk {
    param([Parameter(ValueFromRemainingArguments=$true)]$args)
    $v = _Asolaria-QueryAdvisor -Verb 'diskpart-clean' -Target ($args -join ' ')
    _Asolaria-PrintVerdict $v 'Clear-Disk'
    if ($v.verdict -eq 'HARD-DENY') { return }
    if ($v.verdict -eq 'DEFER-TO-APEX') { return }
    $confirm = Read-Host "  → Proceed with original Clear-Disk? [y/N]"
    if ($confirm -eq 'y') { Storage\Clear-Disk @args }
}

function Remove-Partition {
    param([Parameter(ValueFromRemainingArguments=$true)]$args)
    $v = _Asolaria-QueryAdvisor -Verb 'repartition' -Target ($args -join ' ')
    _Asolaria-PrintVerdict $v 'Remove-Partition'
    if ($v.verdict -eq 'HARD-DENY') { return }
    if ($v.verdict -eq 'DEFER-TO-APEX') { return }
    $confirm = Read-Host "  → Proceed? [y/N]"
    if ($confirm -eq 'y') { Storage\Remove-Partition @args }
}

function New-Partition {
    param([Parameter(ValueFromRemainingArguments=$true)]$args)
    $v = _Asolaria-QueryAdvisor -Verb 'repartition' -Target ($args -join ' ')
    _Asolaria-PrintVerdict $v 'New-Partition'
    if ($v.verdict -eq 'HARD-DENY') { return }
    if ($v.verdict -eq 'DEFER-TO-APEX') { return }
    $confirm = Read-Host "  → Proceed? [y/N]"
    if ($confirm -eq 'y') { Storage\New-Partition @args }
}

function Initialize-Disk {
    param([Parameter(ValueFromRemainingArguments=$true)]$args)
    $v = _Asolaria-QueryAdvisor -Verb 'repartition' -Target ($args -join ' ')
    _Asolaria-PrintVerdict $v 'Initialize-Disk'
    if ($v.verdict -eq 'HARD-DENY') { return }
    if ($v.verdict -eq 'DEFER-TO-APEX') { return }
    $confirm = Read-Host "  → Proceed? [y/N]"
    if ($confirm -eq 'y') { Storage\Initialize-Disk @args }
}

# WMI/CIM HARD-DENY shims (per liris ethernet-drop canon 2026-05-12)
function Get-WmiObject {
    param([Parameter(ValueFromRemainingArguments=$true)]$args)
    $v = _Asolaria-QueryAdvisor -Verb 'wmi-cim-probe' -Target ($args -join ' ')
    _Asolaria-PrintVerdict $v 'Get-WmiObject'
    Write-Host "  → SUBSTITUTE with: $($v.substitute_hint -join ' / ')" -ForegroundColor Magenta
}
function Get-CimInstance {
    param([Parameter(ValueFromRemainingArguments=$true)]$args)
    $v = _Asolaria-QueryAdvisor -Verb 'wmi-cim-probe' -Target ($args -join ' ')
    _Asolaria-PrintVerdict $v 'Get-CimInstance'
    Write-Host "  → SUBSTITUTE with: $($v.substitute_hint -join ' / ')" -ForegroundColor Magenta
}

Write-Host "[Asolaria] Tool Advisor wrapper LOADED · W113 · advisor=$ASOLARIA_ADVISOR_URL · agent_pid=$ASOLARIA_AGENT_PID" -ForegroundColor DarkCyan
