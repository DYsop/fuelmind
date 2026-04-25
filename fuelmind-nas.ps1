[CmdletBinding()]
param(
    [ValidateSet("start", "rebuild", "stop", "restart", "status", "logs", "frontend-logs", "health")]
    [string]$Action = "start",
    [string]$NasHost = $(if ($env:FUELMIND_NAS_HOST) { $env:FUELMIND_NAS_HOST } else { "nas.local" }),
    [string]$NasUser = $(if ($env:FUELMIND_NAS_USER) { $env:FUELMIND_NAS_USER } else { "fuelmind" }),
    [string]$ProjectDir = $(if ($env:FUELMIND_PROJECT_DIR) { $env:FUELMIND_PROJECT_DIR } else { "/volume1/docker/fuelmind" }),
    [string]$SshKeyPath = "$HOME\.ssh\fuelmind_nas_ed25519",
    [switch]$OpenUrls
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Fail {
    param([string]$Message)
    Write-Host ""
    Write-Host "Fehler: $Message" -ForegroundColor Red
    exit 1
}

function Ensure-Command {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [string]$InstallHint = ""
    )

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        $hint = if ($InstallHint) { "`n$InstallHint" } else { "" }
        Fail "$Name wurde auf diesem Windows-Rechner nicht gefunden.$hint"
    }
}

function Invoke-Ssh {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RemoteCommand
    )

    $sshArgs = @()
    if (Test-Path -LiteralPath $SshKeyPath) {
        $sshArgs += @("-i", $SshKeyPath)
    }
    $sshArgs += "$NasUser@$NasHost"
    $sshArgs += $RemoteCommand

    & ssh @sshArgs
    if ($LASTEXITCODE -ne 0) {
        Fail "Der SSH-Befehl auf dem NAS ist fehlgeschlagen.`nPruefe FUELMIND_NAS_HOST, FUELMIND_NAS_USER und ggf. den SSH-Schluessel."
    }
}

Ensure-Command -Name "ssh" -InstallHint "Installiere den OpenSSH-Client in Windows oder aktiviere ihn unter 'Optionale Features'."

Write-Step "Pruefe SSH-Verbindung zu $NasUser@$NasHost"
$probeArgs = @("-o", "BatchMode=yes", "-o", "ConnectTimeout=8")
if (Test-Path -LiteralPath $SshKeyPath) {
    $probeArgs += @("-i", $SshKeyPath)
}
$probeArgs += "$NasUser@$NasHost"
$probeArgs += "echo connected"
& ssh @probeArgs 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    if (Test-Path -LiteralPath $SshKeyPath) {
        Write-Host "Hinweis: SSH mit Schluessel hat nicht automatisch funktioniert. Es wird gleich interaktiv versucht." -ForegroundColor Yellow
    }
    else {
        Write-Host "Hinweis: Es wurde noch kein SSH-Schluessel gefunden. Fuehre bei Bedarf zuerst setup-nas-ssh-key.ps1 aus." -ForegroundColor Yellow
        Write-Host "Voruebergehend fragt das Skript gleich wahrscheinlich dein NAS-Passwort ab." -ForegroundColor Yellow
    }
}

$remotePreflight = @"
set -e
if [ ! -d '$ProjectDir' ]; then
  echo 'PROJECT_DIR_MISSING'
  exit 41
fi
if [ ! -f '$ProjectDir/fuelmind.sh' ]; then
  echo 'HELPER_SCRIPT_MISSING'
  exit 42
fi
if ! command -v docker >/dev/null 2>&1; then
  echo 'DOCKER_MISSING'
  exit 43
fi
if ! sudo -n docker compose version >/dev/null 2>&1; then
  echo 'SUDO_PASSWORD_REQUIRED'
fi
"@

Write-Step "Pruefe Projektordner und Docker auf dem NAS"
$preflightArgs = @()
if (Test-Path -LiteralPath $SshKeyPath) {
    $preflightArgs += @("-i", $SshKeyPath)
}
$preflightArgs += "$NasUser@$NasHost"
$preflightArgs += $remotePreflight
$preflightOutput = & ssh @preflightArgs
$preflightExit = $LASTEXITCODE

if ($preflightExit -eq 41) {
    Fail "Projektordner auf dem NAS nicht gefunden: $ProjectDir"
}
if ($preflightExit -eq 42) {
    Fail "fuelmind.sh wurde auf dem NAS nicht gefunden in: $ProjectDir"
}
if ($preflightExit -eq 43) {
    Fail "Docker ist auf dem NAS nicht verfuegbar oder nicht im PATH."
}
if ($preflightExit -ne 0) {
    Fail "Die Vorpruefung auf dem NAS ist fehlgeschlagen."
}

if (($preflightOutput | Out-String) -match "SUDO_PASSWORD_REQUIRED") {
    Fail "Docker ist auf dem NAS noch nicht fuer automatische sudo-Aufrufe freigegeben.`nFuehre einmal dieses Windows-Setup aus:`n  powershell -ExecutionPolicy Bypass -File .\setup-nas-docker-sudo.ps1"
}

$remoteAction = @"
cd '$ProjectDir'
bash './fuelmind.sh' '$Action'
"@

Write-Step "Fuehre FuelMind-Aktion aus: $Action"
Invoke-Ssh -RemoteCommand $remoteAction

if ($Action -in @("start", "restart", "rebuild", "status", "health")) {
    Write-Host ""
    Write-Host "FuelMind URLs:" -ForegroundColor Green
    Write-Host "- Frontend: http://$NasHost:3000"
    Write-Host "- Backend-Health: http://$NasHost:8000/api/health"
}

if ($OpenUrls -and $Action -in @("start", "restart", "rebuild")) {
    Write-Step "Oeffne Frontend im Browser"
    Start-Process "http://$NasHost:3000"
}
