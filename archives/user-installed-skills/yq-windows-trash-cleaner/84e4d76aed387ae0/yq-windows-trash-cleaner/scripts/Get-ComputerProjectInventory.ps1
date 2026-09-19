[CmdletBinding()]
param(
    [string[]]$ScanRoot,
    [ValidateRange(1, 20)][int]$MaxDepth = 8,
    [ValidateRange(1, 12)][int]$CacheDepth = 6,
    [switch]$SkipCacheSizes,
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'

function Get-CanonicalPath {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    try { return (Resolve-Path -LiteralPath $LiteralPath -ErrorAction Stop).Path }
    catch { return $null }
}

function Test-IsReparsePoint {
    param([Parameter(Mandatory = $true)][System.IO.FileSystemInfo]$Item)
    return [bool]($Item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)
}

function Invoke-GitText {
    param([string]$Root, [string[]]$Arguments)
    if (-not (Get-Command git.exe -ErrorAction SilentlyContinue)) { return @() }
    try { return @(& git.exe -C $Root @Arguments 2>$null) }
    catch { return @() }
}

function Measure-Tree {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    $bytes = [int64]0
    $files = 0
    $dirs = 0
    $errors = New-Object System.Collections.Generic.List[string]
    $stack = New-Object System.Collections.Stack
    $stack.Push($LiteralPath)
    while ($stack.Count -gt 0) {
        $current = [string]$stack.Pop()
        try {
            foreach ($item in Get-ChildItem -LiteralPath $current -Force -ErrorAction Stop) {
                if (Test-IsReparsePoint -Item $item) { continue }
                if ($item.PSIsContainer) { $dirs++; $stack.Push($item.FullName) }
                else { $files++; $bytes += [int64]$item.Length }
            }
        }
        catch { $errors.Add("$current :: $($_.Exception.Message)") }
    }
    return [pscustomobject]@{ Bytes = $bytes; Files = $files; Directories = $dirs; Errors = @($errors | ForEach-Object { $_ }) }
}

function Get-DefaultRoots {
    $roots = New-Object System.Collections.Generic.List[string]
    $fixed = @(Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' -ErrorAction SilentlyContinue)
    $interesting = 'project|projects|repo|repos|src|source|workspace|workspaces|dev|code|coding|tmp'
    foreach ($disk in $fixed) {
        $driveRoot = "$($disk.DeviceID)\"
        try {
            foreach ($dir in Get-ChildItem -LiteralPath $driveRoot -Directory -Force -ErrorAction Stop) {
                if ($dir.Name -match $interesting) { $roots.Add($dir.FullName) }
            }
        }
        catch { }
    }
    foreach ($candidate in @(
        (Get-Location).Path,
        (Join-Path $env:USERPROFILE 'Documents'),
        (Join-Path $env:USERPROFILE 'Desktop'),
        (Join-Path $env:USERPROFILE 'source'),
        (Join-Path $env:USERPROFILE 'repos')
    )) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) { $roots.Add($candidate) }
    }
    return @($roots | ForEach-Object { $_ })
}

$requestedRoots = if ($ScanRoot -and $ScanRoot.Count -gt 0) { @($ScanRoot) } else { @(Get-DefaultRoots) }
$roots = New-Object System.Collections.Generic.List[string]
foreach ($root in $requestedRoots) {
    $resolved = Get-CanonicalPath -LiteralPath $root
    if ($resolved -and -not $roots.Contains($resolved)) { $roots.Add($resolved) }
}

$skipTraversal = @(
    '.git', '.svn', '.hg', 'node_modules', '.venv', 'venv', 'env', 'target', '.next', '.nuxt',
    '.cache', '.gradle', '.m2', '.cargo', '.rustup', '__pycache__', '.pytest_cache', '.mypy_cache',
    '.ruff_cache', '.tox', '.turbo', '.parcel-cache', 'site-packages', 'packages', 'AppData',
    '$Recycle.Bin', 'System Volume Information', 'Windows', 'Program Files', 'Program Files (x86)',
    'ProgramData', 'Recovery'
)
$manifestNames = @('package.json', 'pyproject.toml', 'Cargo.toml', 'go.mod', 'pom.xml', 'build.gradle', 'build.gradle.kts', 'composer.json')
$projectPaths = New-Object System.Collections.Generic.HashSet[string]([System.StringComparer]::OrdinalIgnoreCase)
$scanErrors = New-Object System.Collections.Generic.List[string]

