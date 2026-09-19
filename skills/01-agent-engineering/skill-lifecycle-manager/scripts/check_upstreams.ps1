[CmdletBinding()]
param(
    [ValidateSet("Auto", "Repo", "Local")]
    [string]$Mode = "Auto",

    [ValidateSet("Auto", "Codex", "ClaudeCode", "All")]
    [string]$Runtime = "Auto",

    [string]$RepoRoot,
    [string]$IndexPath,
    [string[]]$SkillRoots,
    [string[]]$ProjectRoots,
    [string]$WorkDir,
    [string]$BackupRoot,
    [switch]$SelfTest,
    [switch]$BootstrapIndex,
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
$indexPathWasExplicit = -not [string]::IsNullOrWhiteSpace($IndexPath)
$backupRootWasExplicit = -not [string]::IsNullOrWhiteSpace($BackupRoot)

if (-not $RepoRoot) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
}
if (-not (Test-Path -LiteralPath $RepoRoot)) {
    throw "Repository root does not exist: $RepoRoot"
}
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
if (-not $IndexPath) {
    $IndexPath = Join-Path $RepoRoot "_meta\skill-upstreams.json"
}
if (-not $WorkDir) {
    $WorkDir = Join-Path $env:TEMP "skill-upstream-audit"
}
if (-not $BackupRoot) {
    $BackupRoot = Join-Path $RepoRoot ".backups\skill-upstream-audit"
}
if ($Mode -eq "Auto") {
    if (Test-Path $IndexPath) { $Mode = "Repo" } else { $Mode = "Local" }
}
if ($Mode -eq "Local" -and -not $indexPathWasExplicit) {
    $homeDir = [Environment]::GetFolderPath("UserProfile")
    $portableIndex = Join-Path $homeDir ".skill-lifecycle\skill-upstreams.json"
    $legacyIndex = Join-Path $homeDir ".agents\skill-upstreams.json"
    $IndexPath = if (Test-Path -LiteralPath $portableIndex) {
        $portableIndex
    } elseif (Test-Path -LiteralPath $legacyIndex) {
        $legacyIndex
    } else {
        $portableIndex
    }
}
if ($Mode -eq "Local" -and -not $backupRootWasExplicit) {
    $BackupRoot = Join-Path ([Environment]::GetFolderPath("UserProfile")) ".skill-lifecycle\backups\skill-upstream-audit"
}

New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)][string[]]$GitArgs,
        [switch]$AllowFailure
    )

    $oldErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & git @GitArgs 2>&1
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $oldErrorActionPreference
    }
    if ($code -ne 0 -and -not $AllowFailure) {
        throw "git $($GitArgs -join ' ') failed: $($output -join "`n")"
    }
    return [pscustomobject]@{
        Code = $code
        Text = (($output | ForEach-Object { "$_" }) -join "`n").Trim()
    }
}

function Get-RepoSlug([string]$Url) {
    $u = $Url.TrimEnd("/")
    $u = $u -replace "^https://github.com/", ""
    $u = $u -replace "^git@github.com:", ""
    $u = $u -replace "\.git$", ""
    return ($u -replace "[^A-Za-z0-9_.-]+", "_")
}

function Update-UpstreamRepo([object]$Entry) {
    $url = $Entry.upstream.url
    if (-not $url) { return $null }

    $slug = Get-RepoSlug $url
    $target = Join-Path $WorkDir $slug
    $ref = $Entry.upstream.ref

    if (Test-Path (Join-Path $target ".git")) {
        $fetch = Invoke-Git -GitArgs @("-C", $target, "fetch", "--depth=1", "origin", $ref) -AllowFailure
        if ($fetch.Code -ne 0) {
            Invoke-Git -GitArgs @("-C", $target, "fetch", "--depth=1", "origin") | Out-Null
        }
        Invoke-Git -GitArgs @("-C", $target, "checkout", "--force", "FETCH_HEAD") | Out-Null
    } else {
        $clone = Invoke-Git -GitArgs @("clone", "--depth", "1", "--branch", $ref, $url, $target) -AllowFailure
        if ($clone.Code -ne 0) {
            Invoke-Git -GitArgs @("clone", "--depth", "1", $url, $target) | Out-Null
            Invoke-Git -GitArgs @("-C", $target, "fetch", "--depth=1", "origin", $ref) | Out-Null
            Invoke-Git -GitArgs @("-C", $target, "checkout", "--force", "FETCH_HEAD") | Out-Null
        }
    }

    return $target
}

