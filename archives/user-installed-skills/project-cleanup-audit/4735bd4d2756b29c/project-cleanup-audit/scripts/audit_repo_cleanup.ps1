[CmdletBinding()]
param(
  [string]$Root = ".",
  [int]$Top = 25,
  [switch]$Json,
  [switch]$IncludeProcesses,
  [switch]$HashReleaseArtifacts
)

$ErrorActionPreference = "Stop"

function Invoke-GitLines {
  param([string[]]$GitArgs)
  $output = & git @GitArgs 2>$null
  if ($LASTEXITCODE -eq 0) {
    return @($output)
  }
  return @()
}

function Get-PathSizeBytes {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) {
    return 0
  }

  $item = Get-Item -LiteralPath $Path -Force
  if (-not $item.PSIsContainer) {
    return [int64]$item.Length
  }

  $sum = (Get-ChildItem -LiteralPath $Path -Recurse -Force -File -ErrorAction SilentlyContinue |
    Measure-Object -Property Length -Sum).Sum
  if ($null -eq $sum) {
    return 0
  }
  return [int64]$sum
}

function Convert-ToMB {
  param([int64]$Bytes)
  return [math]::Round(($Bytes / 1MB), 2)
}

function Get-RelativePathCompat {
  param([string]$BasePath, [string]$ChildPath)
  $base = (Resolve-Path -LiteralPath $BasePath).Path.TrimEnd("\", "/")
  $child = (Resolve-Path -LiteralPath $ChildPath).Path
  $prefix = $base + [System.IO.Path]::DirectorySeparatorChar
  if ($child.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    return $child.Substring($prefix.Length)
  }
  return $child
}

function Get-TopLevelSizes {
  param([string]$RootPath, [int]$Limit)
  $rows = @()
  foreach ($item in Get-ChildItem -LiteralPath $RootPath -Force -ErrorAction SilentlyContinue) {
    $bytes = Get-PathSizeBytes $item.FullName
    $rows += [pscustomobject]@{
      path = $item.Name
      type = if ($item.PSIsContainer) { "dir" } else { "file" }
      size_mb = Convert-ToMB $bytes
      last_write_time = $item.LastWriteTime.ToString("s")
    }
  }
  return @($rows | Sort-Object size_mb -Descending | Select-Object -First $Limit)
}

function Get-CandidateDirectories {
  param([string]$RootPath, [int]$Limit)
  $names = @(
    "node_modules", "target", "dist", "build", "out", ".next", ".nuxt",
    ".svelte-kit", ".turbo", ".vite", ".parcel-cache", "coverage",
    "diagnostics", "output", "logs", "tmp", "temp", ".worktrees",
    ".pytest_cache", ".mypy_cache", ".tox", ".venv", "venv", "__pycache__"
  )

  $rows = @()
  $dirs = Get-ChildItem -LiteralPath $RootPath -Directory -Force -Recurse -Depth 4 -ErrorAction SilentlyContinue
  foreach ($dir in $dirs) {
    $relative = Get-RelativePathCompat $RootPath $dir.FullName
    $normalized = $relative.Replace("\", "/")
    if ($normalized -eq ".git" -or $normalized.StartsWith(".git/")) {
      continue
    }
    if ($names -notcontains $dir.Name) {
      continue
    }
    $bytes = Get-PathSizeBytes $dir.FullName
    $rows += [pscustomobject]@{
      path = $relative
      size_mb = Convert-ToMB $bytes
      last_write_time = $dir.LastWriteTime.ToString("s")
    }
  }
  return @($rows | Sort-Object size_mb -Descending | Select-Object -First $Limit)
}

function Get-ExtensionSummary {
  param([object[]]$Files, [int]$Limit = 8)
  $rows = @()
  $groups = $Files | Group-Object Extension | Sort-Object Count -Descending | Select-Object -First $Limit
  foreach ($group in $groups) {
    $bytes = ($group.Group | Measure-Object -Property Length -Sum).Sum
    if ($null -eq $bytes) {
      $bytes = 0
    }
    $rows += [pscustomobject]@{
      extension = if ([string]::IsNullOrWhiteSpace($group.Name)) { "[none]" } else { $group.Name }
      count = $group.Count
      size_mb = Convert-ToMB ([int64]$bytes)
    }
  }
  return @($rows)
}

function Get-PathInventoryRow {
  param(
    [string]$RootPath,
    [string]$RelativePath,
    [switch]$HashFile
  )

  $fullPath = Join-Path $RootPath $RelativePath
  if (-not (Test-Path -LiteralPath $fullPath)) {
    return [pscustomobject]@{
      path = $RelativePath
      exists = $false
      type = $null
      file_count = 0
      dir_count = 0
      size_mb = 0
      last_write_time = $null
      sha256 = $null
      top_extensions = @()
    }
  }

  $item = Get-Item -LiteralPath $fullPath -Force
  $files = if ($item.PSIsContainer) {
    @(Get-ChildItem -LiteralPath $fullPath -Recurse -Force -File -ErrorAction SilentlyContinue)
  }
  else {
    @($item)
  }
  $dirs = if ($item.PSIsContainer) {
    @(Get-ChildItem -LiteralPath $fullPath -Recurse -Force -Directory -ErrorAction SilentlyContinue)
  }
  else {
    @()
  }
  $bytes = ($files | Measure-Object -Property Length -Sum).Sum
  if ($null -eq $bytes) {
    $bytes = 0
  }

  $sha256 = $null
  if ($HashFile -and -not $item.PSIsContainer) {
    $sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $fullPath).Hash
  }

  return [pscustomobject]@{
    path = $RelativePath
    exists = $true
    type = if ($item.PSIsContainer) { "dir" } else { "file" }
    file_count = $files.Count
    dir_count = $dirs.Count
    size_mb = Convert-ToMB ([int64]$bytes)
    last_write_time = $item.LastWriteTime.ToString("s")
    sha256 = $sha256
    top_extensions = @(Get-ExtensionSummary $files)
  }
}

function Get-LocalContextSummaries {
  param([string]$RootPath)
  $paths = @(".codex", ".codegraph", ".gstack", ".pytest_cache", ".venv", "__pycache__")
  $rows = @()
  foreach ($path in $paths) {
    $rows += Get-PathInventoryRow -RootPath $RootPath -RelativePath $path
  }
  return @($rows)
}

function Get-ReleaseArtifactSummaries {
  param([string]$RootPath, [switch]$HashArtifacts)

  $rows = @()
  $distPath = Join-Path $RootPath "dist"
  if (Test-Path -LiteralPath $distPath) {
    foreach ($item in Get-ChildItem -LiteralPath $distPath -Force -ErrorAction SilentlyContinue) {
      $relative = Get-RelativePathCompat $RootPath $item.FullName
      $shouldHash = $HashArtifacts -and -not $item.PSIsContainer -and $item.Extension -match '^\.(zip|exe|msi|dmg|pkg)$'
      $rows += Get-PathInventoryRow -RootPath $RootPath -RelativePath $relative -HashFile:$shouldHash
    }

    foreach ($releaseDir in Get-ChildItem -LiteralPath $distPath -Directory -Force -Filter "release-*" -ErrorAction SilentlyContinue) {
      foreach ($file in Get-ChildItem -LiteralPath $releaseDir.FullName -File -Force -ErrorAction SilentlyContinue) {
        $relative = Get-RelativePathCompat $RootPath $file.FullName
        $shouldHash = $HashArtifacts -and $file.Extension -match '^\.(zip|exe|msi|dmg|pkg)$'
        $rows += Get-PathInventoryRow -RootPath $RootPath -RelativePath $relative -HashFile:$shouldHash
      }
    }
  }

  foreach ($releaseDir in Get-ChildItem -LiteralPath $RootPath -Directory -Force -Filter "release-*" -ErrorAction SilentlyContinue) {
    $relative = Get-RelativePathCompat $RootPath $releaseDir.FullName
    $rows += Get-PathInventoryRow -RootPath $RootPath -RelativePath $relative
  }

  return @($rows)
}

function Get-LocalDataEvidenceSummaries {
  param([string]$RootPath, [object[]]$ReviewRequiredPaths)

  $rows = @()
  foreach ($entry in $ReviewRequiredPaths) {
    if ($entry.reasons -notcontains "local_data_or_validation_evidence") {
      continue
    }
    $rows += Get-PathInventoryRow -RootPath $RootPath -RelativePath $entry.path
  }
  return @($rows)
}

function Get-WorkspaceProcesses {
  param([string]$RootPath)
  $rootVariants = @(
    $RootPath,
    $RootPath.Replace("\", "/")
  ) | Select-Object -Unique

  $rows = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
      if (-not $_.CommandLine) {
        return $false
      }
      foreach ($variant in $rootVariants) {
        if ($_.CommandLine.IndexOf($variant, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
          return $true
        }
      }
      return $false
    } |
    Select-Object ProcessId, Name, CommandLine
  return @($rows)
}

function Convert-GitCleanLineToPath {
  param([string]$Line)
  $prefix = "Would remove "
  if (-not $Line -or -not $Line.StartsWith($prefix, [System.StringComparison]::Ordinal)) {
    return $null
  }
  return $Line.Substring($prefix.Length).TrimEnd("/", "\")
}

function Get-ReviewRequiredIgnoredPaths {
  param([string[]]$CleanLines)

  $rows = @()
  foreach ($line in $CleanLines) {
    $path = Convert-GitCleanLineToPath $line
    if (-not $path) {
      continue
    }

    $normalized = $path.Replace("\", "/").TrimEnd("/")
    $reasons = [System.Collections.Generic.List[string]]::new()

    if ($normalized -match '(^|/)\.(codex|codegraph|gstack|claude)($|/)') {
      $reasons.Add("agent_context")
    }
    if ($normalized -match '(^|/)(\.runtime|test_dataset|manual_(frontend|program)_runs|raw_documents|mailbox|truth|dataset|extracted_invoices)($|/|_)') {
      $reasons.Add("local_data_or_validation_evidence")
    }
    if ($normalized -match '(^|/)(dist|release[-_][^/]*|[^/]+\.(zip|exe|msi|dmg|pkg|app))($|/)') {
      $reasons.Add("release_artifact")
    }
    if ($normalized -match '(^|/)(\.env($|\.)|[^/]+\.(pem|key|crt|pfx|p12|kdbx))($|/)') {
      $reasons.Add("credential_or_secret_candidate")
    }

    if ($reasons.Count -gt 0) {
      $rows += [pscustomobject]@{
        path = $path
        reasons = @($reasons.ToArray())
      }
    }
  }

  return @($rows)
}

$rootPath = (Resolve-Path -LiteralPath $Root).Path
Push-Location $rootPath
try {
  $gitTop = @(Invoke-GitLines @("rev-parse", "--show-toplevel"))
  $isGit = $gitTop.Count -gt 0

  [string[]]$gitRemotes = @()
  [string[]]$gitStatus = @()
  [string[]]$gitWorktrees = @()
  [string[]]$ignoredCleanDryRun = @()
  [string[]]$untrackedCleanDryRun = @()
  if ($isGit) {
    $gitRemotes = [string[]]@(Invoke-GitLines @("remote", "-v"))
    $gitStatus = [string[]]@(Invoke-GitLines @("status", "--short"))
    $gitWorktrees = [string[]]@(Invoke-GitLines @("worktree", "list", "--porcelain"))
    $ignoredCleanDryRun = [string[]]@(Invoke-GitLines @("clean", "-ndX"))
    $untrackedCleanDryRun = [string[]]@(Invoke-GitLines @("clean", "-nd"))
  }
  [object[]]$reviewRequiredIgnoredPaths = @(Get-ReviewRequiredIgnoredPaths $ignoredCleanDryRun)
  [object[]]$workspaceProcesses = @()
  if ($IncludeProcesses) {
    $workspaceProcesses = [object[]]@(Get-WorkspaceProcesses $rootPath)
  }

  $git = [ordered]@{
    is_git = $isGit
    top_level = if ($isGit) { $gitTop[0] } else { $null }
    branch = if ($isGit) { (Invoke-GitLines @("branch", "--show-current") | Select-Object -First 1) } else { $null }
    head = if ($isGit) { (Invoke-GitLines @("log", "--oneline", "--decorate", "-1") | Select-Object -First 1) } else { $null }
    remotes = $gitRemotes
    status = $gitStatus
    worktrees = $gitWorktrees
    ignored_clean_dry_run = $ignoredCleanDryRun
    untracked_clean_dry_run = $untrackedCleanDryRun
    review_required_ignored_paths = $reviewRequiredIgnoredPaths
  }

  $report = [ordered]@{
    root = $rootPath
    generated_at = (Get-Date).ToString("s")
    git = $git
    top_level_sizes = @(Get-TopLevelSizes $rootPath $Top)
    cleanup_candidate_dirs = @(Get-CandidateDirectories $rootPath $Top)
    local_context_paths = @(Get-LocalContextSummaries $rootPath)
    release_artifacts = @(Get-ReleaseArtifactSummaries -RootPath $rootPath -HashArtifacts:$HashReleaseArtifacts)
    local_data_evidence_paths = @(Get-LocalDataEvidenceSummaries -RootPath $rootPath -ReviewRequiredPaths $reviewRequiredIgnoredPaths)
    workspace_processes = $workspaceProcesses
  }

  if ($Json) {
    $report | ConvertTo-Json -Depth 6
    return
  }

  Write-Output "# Project Cleanup Audit"
  Write-Output ""
  Write-Output "Root: $rootPath"
  Write-Output "Generated: $($report.generated_at)"
  Write-Output ""

  Write-Output "## Git"
  Write-Output "Is Git repo: $($git.is_git)"
  if ($git.is_git) {
    Write-Output "Top level: $($git.top_level)"
    Write-Output "Branch: $($git.branch)"
    Write-Output "HEAD: $($git.head)"
    Write-Output "Status entries: $($git.status.Count)"
    Write-Output "Ignored dry-run entries: $($git.ignored_clean_dry_run.Count)"
    Write-Output "Untracked dry-run entries: $($git.untracked_clean_dry_run.Count)"
    Write-Output "Remotes:"
    $git.remotes | ForEach-Object { Write-Output "  $_" }
  }
  Write-Output ""

  Write-Output "## Top-Level Sizes"
  $report.top_level_sizes | Format-Table -AutoSize | Out-String -Width 220 | Write-Output

  Write-Output "## Cleanup Candidate Directories"
  $report.cleanup_candidate_dirs | Format-Table -AutoSize | Out-String -Width 220 | Write-Output

  if ($git.is_git -and $git.review_required_ignored_paths.Count -gt 0) {
    Write-Output "## Review Required Ignored Paths"
    $git.review_required_ignored_paths |
      Select-Object path, @{Name = "reasons"; Expression = { $_.reasons -join "," } } |
      Format-Table -AutoSize |
      Out-String -Width 220 |
      Write-Output
  }

  Write-Output "## Local Context Paths"
  $report.local_context_paths |
    Select-Object path, exists, type, file_count, dir_count, size_mb, last_write_time |
    Format-Table -AutoSize |
    Out-String -Width 220 |
    Write-Output

  if ($report.release_artifacts.Count -gt 0) {
    Write-Output "## Release Artifact Summary"
    $report.release_artifacts |
      Select-Object path, type, file_count, dir_count, size_mb, last_write_time, sha256 |
      Format-Table -AutoSize |
      Out-String -Width 260 |
      Write-Output
  }

  if ($report.local_data_evidence_paths.Count -gt 0) {
    Write-Output "## Local Data Evidence Summary"
    $report.local_data_evidence_paths |
      Select-Object path, file_count, dir_count, size_mb, @{Name = "top_extensions"; Expression = { ($_.top_extensions | ForEach-Object { "$($_.extension):$($_.count)" }) -join ", " } } |
      Format-Table -AutoSize |
      Out-String -Width 260 |
      Write-Output
  }

  if ($git.is_git) {
    Write-Output "## Git Clean Dry Run: Ignored (-ndX)"
    Write-Output "Showing $([math]::Min($Top, $git.ignored_clean_dry_run.Count)) of $($git.ignored_clean_dry_run.Count)"
    $git.ignored_clean_dry_run | Select-Object -First $Top | ForEach-Object { Write-Output $_ }
    Write-Output ""
    Write-Output "## Git Clean Dry Run: Untracked (-nd)"
    Write-Output "Showing $([math]::Min($Top, $git.untracked_clean_dry_run.Count)) of $($git.untracked_clean_dry_run.Count)"
    $git.untracked_clean_dry_run | Select-Object -First $Top | ForEach-Object { Write-Output $_ }
    Write-Output ""
    Write-Output "## Worktrees"
    $git.worktrees | Select-Object -First ($Top * 4) | ForEach-Object { Write-Output $_ }
    Write-Output ""
  }

  if ($IncludeProcesses) {
    Write-Output "## Workspace Processes"
    $report.workspace_processes | Format-Table -AutoSize | Out-String -Width 220 | Write-Output
  }
}
finally {
  Pop-Location
}
