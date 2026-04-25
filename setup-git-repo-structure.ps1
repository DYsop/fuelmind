[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path,
    [switch]$InitializeGit
)

$ErrorActionPreference = "Stop"

function Ensure-Directory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
        Write-Host "Ordner angelegt: $Path"
    }
    else {
        Write-Host "Ordner bereits vorhanden: $Path"
    }
}

function Ensure-File {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Content
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        Set-Content -LiteralPath $Path -Value $Content -Encoding UTF8
        Write-Host "Datei angelegt: $Path"
    }
    else {
        Write-Host "Datei bereits vorhanden: $Path"
    }
}

function Ensure-GitIgnoreEntries {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string[]]$Entries
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        Set-Content -LiteralPath $Path -Value "" -Encoding UTF8
        Write-Host ".gitignore angelegt: $Path"
    }

    $existing = Get-Content -LiteralPath $Path -ErrorAction Stop
    $changed = $false

    foreach ($entry in $Entries) {
        if ($existing -notcontains $entry) {
            Add-Content -LiteralPath $Path -Value $entry -Encoding UTF8
            Write-Host ".gitignore erweitert: $entry"
            $changed = $true
        }
    }

    if (-not $changed) {
        Write-Host ".gitignore war bereits vollständig."
    }
}

function Ensure-ReadmeSection {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ReadmePath
    )

    $section = @'
## Screenshots

![Dashboard](docs/images/screenshots/dashboard.png)
![Stationssuche](docs/images/screenshots/stationssuche.png)
![Preisalarm](docs/images/screenshots/preisalarm.png)
![Analyse](docs/images/screenshots/analyse.png)
'@

    if (-not (Test-Path -LiteralPath $ReadmePath)) {
        Set-Content -LiteralPath $ReadmePath -Value "# FuelMind`r`n`r`n$section`r`n" -Encoding UTF8
        Write-Host "README.md angelegt mit Screenshot-Sektion."
        return
    }

    $readme = Get-Content -LiteralPath $ReadmePath -Raw
    if ($readme -notmatch "(?m)^## Screenshots\s*$") {
        Add-Content -LiteralPath $ReadmePath -Value "`r`n$section`r`n" -Encoding UTF8
        Write-Host "Screenshot-Sektion in README.md ergänzt."
    }
    else {
        Write-Host "README.md enthält bereits eine Screenshot-Sektion."
    }
}

if (-not (Test-Path -LiteralPath $RepositoryRoot)) {
    throw "RepositoryRoot nicht gefunden: $RepositoryRoot"
}

$resolvedRoot = (Resolve-Path -LiteralPath $RepositoryRoot).Path
Write-Host "Arbeite in: $resolvedRoot"

$directories = @(
    $resolvedRoot,
    (Join-Path $resolvedRoot ".github"),
    (Join-Path $resolvedRoot ".github\ISSUE_TEMPLATE"),
    (Join-Path $resolvedRoot "docs"),
    (Join-Path $resolvedRoot "docs\images"),
    (Join-Path $resolvedRoot "docs\images\screenshots"),
    (Join-Path $resolvedRoot "docs\images\screenshots\desktop"),
    (Join-Path $resolvedRoot "docs\images\screenshots\mobile"),
    (Join-Path $resolvedRoot "docs\images\architecture"),
    (Join-Path $resolvedRoot "docs\images\branding"),
    (Join-Path $resolvedRoot "scripts")
)

foreach ($directory in $directories) {
    Ensure-Directory -Path $directory
}

$gitKeepContent = "# Platzhalterdatei, damit der Ordner im Git-Repo erhalten bleibt."
$gitKeepFiles = @(
    (Join-Path $resolvedRoot "docs\images\screenshots\desktop\.gitkeep"),
    (Join-Path $resolvedRoot "docs\images\screenshots\mobile\.gitkeep"),
    (Join-Path $resolvedRoot "docs\images\architecture\.gitkeep"),
    (Join-Path $resolvedRoot "docs\images\branding\.gitkeep")
)

foreach ($file in $gitKeepFiles) {
    Ensure-File -Path $file -Content $gitKeepContent
}

$readmeTemplate = @'
# FuelMind

Lokale Benzinpreis-App für dein NAS.

## Screenshots

![Dashboard](docs/images/screenshots/dashboard.png)
![Stationssuche](docs/images/screenshots/stationssuche.png)
![Preisalarm](docs/images/screenshots/preisalarm.png)
![Analyse](docs/images/screenshots/analyse.png)

## Entwicklung

- Kopiere keine echten API-Keys in dieses Repository.
- Verwende `.env.example` statt einer echten `.env`.
- Speichere nur neutrale Screenshots ohne sensible Daten.
'@

$issueTemplate = @'
---
name: Bug report
about: Fehler oder unerwartetes Verhalten melden
title: "[Bug] "
labels: bug
assignees: ""
---

## Beschreibung

## Schritte zur Reproduktion

## Erwartetes Verhalten

## Screenshots

## Umgebung
'@

$screenshotGuide = @'
# Screenshot-Guide

Lege hier Screenshots und Bilder für GitHub ab.

Empfohlene Dateien:

- `docs/images/screenshots/dashboard.png`
- `docs/images/screenshots/stationssuche.png`
- `docs/images/screenshots/preisalarm.png`
- `docs/images/screenshots/analyse.png`

Bitte keine sensiblen Daten zeigen:

- keine API-Keys
- keine Tokens oder Passwörter
- keine privaten IP-Adressen, falls nicht gewünscht
- keine privaten Adressen oder persönlichen Standorte
'@

Ensure-File -Path (Join-Path $resolvedRoot "docs\SCREENSHOTS.md") -Content $screenshotGuide
Ensure-File -Path (Join-Path $resolvedRoot ".github\ISSUE_TEMPLATE\bug_report.md") -Content $issueTemplate

$readmePath = Join-Path $resolvedRoot "README.md"
if (-not (Test-Path -LiteralPath $readmePath)) {
    Ensure-File -Path $readmePath -Content $readmeTemplate
}
else {
    Ensure-ReadmeSection -ReadmePath $readmePath
}

$gitIgnoreEntries = @(
    ".env",
    ".env.local",
    "node_modules/",
    "dist/",
    "__pycache__/",
    "*.pyc",
    ".DS_Store",
    "Thumbs.db"
)

Ensure-GitIgnoreEntries -Path (Join-Path $resolvedRoot ".gitignore") -Entries $gitIgnoreEntries

if ($InitializeGit) {
    $gitDir = Join-Path $resolvedRoot ".git"
    if (-not (Test-Path -LiteralPath $gitDir)) {
        Push-Location $resolvedRoot
        try {
            git init | Out-Null
            Write-Host "Git-Repository initialisiert."
        }
        finally {
            Pop-Location
        }
    }
    else {
        Write-Host "Git-Repository ist bereits initialisiert."
    }
}

Write-Host ""
Write-Host "Fertig. Angelegte Struktur:"
Write-Host "- docs/images/screenshots"
Write-Host "- docs/images/architecture"
Write-Host "- docs/images/branding"
Write-Host "- .github/ISSUE_TEMPLATE"
Write-Host "- README-Screenshot-Sektion"
Write-Host "- .gitignore-Einträge für sensible/lokale Dateien"
Write-Host ""
Write-Host "Nächste Schritte:"
Write-Host "1. Screenshots in docs/images/screenshots ablegen"
Write-Host "2. README prüfen"
Write-Host "3. Git committen und zu GitHub pushen"
