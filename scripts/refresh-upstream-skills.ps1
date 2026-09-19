[CmdletBinding()]
param(
    [switch]$Apply,
    [string]$WorkDir,
    [string]$ReportPath
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$indexPath = Join-Path $repoRoot "_meta\skill-upstreams.json"
$lifecycleScript = Join-Path $repoRoot "skills\01-agent-engineering\skill-lifecycle-manager\scripts\check_upstreams.ps1"

if (-not $WorkDir) {
    $scratchRoot = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { Join-Path $repoRoot ".runtime\cache" }
    $WorkDir = Join-Path $scratchRoot "skill-hub-upstream-refresh"
}
if (-not $ReportPath) {
    $ReportPath = Join-Path $WorkDir "upstream-refresh-report.json"
}

New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
$reportParent = Split-Path -Parent $ReportPath
if ($reportParent) { New-Item -ItemType Directory -Force -Path $reportParent | Out-Null }

if (-not (Test-Path -LiteralPath $indexPath)) { throw "Missing source index: $indexPath" }
if (-not (Test-Path -LiteralPath $lifecycleScript)) { throw "Missing lifecycle script: $lifecycleScript" }

$beforeJson = Get-Content -LiteralPath $indexPath -Raw -Encoding UTF8
$beforeIndex = $beforeJson | ConvertFrom-Json

$auditJson = (& $lifecycleScript -Mode Repo -RepoRoot $repoRoot -WorkDir (Join-Path $WorkDir "upstreams") | Out-String).Trim()
$audit = $auditJson | ConvertFrom-Json
$errors = @($audit.results | Where-Object { $_.status -like "error:*" -or $_.status -like "unsafe-*" })
if ($errors.Count -gt 0) {
    $details = ($errors | ForEach-Object { "$($_.name): $($_.status)" }) -join "`n"
    throw "Upstream audit failed:`n$details"
}

$mirrorDrift = @($audit.results | Where-Object { $_.updatePolicy -eq "mirror" -and $_.status -eq "drift" })
$mappedDrift = @($audit.results | Where-Object { $_.updatePolicy -eq "mapped" -and $_.status -eq "mapped-drift" })
$appliedNames = @()

if ($Apply -and $mirrorDrift.Count -gt 0) {
    $backupRoot = Join-Path $WorkDir "backups"
    $applyJson = (& $lifecycleScript -Mode Repo -RepoRoot $repoRoot -WorkDir (Join-Path $WorkDir "upstreams") -BackupRoot $backupRoot -Apply | Out-String).Trim()
    $applyResult = $applyJson | ConvertFrom-Json
    $applyErrors = @($applyResult.results | Where-Object { $_.status -like "error:*" -or $_.status -like "unsafe-*" })
    if ($applyErrors.Count -gt 0) {
        $details = ($applyErrors | ForEach-Object { "$($_.name): $($_.status)" }) -join "`n"
        throw "Upstream apply failed:`n$details"
    }
    $appliedNames = @($applyResult.results | Where-Object applied | ForEach-Object name)

    # Mapped Skills differ by design. A scheduled mirror refresh must not rewrite
    # their reviewed status or comparison commit without a human merge.
    $afterIndex = Get-Content -LiteralPath $indexPath -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($beforeEntry in @($beforeIndex.sources | Where-Object updatePolicy -eq "mapped")) {
        $afterEntry = $afterIndex.sources | Where-Object name -eq $beforeEntry.name | Select-Object -First 1
        if (-not $afterEntry) { continue }
        $afterEntry.status = $beforeEntry.status
        $afterEntry.lastChecked.date = $beforeEntry.lastChecked.date
        $afterEntry.lastChecked.commit = $beforeEntry.lastChecked.commit
    }
    $encoded = $afterIndex | ConvertTo-Json -Depth 12
    [IO.File]::WriteAllText($indexPath, $encoded + "`n", [Text.UTF8Encoding]::new($false))

    if (Test-Path -LiteralPath $backupRoot) {
        Remove-Item -LiteralPath $backupRoot -Recurse -Force
    }
}

$result = [ordered]@{
    generatedAt = (Get-Date).ToUniversalTime().ToString("o")
    apply = [bool]$Apply
    mirrorDriftCount = $mirrorDrift.Count
    appliedMirrorSkills = $appliedNames
    mappedReviewRequired = @($mappedDrift | ForEach-Object {
        [ordered]@{
            name = $_.name
            upstreamCommit = $_.upstreamCommit
            missingLocalFiles = $_.missingLocalFiles
            extraLocalFiles = $_.extraLocalFiles
            changedFiles = $_.changedFiles
        }
    })
    currentMirrorCount = @($audit.results | Where-Object { $_.updatePolicy -eq "mirror" -and $_.status -eq "current" }).Count
}

$resultJson = $result | ConvertTo-Json -Depth 8
[IO.File]::WriteAllText($ReportPath, $resultJson + "`n", [Text.UTF8Encoding]::new($false))
$resultJson
