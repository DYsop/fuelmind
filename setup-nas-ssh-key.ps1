[CmdletBinding()]
param(
    [string]$NasHost = $(if ($env:FUELMIND_NAS_HOST) { $env:FUELMIND_NAS_HOST } else { "nas.local" }),
    [string]$NasUser = $(if ($env:FUELMIND_NAS_USER) { $env:FUELMIND_NAS_USER } else { "fuelmind" }),
    [string]$KeyPath = "$HOME\.ssh\fuelmind_nas_ed25519",
    [string]$HostAlias = "fuelmind-nas"
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
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Fail "$Name wurde nicht gefunden. Bitte installiere den Windows OpenSSH-Client."
    }
}

function Ensure-LineInFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Line
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        Set-Content -LiteralPath $Path -Value "" -Encoding UTF8
    }

    $content = Get-Content -LiteralPath $Path -ErrorAction Stop
    if ($content -notcontains $Line) {
        Add-Content -LiteralPath $Path -Value $Line -Encoding UTF8
    }
}

Ensure-Command -Name "ssh"
Ensure-Command -Name "ssh-keygen"

$sshDir = Split-Path -Parent $KeyPath
if (-not (Test-Path -LiteralPath $sshDir)) {
    New-Item -ItemType Directory -Path $sshDir | Out-Null
}

if (-not (Test-Path -LiteralPath $KeyPath)) {
    Write-Step "Erzeuge neuen SSH-Schluessel"
    $keygenArgs = "-t ed25519 -f `"$KeyPath`" -N `"`" -C `"fuelmind-nas`""
    $process = Start-Process -FilePath "ssh-keygen" -ArgumentList $keygenArgs -Wait -NoNewWindow -PassThru
    if ($process.ExitCode -ne 0) {
        Fail "ssh-keygen konnte keinen Schluessel erzeugen."
    }
}
else {
    Write-Step "SSH-Schluessel bereits vorhanden"
}

$pubKeyPath = "$KeyPath.pub"
if (-not (Test-Path -LiteralPath $pubKeyPath)) {
    Fail "Der oeffentliche Schluessel wurde nicht gefunden: $pubKeyPath"
}

$publicKey = (Get-Content -LiteralPath $pubKeyPath -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($publicKey)) {
    Fail "Der oeffentliche SSH-Schluessel ist leer."
}

Write-Step "Installiere den oeffentlichen Schluessel auf dem NAS"
Write-Host "Du wirst jetzt wahrscheinlich einmal nach dem NAS-Passwort gefragt." -ForegroundColor Yellow
& ssh "$NasUser@$NasHost" "mkdir -p ~/.ssh && chmod 700 ~/.ssh && touch ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
if ($LASTEXITCODE -ne 0) {
    Fail "Der SSH-Schluessel konnte auf dem NAS nicht vorbereitet werden."
}

$appendCommand = "grep -Fqx '$publicKey' ~/.ssh/authorized_keys || printf '%s`n' '$publicKey' >> ~/.ssh/authorized_keys"
& ssh "$NasUser@$NasHost" $appendCommand
if ($LASTEXITCODE -ne 0) {
    Fail "Der SSH-Schluessel konnte nicht in authorized_keys eingetragen werden."
}

$configPath = Join-Path $sshDir "config"
Write-Step "Ergaenze lokale SSH-Konfiguration"
Ensure-LineInFile -Path $configPath -Line "Host $HostAlias"
Ensure-LineInFile -Path $configPath -Line "    HostName $NasHost"
Ensure-LineInFile -Path $configPath -Line "    User $NasUser"
Ensure-LineInFile -Path $configPath -Line "    IdentityFile $KeyPath"
Ensure-LineInFile -Path $configPath -Line "    IdentitiesOnly yes"

Write-Step "Teste passwortlose Verbindung"
& ssh -o BatchMode=yes -i $KeyPath "$NasUser@$NasHost" "echo SSH_OK"
if ($LASTEXITCODE -ne 0) {
    Fail "Die passwortlose SSH-Verbindung funktioniert noch nicht."
}

Write-Host ""
Write-Host "Fertig. Ab jetzt sollte die Verbindung automatisch funktionieren." -ForegroundColor Green
Write-Host "Verwendeter Schluessel: $KeyPath"
Write-Host "SSH-Hostalias: $HostAlias"
Write-Host "NAS-Host: $NasHost"
Write-Host "NAS-User: $NasUser"
Write-Host ""
Write-Host "Danach kannst du normal nutzen:"
Write-Host "powershell -ExecutionPolicy Bypass -File .\fuelmind-nas.ps1 -Action start"
Write-Host "oder per Doppelklick auf fuelmind-nas.bat"
