[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path,
    [string]$RemoteUrl = "",
    [string]$Branch = "main",
    [string]$CommitMessage = "Initial commit",
    [switch]$Push
)

$ErrorActionPreference = "Stop"

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

if (-not (Test-Path -LiteralPath $RepositoryRoot)) {
    throw "RepositoryRoot nicht gefunden: $RepositoryRoot"
}

$resolvedRoot = (Resolve-Path -LiteralPath $RepositoryRoot).Path
Write-Host "Arbeite in: $resolvedRoot"

Push-Location $resolvedRoot
try {
    $gitVersion = git --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Git ist auf diesem Rechner nicht installiert oder nicht im PATH verfügbar."
    }

    Write-Host $gitVersion

    if (-not (Test-Path -LiteralPath (Join-Path $resolvedRoot ".git"))) {
        Write-Host "Initialisiere Git-Repository ..."
        Invoke-Git -Arguments @("init")
    }
    else {
        Write-Host "Git-Repository bereits vorhanden."
    }

    Write-Host "Setze Standard-Branch auf $Branch ..."
    Invoke-Git -Arguments @("branch", "-M", $Branch)

    if (-not [string]::IsNullOrWhiteSpace($RemoteUrl)) {
        $existingRemotes = @(git remote)
        if ($LASTEXITCODE -ne 0) {
            throw "Git-Remotes konnten nicht gelesen werden."
        }

        if ($existingRemotes -contains "origin") {
            $existingOrigin = git remote get-url origin
            if ($LASTEXITCODE -ne 0) {
                throw "origin konnte nicht gelesen werden."
            }

            if ($existingOrigin.Trim() -ne $RemoteUrl.Trim()) {
                Write-Host "Aktualisiere origin auf $RemoteUrl"
                Invoke-Git -Arguments @("remote", "set-url", "origin", $RemoteUrl)
            }
            else {
                Write-Host "origin ist bereits korrekt gesetzt."
            }
        }
        else {
            Write-Host "Lege origin an: $RemoteUrl"
            Invoke-Git -Arguments @("remote", "add", "origin", $RemoteUrl)
        }
    }
    else {
        Write-Host "Kein Remote angegeben. Ueberspringe origin-Konfiguration."
    }

    Write-Host "Fuege Dateien zum Commit hinzu ..."
    Invoke-Git -Arguments @("add", ".")

    $status = git status --porcelain
    if ($LASTEXITCODE -ne 0) {
        throw "Git-Status konnte nicht ermittelt werden."
    }

    if ([string]::IsNullOrWhiteSpace(($status | Out-String))) {
        Write-Host "Keine neuen Aenderungen zum Committen vorhanden."
    }
    else {
        Write-Host "Erstelle Commit: $CommitMessage"
        Invoke-Git -Arguments @("commit", "-m", $CommitMessage)
    }

    if ($Push) {
        if ([string]::IsNullOrWhiteSpace($RemoteUrl)) {
            throw "Fuer -Push musst du auch -RemoteUrl angeben."
        }
        Write-Host "Pushe nach origin/$Branch ..."
        Invoke-Git -Arguments @("push", "-u", "origin", $Branch)
    }

    Write-Host ""
    Write-Host "Fertig."
    Write-Host "Typische naechste Befehle:"
    Write-Host "git status"
    if (-not [string]::IsNullOrWhiteSpace($RemoteUrl) -and -not $Push) {
        Write-Host "git push -u origin $Branch"
    }
}
finally {
    Pop-Location
}
