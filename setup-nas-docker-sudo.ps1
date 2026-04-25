[CmdletBinding()]
param(
    [string]$NasHost = $(if ($env:FUELMIND_NAS_HOST) { $env:FUELMIND_NAS_HOST } else { "nas.local" }),
    [string]$NasUser = $(if ($env:FUELMIND_NAS_USER) { $env:FUELMIND_NAS_USER } else { "fuelmind" }),
    [string]$ProjectDir = $(if ($env:FUELMIND_PROJECT_DIR) { $env:FUELMIND_PROJECT_DIR } else { "/volume1/docker/fuelmind" }),
    [string]$SshKeyPath = "$HOME\.ssh\fuelmind_nas_ed25519"
)

$ErrorActionPreference = "Stop"

function Fail {
    param([string]$Message)
    Write-Host ""
    Write-Host "Fehler: $Message" -ForegroundColor Red
    exit 1
}

if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    Fail "ssh wurde auf diesem Windows-Rechner nicht gefunden."
}

$sshArgs = @("-tt")
if (Test-Path -LiteralPath $SshKeyPath) {
    $sshArgs += @("-i", $SshKeyPath)
}
$sshArgs += "$NasUser@$NasHost"
$sshArgs += "cd '$ProjectDir' && bash './scripts/install_fuelmind_sudo.sh'"

Write-Host "Starte einmaliges Docker-sudo-Setup auf dem NAS ..." -ForegroundColor Cyan
Write-Host "Du wirst jetzt einmal nach deinem NAS-/sudo-Passwort gefragt." -ForegroundColor Yellow

& ssh @sshArgs
if ($LASTEXITCODE -ne 0) {
    Fail "Das Docker-sudo-Setup auf dem NAS ist fehlgeschlagen.`nPruefe FUELMIND_NAS_HOST, FUELMIND_NAS_USER und FUELMIND_PROJECT_DIR."
}

Write-Host ""
Write-Host "Fertig. Danach sollten fuelmind-nas.ps1 und fuelmind-nas.bat automatisch funktionieren." -ForegroundColor Green