function Get-NormalizedHashes([string]$Dir, [bool]$TrimTrailingWhitespace = $false) {
    $map = @{}
    if (-not (Test-Path $Dir)) { return $map }
    $resolvedDir = (Resolve-Path $Dir).Path
    Get-ChildItem -LiteralPath $Dir -Recurse -File -Force |
        Where-Object {
            $relForFilter = $_.FullName.Substring($resolvedDir.Length).TrimStart("\", "/")
            ($relForFilter -split '[\\/]') -notcontains ".git"
        } |
        ForEach-Object {
            $rel = $_.FullName.Substring($resolvedDir.Length).TrimStart("\", "/").Replace("\", "/")
            $bytes = [IO.File]::ReadAllBytes($_.FullName)
            $text = [Text.Encoding]::UTF8.GetString($bytes)
            $text = $text -replace "`r`n", "`n"
            if ($TrimTrailingWhitespace) {
                $text = $text -replace "[ `t]+(?=`n)", ""
                $text = $text -replace "(`n)+\z", "`n"
            }
            if ($text.Length -gt 0 -and $text[0] -eq [char]0xFEFF) { $text = $text.Substring(1) }
            $sha = [Security.Cryptography.SHA256]::Create()
            $hash = $sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($text))
            $map[$rel] = ([BitConverter]::ToString($hash)).Replace("-", "").ToLowerInvariant()
        }
    return $map
}

function Get-CanonicalPath([string]$Path) {
    return [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $Path).Path).TrimEnd("\", "/")
}

function Test-PathStrictlyUnderRoot([string]$Path, [string]$Root) {
    $resolvedPath = Get-CanonicalPath $Path
    $resolvedRoot = Get-CanonicalPath $Root
    $rootPrefix = $resolvedRoot + [IO.Path]::DirectorySeparatorChar
    return ($resolvedPath -ne $resolvedRoot -and
        $resolvedPath.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase))
}

function Assert-PathUnderRoot([string]$Path, [string]$Root) {
    $resolvedPath = Get-CanonicalPath $Path
    $resolvedRoot = Get-CanonicalPath $Root
    if (-not (Test-PathStrictlyUnderRoot -Path $resolvedPath -Root $resolvedRoot)) {
        throw "Refusing to modify path outside allowed root. Path=$resolvedPath Root=$resolvedRoot"
    }
}

function New-DirectoryBackup([string]$SourceDir, [string]$DestinationRoot, [string]$Label) {
    $resolvedSource = Get-CanonicalPath $SourceDir
    if (-not (Test-Path -LiteralPath $DestinationRoot)) {
        New-Item -ItemType Directory -Force -Path $DestinationRoot | Out-Null
    }
    $resolvedBackupRoot = Get-CanonicalPath $DestinationRoot
    $sourcePrefix = $resolvedSource + [IO.Path]::DirectorySeparatorChar
    if ($resolvedBackupRoot -eq $resolvedSource -or
        $resolvedBackupRoot.StartsWith($sourcePrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Backup root must not be inside the source directory. Source=$resolvedSource BackupRoot=$resolvedBackupRoot"
    }

    $safeLabel = ($Label -replace "[^A-Za-z0-9_.-]+", "-").Trim("-")
    if (-not $safeLabel) { $safeLabel = "skill" }
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss-fff"
    $backupPath = Join-Path $resolvedBackupRoot "$safeLabel-before-mirror-$timestamp"
    if (Test-Path -LiteralPath $backupPath) {
        throw "Backup path already exists: $backupPath"
    }

    New-Item -ItemType Directory -Path $backupPath | Out-Null
    Get-ChildItem -LiteralPath $resolvedSource -Force | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $backupPath -Recurse -Force
    }
    return $backupPath
}

function Sync-DirectoryMirror(
    [string]$SourceDir,
    [string]$TargetDir,
    [string]$AllowedRoot,
    [string]$BackupRoot,
    [string]$Label
) {
    Assert-PathUnderRoot -Path $TargetDir -Root $AllowedRoot
    if (-not (Test-Path $SourceDir)) { throw "Missing source directory: $SourceDir" }
    if (-not (Test-Path $TargetDir)) { New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null }

    $backupPath = New-DirectoryBackup -SourceDir $TargetDir -DestinationRoot $BackupRoot -Label $Label

    Get-ChildItem -LiteralPath $TargetDir -Force | ForEach-Object {
        Remove-Item -LiteralPath $_.FullName -Recurse -Force
    }
    Get-ChildItem -LiteralPath $SourceDir -Force | Where-Object { $_.Name -ne ".git" } | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $TargetDir -Recurse -Force
    }
    return $backupPath
}

