[CmdletBinding()]
param(
    [string]$ProjectRoot = $(if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }),
    [switch]$Stage,
    [switch]$Commit,
    [switch]$Push,
    [string]$CommitMessage = "Update screenshots"
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Get-ScreenshotMarkdown {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FolderPath,
        [Parameter(Mandatory = $true)]
        [string]$RelativePrefix
    )

    if (-not (Test-Path -LiteralPath $FolderPath)) {
        return @()
    }

    $files = Get-ChildItem -LiteralPath $FolderPath -File |
        Where-Object { $_.Extension -match '^\.(png|jpg|jpeg|webp)$' } |
        Sort-Object Name

    $lines = @()
    foreach ($file in $files) {
        $label = [System.IO.Path]::GetFileNameWithoutExtension($file.Name) -replace '[_-]+', ' '
        $relativePath = "$RelativePrefix/$($file.Name)" -replace '\\', '/'
        $lines += "![${label}](${relativePath})"
    }

    return $lines
}

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & git @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Git-Befehl fehlgeschlagen: git $($Arguments -join ' ')"
    }
}

$readmePath = Join-Path $ProjectRoot "README.md"
$desktopPath = Join-Path $ProjectRoot "docs\images\screenshots\desktop"
$mobilePath = Join-Path $ProjectRoot "docs\images\screenshots\mobile"

if (-not (Test-Path -LiteralPath $readmePath)) {
    throw "README.md nicht gefunden: $readmePath"
}

$desktopLines = Get-ScreenshotMarkdown -FolderPath $desktopPath -RelativePrefix "docs/images/screenshots/desktop"
$mobileLines = Get-ScreenshotMarkdown -FolderPath $mobilePath -RelativePrefix "docs/images/screenshots/mobile"

if (($desktopLines.Count + $mobileLines.Count) -eq 0) {
    throw "Keine Screenshot-Dateien gefunden unter docs/images/screenshots."
}

$generatedLines = @(
    "## Screenshots",
    "",
    "<!-- screenshots:start -->"
)

if ($desktopLines.Count -gt 0) {
    $generatedLines += ""
    $generatedLines += "### Desktop"
    $generatedLines += ""
    $generatedLines += $desktopLines
}

if ($mobileLines.Count -gt 0) {
    $generatedLines += ""
    $generatedLines += "### Mobile"
    $generatedLines += ""
    $generatedLines += $mobileLines
}

$generatedLines += ""
$generatedLines += "<!-- screenshots:end -->"

$generatedBlock = ($generatedLines -join [Environment]::NewLine)
$readmeContent = Get-Content -LiteralPath $readmePath -Raw

$pattern = '(?s)## Screenshots\s*.*?<!-- screenshots:end -->'
if ($readmeContent -match '<!-- screenshots:start -->' -and $readmeContent -match '<!-- screenshots:end -->') {
    $updatedReadme = [regex]::Replace($readmeContent, $pattern, $generatedBlock)
}
else {
    $trimmed = $readmeContent.TrimEnd()
    $updatedReadme = $trimmed + [Environment]::NewLine + [Environment]::NewLine + $generatedBlock + [Environment]::NewLine
}

Set-Content -LiteralPath $readmePath -Value $updatedReadme -Encoding UTF8

Write-Step "README-Screenshot-Sektion aktualisiert"
Write-Host "Desktop-Bilder: $($desktopLines.Count)"
Write-Host "Mobile-Bilder:  $($mobileLines.Count)"

if ($Stage -or $Commit -or $Push) {
    Write-Step "Stage README und Screenshot-Dateien"
    Invoke-Git -Arguments @("add", "README.md", "docs/images/screenshots")
}

if ($Commit -or $Push) {
    Write-Step "Erstelle Git-Commit"
    Invoke-Git -Arguments @("commit", "-m", $CommitMessage)
}

if ($Push) {
    Write-Step "Push nach GitHub"
    Invoke-Git -Arguments @("push")
}

Write-Host ""
Write-Host "Fertig. Screenshots sind jetzt korrekt in README.md eingetragen." -ForegroundColor Green
if (-not $Stage -and -not $Commit -and -not $Push) {
    Write-Host "Wenn du sie gleich fuer Git vorbereiten willst:" -ForegroundColor Yellow
    Write-Host "  powershell -ExecutionPolicy Bypass -File .\publish-screenshots.ps1 -Stage"
}
