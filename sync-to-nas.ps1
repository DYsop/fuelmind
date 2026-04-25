[CmdletBinding()]
param(
    [string]$SourcePath = $(if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }),
    [string]$DestinationPath = "Z:\docker\fuelmind",
    [switch]$CreateDestination,
    [switch]$IncludeEnvFile
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Invoke-RobocopySafe {
    param(
        [string]$From,
        [string]$To
    )

    $arguments = @(
        $From,
        $To,
        "/E",
        "/R:2",
        "/W:1",
        "/NFL",
        "/NDL",
        "/NP",
        "/XD", "node_modules", "dist", ".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", ".vite", "htmlcov", ".venv"
    )

    & robocopy @arguments | Out-Null
    $exitCode = $LASTEXITCODE

    if ($exitCode -gt 7) {
        throw "Robocopy-Fehler beim Kopieren von '$From' nach '$To' (ExitCode $exitCode)."
    }
}

if (-not (Test-Path -LiteralPath $SourcePath)) {
    throw "Quellpfad nicht gefunden: $SourcePath"
}

if (-not (Test-Path -LiteralPath $DestinationPath)) {
    if ($CreateDestination) {
        Write-Step "Zielpfad wird erstellt: $DestinationPath"
        New-Item -ItemType Directory -Path $DestinationPath -Force | Out-Null
    }
    else {
        throw "Zielpfad nicht gefunden: $DestinationPath`nNutze -CreateDestination, wenn der Ordner automatisch angelegt werden soll."
    }
}

$excludedRootFiles = @(
    "sync-to-nas.ps1",
    ".env"
)

if ($IncludeEnvFile) {
    $excludedRootFiles = $excludedRootFiles | Where-Object { $_ -ne ".env" }
}

Write-Step "Synchronisiere FuelMind nach $DestinationPath"

$rootItems = Get-ChildItem -LiteralPath $SourcePath -Force
foreach ($item in $rootItems) {
    if ($excludedRootFiles -contains $item.Name) {
        continue
    }

    $target = Join-Path $DestinationPath $item.Name

    if ($item.PSIsContainer) {
        Write-Step "Ordner: $($item.Name)"
        Invoke-RobocopySafe -From $item.FullName -To $target
    }
    else {
        Write-Step "Datei: $($item.Name)"
        Copy-Item -LiteralPath $item.FullName -Destination $target -Force
    }
}

Write-Step "Synchronisation abgeschlossen."
Write-Host "Quelle:      $SourcePath"
Write-Host "Ziel:        $DestinationPath"
Write-Host ""
if (-not $IncludeEnvFile) {
    Write-Host "Hinweis: .env wurde absichtlich NICHT kopiert." -ForegroundColor Yellow
    Write-Host "Falls du sie bewusst mitsynchronisieren willst:" -ForegroundColor Yellow
    Write-Host "  powershell -ExecutionPolicy Bypass -File .\sync-to-nas.ps1 -IncludeEnvFile"
    Write-Host ""
}
Write-Host "Danach auf dem NAS bei Bedarf neu bauen mit:" -ForegroundColor Green
Write-Host "  fuelmind rebuild"