function Invoke-RepoMode {
    if (-not (Test-Path $IndexPath)) {
        throw "Missing source index: $IndexPath"
    }

    $index = Get-Content $IndexPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $results = @()
    $today = Get-Date -Format "yyyy-MM-dd"

    foreach ($entry in @($index.sources)) {
        if ($entry.classification -ne "open-source") { continue }

        $localPath = Join-Path $RepoRoot ($entry.path -replace "/", "\")
        $result = [ordered]@{
            mode = "repo"
            name = $entry.name
            path = $entry.path
            updatePolicy = $entry.updatePolicy
            upstream = $entry.upstream.url
            upstreamPath = $entry.upstream.path
            status = "unknown"
            upstreamCommit = $null
            missingLocalFiles = 0
            extraLocalFiles = 0
            changedFiles = 0
            applied = $false
            backupPath = $null
        }

        if (-not (Test-Path $localPath)) {
            $result.status = "missing-local-path"
            $results += [pscustomobject]$result
            continue
        }

        try {
            Assert-PathUnderRoot -Path $localPath -Root $RepoRoot
        } catch {
            $result.status = "unsafe-local-path: $($_.Exception.Message)"
            $results += [pscustomobject]$result
            continue
        }

        try {
            $repoPath = Update-UpstreamRepo $entry
            if (-not $repoPath) {
                $result.status = "missing-upstream-url"
                $results += [pscustomobject]$result
                continue
            }

            $commit = (Invoke-Git -GitArgs @("-C", $repoPath, "rev-parse", "HEAD")).Text
            $result.upstreamCommit = $commit
            $upPath = Join-Path $repoPath ($entry.upstream.path -replace "/", "\")
            if (-not (Test-Path $upPath)) {
                $result.status = "missing-upstream-path"
                $results += [pscustomobject]$result
                continue
            }

            $trimTrailingWhitespace = $false
            if ($entry.PSObject.Properties["normalization"] -and
                $entry.normalization.PSObject.Properties["trimTrailingWhitespace"]) {
                $trimTrailingWhitespace = [bool]$entry.normalization.trimTrailingWhitespace
            }

            $local = Get-NormalizedHashes $localPath $trimTrailingWhitespace
            $up = Get-NormalizedHashes $upPath $trimTrailingWhitespace
            $localKeys = [System.Collections.Generic.HashSet[string]]::new([string[]]$local.Keys)
            $upKeys = [System.Collections.Generic.HashSet[string]]::new([string[]]$up.Keys)

            $missing = 0
            foreach ($k in $upKeys) { if (-not $localKeys.Contains($k)) { $missing++ } }
            $extra = 0
            foreach ($k in $localKeys) { if (-not $upKeys.Contains($k)) { $extra++ } }
            $changed = 0
            foreach ($k in $upKeys) {
                if ($localKeys.Contains($k) -and $local[$k] -ne $up[$k]) { $changed++ }
            }

            $result.missingLocalFiles = $missing
            $result.extraLocalFiles = $extra
            $result.changedFiles = $changed
            if (($missing + $extra + $changed) -eq 0) {
                $result.status = "current"
            } elseif ($entry.updatePolicy -eq "mapped") {
                $result.status = "mapped-drift"
            } else {
                $result.status = "drift"
            }

            if ($Apply -and $result.status -eq "drift" -and $entry.updatePolicy -eq "mirror") {
                $result.backupPath = Sync-DirectoryMirror `
                    -SourceDir $upPath `
                    -TargetDir $localPath `
                    -AllowedRoot $RepoRoot `
                    -BackupRoot $BackupRoot `
                    -Label $entry.name
                $result.status = "updated"
                $result.applied = $true
            }

            if ($entry.PSObject.Properties["lastChecked"]) {
                $entry.lastChecked.date = $today
                $entry.lastChecked.commit = $commit
            }
            if ($entry.PSObject.Properties["status"]) {
                $entry.status = $result.status
            }
        } catch {
            $result.status = "error: $($_.Exception.Message)"
        }

        $results += [pscustomobject]$result
    }

    if ($Apply) {
        $index.updated_at = $today
        $json = $index | ConvertTo-Json -Depth 12
        $enc = New-Object System.Text.UTF8Encoding($false)
        [IO.File]::WriteAllText($IndexPath, $json, $enc)
    }

    return [pscustomobject]@{
        mode = "repo"
        apply = [bool]$Apply
        indexPath = $IndexPath
        backupRoot = if ($Apply) { $BackupRoot } else { $null }
        results = $results
    }
}

function Invoke-SelfTest {
    $tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd("\", "/")
    $testBase = Join-Path $tempRoot ("skill-upstream-selftest-" + [guid]::NewGuid().ToString("N"))
    $allowedRoot = Join-Path $testBase "root"
    $child = Join-Path $allowedRoot "child"
    $sibling = Join-Path $testBase "root-escape"
    $backup = Join-Path $testBase "backups"
    $claudeConfig = Join-Path $testBase "claude-profile"
    $claudePersonalSkill = Join-Path $claudeConfig "skills\sample"
    $claudePluginSkill = Join-Path $claudeConfig "plugins\cache\market\1.0.0\skills\sample"
    $claudeProjectSkill = Join-Path $testBase "project\.claude\skills\sample"
    $oldClaudeConfigDir = $env:CLAUDE_CONFIG_DIR

    try {
        New-Item -ItemType Directory -Path $child -Force | Out-Null
        New-Item -ItemType Directory -Path $sibling -Force | Out-Null
        Set-Content -LiteralPath (Join-Path $child "sentinel.txt") -Value "backup-test" -Encoding UTF8
        New-Item -ItemType Directory -Path $claudePersonalSkill,$claudePluginSkill,$claudeProjectSkill -Force | Out-Null
        $env:CLAUDE_CONFIG_DIR = $claudeConfig

        Assert-PathUnderRoot -Path $child -Root $allowedRoot

        $rootRejected = $false
        try { Assert-PathUnderRoot -Path $allowedRoot -Root $allowedRoot } catch { $rootRejected = $true }
        if (-not $rootRejected) { throw "Root path was not rejected." }

        $siblingRejected = $false
        try { Assert-PathUnderRoot -Path $sibling -Root $allowedRoot } catch { $siblingRejected = $true }
        if (-not $siblingRejected) { throw "Sibling-prefix path was not rejected." }

        $backupPath = New-DirectoryBackup -SourceDir $child -DestinationRoot $backup -Label "selftest"
        if (-not (Test-Path -LiteralPath (Join-Path $backupPath "sentinel.txt"))) {
            throw "Backup did not preserve the sentinel file."
        }

        $personalInfo = Get-SkillRuntimeInfo $claudePersonalSkill
        $pluginInfo = Get-SkillRuntimeInfo $claudePluginSkill
        $projectInfo = Get-SkillRuntimeInfo $claudeProjectSkill
        if ($personalInfo.runtime -ne "claude-code" -or $personalInfo.scope -ne "personal") {
            throw "Claude Code personal skill classification failed."
        }
        if ($pluginInfo.scope -ne "plugin-cache-managed") {
            throw "Claude Code plugin cache classification failed."
        }
        if ($projectInfo.runtime -ne "claude-code" -or $projectInfo.scope -ne "project") {
            throw "Claude Code project skill classification failed."
        }

        return [pscustomobject]@{
            passed = $true
            childAccepted = $true
            rootRejected = $rootRejected
            siblingPrefixRejected = $siblingRejected
            backupCreated = $true
            claudePersonalClassified = $true
            claudeProjectClassified = $true
            claudePluginCacheExcluded = $true
        }
    } finally {
        $env:CLAUDE_CONFIG_DIR = $oldClaudeConfigDir
        $resolvedBase = if (Test-Path -LiteralPath $testBase) { Get-CanonicalPath $testBase } else { $null }
        $tempPrefix = $tempRoot + [IO.Path]::DirectorySeparatorChar
        if ($resolvedBase -and $resolvedBase.StartsWith($tempPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            Remove-Item -LiteralPath $resolvedBase -Recurse -Force
        }
    }
}

function Read-SkillName([string]$SkillFile) {
    $lines = Get-Content -LiteralPath $SkillFile -Encoding UTF8 -TotalCount 80
    foreach ($line in $lines) {
        if ($line -match '^\s*name\s*:\s*(.+?)\s*$') {
            return ($Matches[1].Trim().Trim('"').Trim("'"))
        }
    }
    return (Split-Path -Leaf (Split-Path -Parent $SkillFile))
}

function Find-GitRoot([string]$StartDir) {
    $dir = Get-Item -LiteralPath $StartDir
    while ($dir) {
        if (Test-Path (Join-Path $dir.FullName ".git")) { return $dir.FullName }
        $dir = $dir.Parent
    }
    return $null
}

function Get-GitHubUrls([string]$SkillFile) {
    $text = Get-Content -LiteralPath $SkillFile -Raw -Encoding UTF8
    $matches = [regex]::Matches($text, 'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_./?#=&%-]+)?')
    return @($matches | ForEach-Object { $_.Value.TrimEnd(".", ")", "]") } | Select-Object -Unique)
}

function Get-ClaudeConfigRoot {
    $homeDir = [Environment]::GetFolderPath("UserProfile")
    if ($env:CLAUDE_CONFIG_DIR) {
        return [IO.Path]::GetFullPath([Environment]::ExpandEnvironmentVariables($env:CLAUDE_CONFIG_DIR))
    }
    return (Join-Path $homeDir ".claude")
}

function Get-DefaultSkillRoots([string]$TargetRuntime, [string[]]$Projects) {
    $homeDir = [Environment]::GetFolderPath("UserProfile")
    $candidates = @()

    if ($TargetRuntime -in @("Auto", "Codex", "All")) {
        $candidates += Join-Path $homeDir ".codex\skills"
        $candidates += Join-Path $homeDir ".agents\skills"
    }
    if ($TargetRuntime -in @("Auto", "ClaudeCode", "All")) {
        $candidates += Join-Path (Get-ClaudeConfigRoot) "skills"
        foreach ($project in @($Projects)) {
            if (-not $project) { continue }
            $expanded = [Environment]::ExpandEnvironmentVariables($project)
            if (Test-Path -LiteralPath $expanded) {
                $candidates += Join-Path (Resolve-Path -LiteralPath $expanded).Path ".claude\skills"
            }
        }
        if (-not $Projects -or $Projects.Count -eq 0) {
            $gitRoot = (Invoke-Git -GitArgs @("-C", (Get-Location).Path, "rev-parse", "--show-toplevel") -AllowFailure).Text
            if ($gitRoot) { $candidates += Join-Path $gitRoot ".claude\skills" }
        }
    }

    return @($candidates | Where-Object { Test-Path -LiteralPath $_ } | ForEach-Object {
        (Resolve-Path -LiteralPath $_).Path
    } | Sort-Object -Unique)
}

function Get-SkillRuntimeInfo([string]$InstallPath) {
    $canonical = (Get-CanonicalPath $InstallPath).Replace("\", "/")
    $homeDir = [Environment]::GetFolderPath("UserProfile").Replace("\", "/").TrimEnd("/")
    $claudeConfig = ([IO.Path]::GetFullPath((Get-ClaudeConfigRoot))).Replace("\", "/").TrimEnd("/")

    if ($canonical.StartsWith("$claudeConfig/plugins/cache/", [StringComparison]::OrdinalIgnoreCase)) {
        return [pscustomobject]@{ runtime = "claude-code"; scope = "plugin-cache-managed" }
    }
    if ($canonical.StartsWith("$claudeConfig/skills/", [StringComparison]::OrdinalIgnoreCase)) {
        return [pscustomobject]@{ runtime = "claude-code"; scope = "personal" }
    }
    if ($canonical -match '/\.claude/skills/') {
        return [pscustomobject]@{ runtime = "claude-code"; scope = "project" }
    }
    if ($canonical.StartsWith("$homeDir/.codex/skills/", [StringComparison]::OrdinalIgnoreCase)) {
        return [pscustomobject]@{ runtime = "codex"; scope = "user" }
    }
    if ($canonical.StartsWith("$homeDir/.agents/skills/", [StringComparison]::OrdinalIgnoreCase)) {
        return [pscustomobject]@{ runtime = "agent-skills"; scope = "user-shared" }
    }
    if ($canonical -match '/\.codex/skills/') {
        return [pscustomobject]@{ runtime = "codex"; scope = "project" }
    }
    return [pscustomobject]@{ runtime = "unknown"; scope = "custom-root" }
}

function Get-ClaudePluginInventory([string]$TargetRuntime) {
    if ($TargetRuntime -notin @("Auto", "ClaudeCode", "All")) {
        return [pscustomobject]@{ status = "not-requested"; plugins = @(); cacheManaged = $true }
    }
    $claudeCommand = Get-Command claude -ErrorAction SilentlyContinue
    if (-not $claudeCommand) {
        return [pscustomobject]@{ status = "claude-cli-unavailable"; plugins = @(); cacheManaged = $true }
    }

    $oldErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & claude plugin list --json 2>&1
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $oldErrorActionPreference
    }
    if ($code -ne 0) {
        return [pscustomobject]@{
            status = "plugin-list-error"
            plugins = @()
            cacheManaged = $true
            error = (($output | ForEach-Object { "$_" }) -join "`n").Trim()
        }
    }
    try {
        $plugins = @(($output -join "`n") | ConvertFrom-Json)
        return [pscustomobject]@{ status = "inventoried"; plugins = $plugins; cacheManaged = $true }
    } catch {
        return [pscustomobject]@{ status = "plugin-list-invalid-json"; plugins = @(); cacheManaged = $true; error = $_.Exception.Message }
    }
}

function Get-InstalledSkillFiles([string[]]$Roots) {
    $files = @()
    foreach ($root in $Roots) {
        if (-not (Test-Path -LiteralPath $root)) { continue }
        $resolvedRoot = (Resolve-Path -LiteralPath $root).Path
        $rootSkill = Join-Path $resolvedRoot "SKILL.md"
        if (Test-Path -LiteralPath $rootSkill) {
            $files += Get-Item -LiteralPath $rootSkill
        }
        Get-ChildItem -LiteralPath $resolvedRoot -Directory -Force | ForEach-Object {
            $skillFile = Join-Path $_.FullName "SKILL.md"
            if (Test-Path -LiteralPath $skillFile) {
                $files += Get-Item -LiteralPath $skillFile
            }
        }
    }
    return @($files | Sort-Object FullName -Unique)
}

function Read-SourceIndex([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    $index = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $index.PSObject.Properties["sources"]) {
        throw "Source index has no sources array: $Path"
    }
    return $index
}

function Write-SourceIndex([object]$Index, [string]$Path) {
    $parent = Split-Path -Parent $Path
    if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    $json = $Index | ConvertTo-Json -Depth 12
    $enc = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($Path, $json, $enc)
}

function Get-GitHubRepositoryUrl([string]$Url) {
    if (-not $Url) { return $null }
    $match = [regex]::Match($Url, '^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)')
    if (-not $match.Success) { return $null }
    $repo = $match.Groups[2].Value -replace '\.git$', ''
    return "https://github.com/$($match.Groups[1].Value)/$repo"
}

function Find-LocalSourceEntry([object]$Index, [string]$InstallPath) {
    if (-not $Index) { return $null }
    $canonicalInstall = Get-CanonicalPath $InstallPath
    foreach ($entry in @($Index.sources)) {
        if (-not $entry.PSObject.Properties["install"] -or
            -not $entry.install.PSObject.Properties["path"] -or
            -not $entry.install.path) { continue }
        try {
            $candidate = [IO.Path]::GetFullPath([Environment]::ExpandEnvironmentVariables($entry.install.path)).TrimEnd("\", "/")
            if ($candidate -eq $canonicalInstall) { return $entry }
        } catch {
            continue
        }
    }
    return $null
}

function Find-ContainingSkillRoot([string]$InstallPath, [string[]]$Roots) {
    foreach ($root in $Roots) {
        if (-not (Test-Path -LiteralPath $root)) { continue }
        if (Test-PathStrictlyUnderRoot -Path $InstallPath -Root $root) {
            return (Get-CanonicalPath $root)
        }
    }
    return $null
}

function New-LocalIndexEntry([object]$Skill) {
    $candidates = @()
    $evidence = @("Canonical installed path inventoried by skill-lifecycle-manager.")
    $verification = @()

    if ($Skill.gitRoot) {
        $remote = (Invoke-Git -GitArgs @("-C", $Skill.gitRoot, "remote", "get-url", "origin") -AllowFailure).Text
        $branch = (Invoke-Git -GitArgs @("-C", $Skill.gitRoot, "rev-parse", "--abbrev-ref", "HEAD") -AllowFailure).Text
        if ($remote) {
            $candidates += [pscustomobject]@{
                url = $remote
                path = $Skill.path.Substring($Skill.gitRoot.Length).TrimStart("\", "/").Replace("\", "/") + "/"
                ref = $branch
                signal = "containing-git-origin"
            }
            $evidence += "Containing Git repository origin observed; public/open-source status was not inferred."
        }
    }

    foreach ($url in @($Skill.embeddedGitHubUrls)) {
        $repoUrl = Get-GitHubRepositoryUrl $url
        if ($repoUrl -and -not (@($candidates | Where-Object { $_.url -eq $repoUrl }).Count)) {
            $candidates += [pscustomobject]@{
                url = $repoUrl
                path = $null
                ref = $null
                signal = "embedded-url"
            }
        }
    }
    if ($Skill.embeddedGitHubUrls.Count -gt 0) {
        $evidence += "GitHub URL found in SKILL.md; it may be a dependency or example, so it remains unverified."
    }

    $verification += "Inspect git origin, install receipts, junction targets, source metadata, README attribution, and adjacent source checkouts."
    $verification += "Search GitHub for the exact frontmatter name and distinctive SKILL.md phrases."
    $verification += "Verify the exact repository path and full directory before assigning open-source and an update policy."

    return [pscustomobject]@{
        name = $Skill.name
        install = [pscustomobject]@{
            path = (Get-CanonicalPath $Skill.path).Replace("\", "/")
            runtime = $Skill.runtime
            scope = $Skill.scope
        }
        classification = if ($candidates.Count -gt 0) { "candidate" } else { "unknown" }
        updatePolicy = "none"
        status = if ($candidates.Count -gt 0) { "source-discovery-required" } else { "source-unresolved" }
        candidates = $candidates
        evidence = $evidence
        verificationPath = $verification
        notes = "Bootstrap entry only; no automatic overwrite is permitted until provenance is verified."
    }
}

function Add-MissingLocalIndexEntries([object]$Index, [object[]]$Skills) {
    if (-not $Index) {
        $Index = [pscustomobject]@{
            schema_version = 1
            index_kind = "local-skill-upstreams"
            updated_at = (Get-Date -Format "yyyy-MM-dd")
            sources = @()
        }
    }
    $sources = @($Index.sources)
    foreach ($skill in $Skills) {
        if (-not (Find-LocalSourceEntry -Index $Index -InstallPath $skill.path)) {
            $sources += New-LocalIndexEntry $skill
            $Index.sources = $sources
        }
    }
    $Index | Add-Member -Force -NotePropertyName updated_at -NotePropertyValue (Get-Date -Format "yyyy-MM-dd")
    return $Index
}

function Compare-MappedStandalone([object]$Skill, [object]$Entry, [string[]]$Roots) {
    $result = [ordered]@{
        name = $Skill.name
        path = $Skill.path
        runtime = $Skill.runtime
        scope = $Skill.scope
        indexClassification = $Entry.classification
        updatePolicy = $Entry.updatePolicy
        upstream = $null
        upstreamPath = $null
        upstreamCommit = $null
        status = "unverified-mapping"
        missingLocalFiles = 0
        extraLocalFiles = 0
        changedFiles = 0
        applied = $false
        backupPath = $null
    }

    if ($Entry.classification -ne "open-source" -or
        -not $Entry.PSObject.Properties["upstream"] -or
        -not $Entry.upstream.url -or
        -not $Entry.upstream.path -or
        -not $Entry.upstream.ref) {
        if ($Entry.classification -eq "self") { $result.status = "self-maintained" }
        elseif ($Entry.classification -eq "local") { $result.status = "local-no-external-upstream" }
        return [pscustomobject]$result
    }

    $result.upstream = $Entry.upstream.url
    $result.upstreamPath = $Entry.upstream.path
    try {
        $repoPath = Update-UpstreamRepo $Entry
        $commit = (Invoke-Git -GitArgs @("-C", $repoPath, "rev-parse", "HEAD")).Text
        $result.upstreamCommit = $commit
        $upPath = Join-Path $repoPath ($Entry.upstream.path -replace "/", "\")
        if (-not (Test-Path -LiteralPath $upPath)) {
            $result.status = "missing-upstream-path"
            return [pscustomobject]$result
        }

        $trimTrailingWhitespace = $false
        if ($Entry.PSObject.Properties["normalization"] -and
            $Entry.normalization.PSObject.Properties["trimTrailingWhitespace"]) {
            $trimTrailingWhitespace = [bool]$Entry.normalization.trimTrailingWhitespace
        }
        $local = Get-NormalizedHashes $Skill.path $trimTrailingWhitespace
        $up = Get-NormalizedHashes $upPath $trimTrailingWhitespace
        $localKeys = [System.Collections.Generic.HashSet[string]]::new([string[]]$local.Keys)
        $upKeys = [System.Collections.Generic.HashSet[string]]::new([string[]]$up.Keys)
        foreach ($key in $upKeys) {
            if (-not $localKeys.Contains($key)) { $result.missingLocalFiles++ }
            elseif ($local[$key] -ne $up[$key]) { $result.changedFiles++ }
        }
        foreach ($key in $localKeys) {
            if (-not $upKeys.Contains($key)) { $result.extraLocalFiles++ }
        }

        if (($result.missingLocalFiles + $result.extraLocalFiles + $result.changedFiles) -eq 0) {
            $result.status = "current"
        } elseif ($Entry.updatePolicy -eq "mapped") {
            $result.status = "mapped-drift"
        } else {
            $result.status = "drift"
        }

        if ($Apply -and $result.status -eq "drift" -and $Entry.updatePolicy -eq "mirror") {
            $allowedRoot = Find-ContainingSkillRoot -InstallPath $Skill.path -Roots $Roots
            if (-not $allowedRoot) { throw "Installed path is not below an audited skill root." }
            $result.backupPath = Sync-DirectoryMirror `
                -SourceDir $upPath `
                -TargetDir $Skill.path `
                -AllowedRoot $allowedRoot `
                -BackupRoot $BackupRoot `
                -Label $Entry.name
            $result.status = "updated"
            $result.applied = $true
        }

        if ($Apply) {
            if (-not $Entry.PSObject.Properties["lastChecked"]) {
                $Entry | Add-Member -NotePropertyName lastChecked -NotePropertyValue ([pscustomobject]@{})
            }
            $Entry.lastChecked | Add-Member -Force -NotePropertyName date -NotePropertyValue (Get-Date -Format "yyyy-MM-dd")
            $Entry.lastChecked | Add-Member -Force -NotePropertyName commit -NotePropertyValue $commit
            $Entry | Add-Member -Force -NotePropertyName status -NotePropertyValue $result.status
        }
    } catch {
        $result.status = "error: $($_.Exception.Message)"
    }
    return [pscustomobject]$result
}

function Invoke-LocalMode {
    if (-not $SkillRoots -or $SkillRoots.Count -eq 0) {
        $SkillRoots = Get-DefaultSkillRoots -TargetRuntime $Runtime -Projects $ProjectRoots
    }
    if (-not $SkillRoots -or $SkillRoots.Count -eq 0) {
        if ($Runtime -in @("Auto", "ClaudeCode", "All")) {
            $SkillRoots = @()
        } else {
            throw "No skill roots found. Pass -SkillRoots explicitly."
        }
    }

    $skillFiles = Get-InstalledSkillFiles $SkillRoots

    $skills = @()
    foreach ($file in $skillFiles) {
        $dir = Split-Path -Parent $file.FullName
        $gitRoot = Find-GitRoot $dir
        $runtimeInfo = Get-SkillRuntimeInfo $dir
        $skills += [pscustomobject]@{
            name = Read-SkillName $file.FullName
            path = $dir
            skillFile = $file.FullName
            gitRoot = $gitRoot
            embeddedGitHubUrls = Get-GitHubUrls $file.FullName
            runtime = $runtimeInfo.runtime
            scope = $runtimeInfo.scope
        }
    }

    $managedInstallExclusions = @($skills | Where-Object { $_.scope -eq "plugin-cache-managed" })
    $skills = @($skills | Where-Object { $_.scope -ne "plugin-cache-managed" })

    $sourceIndex = Read-SourceIndex $IndexPath
    $sourceIndexInitiallyPresent = $null -ne $sourceIndex
    if ($BootstrapIndex) {
        if ($sourceIndex -and
            ((-not $sourceIndex.PSObject.Properties["index_kind"]) -or
             $sourceIndex.index_kind -ne "local-skill-upstreams")) {
            throw "Refusing to bootstrap into a non-local source index: $IndexPath"
        }
        $sourceIndex = Add-MissingLocalIndexEntries -Index $sourceIndex -Skills $skills
        Write-SourceIndex -Index $sourceIndex -Path $IndexPath
    }

    $repoResults = @()
    $gitRoots = @($skills | Where-Object { $_.gitRoot } | Select-Object -ExpandProperty gitRoot -Unique)
    foreach ($gitRoot in $gitRoots) {
        $repoSkills = @($skills | Where-Object { $_.gitRoot -eq $gitRoot } | Select-Object -ExpandProperty name)
        $remote = (Invoke-Git -GitArgs @("-C", $gitRoot, "remote", "get-url", "origin") -AllowFailure).Text
        $branch = (Invoke-Git -GitArgs @("-C", $gitRoot, "rev-parse", "--abbrev-ref", "HEAD") -AllowFailure).Text
        $head = (Invoke-Git -GitArgs @("-C", $gitRoot, "rev-parse", "HEAD") -AllowFailure).Text
        $dirty = (Invoke-Git -GitArgs @("-C", $gitRoot, "status", "--short") -AllowFailure).Text
        $upstream = (Invoke-Git -GitArgs @("-C", $gitRoot, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}") -AllowFailure).Text
        if (-not $upstream -and $branch) { $upstream = "origin/$branch" }

        $status = "unknown"
        $behind = $null
        $newHead = $head
        $applied = $false
        try {
            if ($remote) { Invoke-Git -GitArgs @("-C", $gitRoot, "fetch", "origin", "--prune") | Out-Null }
            if ($upstream) {
                $behindText = (Invoke-Git -GitArgs @("-C", $gitRoot, "rev-list", "--count", "$head..$upstream") -AllowFailure).Text
                if ($behindText -match '^\d+$') { $behind = [int]$behindText }
            }

            if (-not $remote) {
                $status = "missing-origin-remote"
            } elseif ($dirty) {
                $status = "dirty-worktree"
            } elseif ($behind -gt 0) {
                $status = "behind"
                if ($Apply) {
                    Invoke-Git -GitArgs @("-C", $gitRoot, "pull", "--ff-only") | Out-Null
                    $newHead = (Invoke-Git -GitArgs @("-C", $gitRoot, "rev-parse", "HEAD")).Text
                    $status = "updated"
                    $applied = $true
                }
            } else {
                $status = "current"
            }
        } catch {
            $status = "error: $($_.Exception.Message)"
        }

        $repoResults += [pscustomobject]@{
            gitRoot = $gitRoot
            remote = $remote
            branch = $branch
            upstream = $upstream
            head = $head
            newHead = $newHead
            behind = $behind
            status = $status
            applied = $applied
            skills = $repoSkills
        }
    }

    $standaloneInventory = @($skills | Where-Object { -not $_.gitRoot })
    $standalone = @()
    $mappedStandalone = @()
    $discoveryQueue = @()
    foreach ($skill in $standaloneInventory) {
        $entry = Find-LocalSourceEntry -Index $sourceIndex -InstallPath $skill.path
        if ($entry) {
            $mappedResult = Compare-MappedStandalone -Skill $skill -Entry $entry -Roots $SkillRoots
            $mappedStandalone += $mappedResult
            if ($mappedResult.status -eq "unverified-mapping") {
                $discoveryQueue += [pscustomobject]@{
                    name = $skill.name
                    path = $skill.path
                    runtime = $skill.runtime
                    scope = $skill.scope
                    classification = $entry.classification
                    candidates = if ($entry.PSObject.Properties["candidates"]) { $entry.candidates } else { @() }
                    verificationPath = if ($entry.PSObject.Properties["verificationPath"]) { $entry.verificationPath } else { @() }
                }
            }
            continue
        }

        $status = if ($skill.embeddedGitHubUrls.Count -gt 0) { "candidate-url-found" } else { "local-or-unknown" }
        $standalone += [pscustomobject]@{
            name = $skill.name
            path = $skill.path
            runtime = $skill.runtime
            scope = $skill.scope
            status = $status
            embeddedGitHubUrls = $skill.embeddedGitHubUrls
            verificationPath = if ($skill.embeddedGitHubUrls.Count -gt 0) {
                "Bootstrap the source index, then verify the exact repository/path before overwriting."
            } else {
                "Bootstrap the source index, then search exact frontmatter name and distinctive SKILL.md phrases."
            }
        }
        $discoveryQueue += [pscustomobject]@{
            name = $skill.name
            path = $skill.path
            runtime = $skill.runtime
            scope = $skill.scope
            classification = "unmapped"
            candidates = @($skill.embeddedGitHubUrls)
            verificationPath = $standalone[-1].verificationPath
        }
    }

    if ($Apply -and $sourceIndex) {
        $sourceIndex | Add-Member -Force -NotePropertyName updated_at -NotePropertyValue (Get-Date -Format "yyyy-MM-dd")
        Write-SourceIndex -Index $sourceIndex -Path $IndexPath
    }

    $mappedCount = @($mappedStandalone).Count
    $verifiedMappedCount = @($mappedStandalone | Where-Object { $_.upstreamCommit }).Count
    $claudePlugins = Get-ClaudePluginInventory $Runtime

    return [pscustomobject]@{
        mode = "local"
        runtime = $Runtime
        apply = [bool]$Apply
        bootstrapIndex = [bool]$BootstrapIndex
        sourceIndexPath = $IndexPath
        sourceIndexInitiallyPresent = $sourceIndexInitiallyPresent
        sourceIndexPresent = $null -ne $sourceIndex
        skillRoots = $SkillRoots
        projectRoots = @($ProjectRoots)
        skillCount = @($skills).Count
        gitRepositoryCount = @($repoResults).Count
        standaloneCount = @($standaloneInventory).Count
        gitRepositories = $repoResults
        mappedStandaloneSkills = $mappedStandalone
        standaloneSkills = $standalone
        claudePlugins = $claudePlugins
        managedPluginCachePolicy = "excluded-from-standalone-mirror"
        managedPluginCacheSkillsExcluded = $managedInstallExclusions
        sourceIndexCoverage = [pscustomobject]@{
            exactPathMappings = $mappedCount
            verifiedMappingsCompared = $verifiedMappedCount
            discoveryRequired = @($discoveryQueue).Count
        }
        sourceDiscoveryQueue = $discoveryQueue
    }
}

if ($SelfTest) {
    Invoke-SelfTest | ConvertTo-Json -Depth 10
} elseif ($Mode -eq "Repo") {
    Invoke-RepoMode | ConvertTo-Json -Depth 10
} else {
    Invoke-LocalMode | ConvertTo-Json -Depth 10
}