foreach ($root in $roots) {
    $queue = New-Object System.Collections.Queue
    $queue.Enqueue([pscustomobject]@{ Path = $root; Depth = 0 })
    while ($queue.Count -gt 0) {
        $entry = $queue.Dequeue()
        $path = [string]$entry.Path
        $depth = [int]$entry.Depth
        try {
            $dir = Get-Item -LiteralPath $path -Force -ErrorAction Stop
            if (Test-IsReparsePoint -Item $dir) { continue }
            $isGit = Test-Path -LiteralPath (Join-Path $path '.git')
            $hasManifest = $false
            foreach ($manifest in $manifestNames) {
                if (Test-Path -LiteralPath (Join-Path $path $manifest)) { $hasManifest = $true; break }
            }
            if (-not $hasManifest) {
                $solution = Get-ChildItem -LiteralPath $path -File -Filter '*.sln' -ErrorAction SilentlyContinue | Select-Object -First 1
                $hasManifest = [bool]$solution
            }
            if ($isGit -or $hasManifest) { [void]$projectPaths.Add($path) }
            if ($depth -ge $MaxDepth) { continue }
            foreach ($child in Get-ChildItem -LiteralPath $path -Directory -Force -ErrorAction Stop) {
                if (Test-IsReparsePoint -Item $child) { continue }
                if ($skipTraversal -contains $child.Name) { continue }
                $queue.Enqueue([pscustomobject]@{ Path = $child.FullName; Depth = $depth + 1 })
            }
        }
        catch { $scanErrors.Add("$path :: $($_.Exception.Message)") }
    }
}

$processes = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessId -ne $PID -and ($_.CommandLine -or $_.ExecutablePath) })
$projects = New-Object System.Collections.Generic.List[object]
$canonicalProjects = New-Object System.Collections.Generic.HashSet[string]([System.StringComparer]::OrdinalIgnoreCase)
$cacheNames = @('node_modules', '.venv', 'venv', 'target', '.next', '.nuxt', '.pytest_cache', '.mypy_cache', '.ruff_cache', '__pycache__', '.tox', '.turbo', '.parcel-cache', 'playwright-report', 'test-results', '.codegraph', 'dist', 'build', 'output')

foreach ($projectPath in @($projectPaths | Sort-Object)) {
    $gitTop = (Invoke-GitText -Root $projectPath -Arguments @('rev-parse', '--show-toplevel') | Select-Object -First 1)
    $isGit = [bool]$gitTop
    $canonical = if ($isGit) { ($gitTop -replace '/', '\') } else { $projectPath }
    $canonical = Get-CanonicalPath -LiteralPath $canonical
    if (-not $canonical -or -not $canonicalProjects.Add($canonical)) { continue }
    $status = if ($isGit) { @(Invoke-GitText -Root $canonical -Arguments @('status', '--porcelain=v1', '--untracked-files=normal')) } else { @() }
    $branch = if ($isGit) { (Invoke-GitText -Root $canonical -Arguments @('branch', '--show-current') | Select-Object -First 1) } else { $null }
    $head = if ($isGit) { (Invoke-GitText -Root $canonical -Arguments @('rev-parse', 'HEAD') | Select-Object -First 1) } else { $null }
    $origin = if ($isGit) { (Invoke-GitText -Root $canonical -Arguments @('remote', 'get-url', 'origin') | Select-Object -First 1) } else { $null }
    if ($origin) {
        try {
            $originUri = [Uri]$origin
            if (-not [string]::IsNullOrWhiteSpace($originUri.UserInfo)) {
                $origin = $origin -replace ('//' + [regex]::Escape($originUri.UserInfo) + '@'), '//[redacted]@'
            }
        } catch { }
    }
    $defaultRef = if ($isGit) { (Invoke-GitText -Root $canonical -Arguments @('symbolic-ref', '--quiet', '--short', 'refs/remotes/origin/HEAD') | Select-Object -First 1) } else { $null }
    $worktreeLines = if ($isGit) { @(Invoke-GitText -Root $canonical -Arguments @('worktree', 'list', '--porcelain')) } else { @() }
    $active = @($processes | Where-Object {
        ($_.CommandLine -and $_.CommandLine.IndexOf($canonical, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) -or
        ($_.ExecutablePath -and $_.ExecutablePath.IndexOf($canonical, [System.StringComparison]::OrdinalIgnoreCase) -ge 0)
    } | Select-Object ProcessId, Name, ExecutablePath)

    $manifests = New-Object System.Collections.Generic.List[string]
    foreach ($name in $manifestNames) {
        $candidate = Join-Path $canonical $name
        if (Test-Path -LiteralPath $candidate) { $manifests.Add($candidate) }
    }
    foreach ($file in Get-ChildItem -LiteralPath $canonical -File -Filter '*.sln' -ErrorAction SilentlyContinue) { $manifests.Add($file.FullName) }

    $cacheCandidates = New-Object System.Collections.Generic.List[object]
    $queue = New-Object System.Collections.Queue
    $queue.Enqueue([pscustomobject]@{ Path = $canonical; Depth = 0 })
    while ($queue.Count -gt 0) {
        $entry = $queue.Dequeue()
        if ([int]$entry.Depth -ge $CacheDepth) { continue }
        try {
            foreach ($child in Get-ChildItem -LiteralPath ([string]$entry.Path) -Directory -Force -ErrorAction Stop) {
                if (Test-IsReparsePoint -Item $child) { continue }
                if ($child.Name -eq '.git') { continue }
                if ($cacheNames -contains $child.Name) {
                    $class = if ($child.Name -in @('dist', 'build', 'output', '.codegraph')) { 'REVIEW_REQUIRED' } else { 'SAFE_REBUILDABLE_CANDIDATE' }
                    $measurement = if ($SkipCacheSizes) { $null } else { Measure-Tree -LiteralPath $child.FullName }
                    $cacheCandidates.Add([pscustomobject]@{
                        Path = $child.FullName
                        Name = $child.Name
                        Class = $class
                        Bytes = if ($measurement) { $measurement.Bytes } else { $null }
                        Files = if ($measurement) { $measurement.Files } else { $null }
                        Errors = if ($measurement) { @($measurement.Errors) } else { @() }
                    })
                    continue
                }
                $nestedGit = Test-Path -LiteralPath (Join-Path $child.FullName '.git')
                if (-not $nestedGit) { $queue.Enqueue([pscustomobject]@{ Path = $child.FullName; Depth = [int]$entry.Depth + 1 }) }
            }
        }
        catch { $scanErrors.Add("$([string]$entry.Path) :: $($_.Exception.Message)") }
    }

    $instructions = @(Get-ChildItem -LiteralPath $canonical -File -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -in @('AGENTS.md', 'CLAUDE.md') } | Select-Object -ExpandProperty FullName)
    $manifestArray = @($manifests | ForEach-Object { $_ })
    $cacheArray = @($cacheCandidates | ForEach-Object { $_ })
    $projects.Add([pscustomobject]@{
        Root = $canonical
        IsGit = $isGit
        Branch = $branch
        Head = $head
        Origin = $origin
        RemoteDefaultRef = $defaultRef
        StatusEntries = $status.Count
        Dirty = [bool]($status.Count -gt 0)
        WorktreePorcelain = @($worktreeLines)
        ActiveProcesses = @($active)
        Manifests = $manifestArray
        Instructions = $instructions
        CacheCandidates = $cacheArray
    })
}

$result = [pscustomobject]@{
    CapturedAt = (Get-Date).ToString('o')
    ComputerName = $env:COMPUTERNAME
    RequestedRoots = @($requestedRoots)
    ScannedRoots = @($roots | ForEach-Object { $_ })
    MaxDepth = $MaxDepth
    CacheDepth = $CacheDepth
    Projects = @($projects | ForEach-Object { $_ })
    Errors = @($scanErrors | ForEach-Object { $_ })
}

$json = $result | ConvertTo-Json -Depth 10
if ($OutputPath) {
    $parent = Split-Path -Parent $OutputPath
    if ($parent -and -not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    [System.IO.File]::WriteAllText($OutputPath, $json, (New-Object System.Text.UTF8Encoding($false)))
}
$json
