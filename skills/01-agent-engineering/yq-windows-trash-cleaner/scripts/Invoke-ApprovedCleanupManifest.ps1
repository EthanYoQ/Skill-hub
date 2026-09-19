[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ManifestPath,
    [Parameter(Mandatory = $true)][string[]]$ApprovedId,
    [switch]$Apply,
    [string]$PreflightToken,
    [string]$LogPath
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

function Get-Sha256Text {
    param([Parameter(Mandatory = $true)][string]$Text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Text))).Replace('-', '').ToLowerInvariant()) }
    finally { $sha.Dispose() }
}

function Get-FreeBytesForPath {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    try { return [int64]([System.IO.DriveInfo]::new([System.IO.Path]::GetPathRoot($LiteralPath)).AvailableFreeSpace) }
    catch { return $null }
}

function Resolve-SafeTarget {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    if (-not [System.IO.Path]::IsPathRooted($LiteralPath)) { throw "Target is not absolute: $LiteralPath" }
    $resolved = (Resolve-Path -LiteralPath $LiteralPath -ErrorAction Stop).Path
    $cursor = Get-Item -LiteralPath $resolved -Force -ErrorAction Stop
    while ($cursor) {
        if ($cursor.Attributes -band [System.IO.FileAttributes]::ReparsePoint) { throw "Target or parent is a reparse point: $($cursor.FullName)" }
        $cursor = $cursor.Parent
    }
    return $resolved
}

function Get-TrustedCommandPath {
    param([Parameter(Mandatory = $true)][string]$Name, [Parameter(Mandatory = $true)][string]$ExpectedPath)
    if (-not [System.IO.Path]::IsPathRooted($ExpectedPath)) { throw "expected_command_path must be absolute for $Name." }
    $command = Get-Command -Name $Name -CommandType Application -ErrorAction Stop | Select-Object -First 1
    $resolved = (Resolve-Path -LiteralPath $command.Source -ErrorAction Stop).Path
    $expected = (Resolve-Path -LiteralPath $ExpectedPath -ErrorAction Stop).Path
    if ([System.IO.Path]::GetExtension($resolved) -notin @('.exe', '.cmd')) { throw "Command type is not an allowlisted executable wrapper: $resolved" }
    if (-not $resolved.Equals($expected, [System.StringComparison]::OrdinalIgnoreCase)) { throw "Resolved command path differs from expected_command_path: $resolved" }
    return $resolved
}

function Get-MatchingProcesses {
    param([string]$LiteralPath, [string[]]$Names)
    return @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        if ($_.ProcessId -eq $PID) { return $false }
        $baseName = [System.IO.Path]::GetFileNameWithoutExtension([string]$_.Name).ToLowerInvariant()
        ($Names -contains $baseName) -or
        ($_.CommandLine -and $_.CommandLine.IndexOf($LiteralPath, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) -or
        ($_.ExecutablePath -and $_.ExecutablePath.IndexOf($LiteralPath, [System.StringComparison]::OrdinalIgnoreCase) -ge 0)
    } | Select-Object ProcessId, Name, ExecutablePath)
}

function Write-ActionLog {
    param([Parameter(Mandatory = $true)][object]$Record)
    if (-not $LogPath) { return }
    $parent = Split-Path -Parent $LogPath
    if ($parent -and -not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    [System.IO.File]::AppendAllText($LogPath, (($Record | ConvertTo-Json -Depth 10 -Compress) + [Environment]::NewLine), (New-Object System.Text.UTF8Encoding($false)))
}

function Write-ResultAndExit {
    param([object[]]$Results, [string]$Token, [int]$ExitCode)
    [pscustomobject]@{
        GeneratedAt = (Get-Date).ToString('o')
        Apply = [bool]$Apply
        PreflightToken = $Token
        Results = @($Results)
    } | ConvertTo-Json -Depth 12 | Write-Output
    if ($ExitCode -ne 0) { exit $ExitCode }
}

$actionMap = @{
    'pnpm-store-prune' = @{ Name = 'pnpm.cmd'; Query = @('store','path'); Execute = @('store','prune'); Processes = @('node','pnpm') }
    'uv-cache-prune'   = @{ Name = 'uv.exe'; Query = @('cache','dir'); Execute = @('cache','prune'); Processes = @('uv','python','pythonw') }
    'pip-cache-purge'  = @{ Name = 'python.exe'; Query = @('-m','pip','cache','dir'); Execute = @('-m','pip','cache','purge'); Processes = @('python','pythonw','pip') }
    'npm-cache-clean'  = @{ Name = 'npm.cmd'; Query = @('config','get','cache'); Execute = @('cache','clean','--force'); Processes = @('node','npm','npx') }
    'yarn-cache-clean' = @{ Name = 'yarn.cmd'; Query = @('cache','dir'); Execute = @('cache','clean'); Processes = @('node','yarn') }
    'bun-cache-clean'  = @{ Name = 'bun.exe'; Query = @('pm','cache'); Execute = @('pm','cache','rm'); Processes = @('bun') }
}

$manifestRaw = Get-Content -LiteralPath $ManifestPath -Raw
$manifestDocument = $manifestRaw | ConvertFrom-Json
$entries = if ($manifestDocument.PSObject.Properties.Name -contains 'items') { @($manifestDocument.items) } else { @($manifestDocument) }
$duplicateIds = @($entries | Group-Object id | Where-Object Count -gt 1)
if ($duplicateIds.Count -gt 0) { throw "Manifest contains duplicate IDs: $($duplicateIds.Name -join ', ')" }
$requested = @($ApprovedId | Select-Object -Unique | Sort-Object)
$unknown = @($requested | Where-Object { $_ -notin @($entries.id) })
if ($unknown.Count -gt 0) { throw "ApprovedId not found in manifest: $($unknown -join ', ')" }

$plans = @()
$preflightResults = @()
foreach ($id in $requested) {
    $entry = @($entries | Where-Object id -eq $id) | Select-Object -First 1
    $result = [ordered]@{ Id = $id; StartedAt = (Get-Date).ToString('o'); Apply = [bool]$Apply; Status = 'PREFLIGHT'; Action = [string]$entry.action }
    try {
        if (-not ($entry.PSObject.Properties.Name -contains 'approved') -or -not ($entry.approved -is [bool]) -or $entry.approved -ne $true) { throw 'approved must be the JSON Boolean true.' }
        if ([string]$entry.class -ne 'SAFE_REBUILDABLE') { throw "Class is not SAFE_REBUILDABLE: $($entry.class)" }
        $target = Resolve-SafeTarget -LiteralPath ([string]$entry.target)
        $result.Target = $target
        $plan = [ordered]@{ Id = $id; Action = [string]$entry.action; Target = $target; BeforeFreeBytes = Get-FreeBytesForPath -LiteralPath $target }

        if ([string]$entry.action -eq 'git-worktree-remove') {
            foreach ($required in @('owner_root','expected_command_path')) { if (-not ($entry.PSObject.Properties.Name -contains $required) -or -not $entry.$required) { throw "git-worktree-remove requires $required." } }
            $ownerRoot = Resolve-SafeTarget -LiteralPath ([string]$entry.owner_root)
            $gitPath = Get-TrustedCommandPath -Name 'git.exe' -ExpectedPath ([string]$entry.expected_command_path)
            $directActive = @(Get-MatchingProcesses -LiteralPath $target -Names @())
            if ($directActive.Count -gt 0) { throw "Active process path match blocks worktree removal: $($directActive.ProcessId -join ', ')" }
            $ambiguousInterpreters = @(Get-MatchingProcesses -LiteralPath $target -Names @('python','pythonw','node','bun','java','dotnet','ruby'))
            if ($ambiguousInterpreters.Count -gt 0) { throw "Interpreter activity cannot be proven outside the worktree; close or independently trace these PIDs: $($ambiguousInterpreters.ProcessId -join ', ')" }
            $listed = @(& $gitPath -C $ownerRoot worktree list --porcelain 2>&1)
            $registered = ($listed -contains ("worktree " + $target)) -or ($listed -contains ("worktree " + ($target -replace '\\','/')))
            if ($LASTEXITCODE -ne 0 -or -not $registered) { throw 'Target is not a registered worktree.' }
            $status = @(& $gitPath -C $target status --porcelain=v1 --untracked-files=normal 2>&1)
            if ($LASTEXITCODE -ne 0 -or $status.Count -gt 0) { throw 'Worktree is dirty or Git status failed.' }
            $head = @(& $gitPath -C $target rev-parse HEAD 2>&1) | Select-Object -First 1
            $defaultRef = @(& $gitPath -C $ownerRoot symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>$null) | Select-Object -First 1
            if (-not $defaultRef) { throw 'Remote default ref is unavailable; refresh and verify it before approval.' }
            & $gitPath -C $target merge-base --is-ancestor HEAD $defaultRef 2>$null
            if ($LASTEXITCODE -ne 0) { throw "Worktree HEAD is not contained in $defaultRef." }
            $plan.OwnerRoot = $ownerRoot; $plan.CommandPath = $gitPath; $plan.Head = $head; $plan.RemoteDefaultRef = $defaultRef
            $result.Preflight = 'REGISTERED_CLEAN_INACTIVE_REMOTE_CONTAINED'
        }
        elseif ($actionMap.ContainsKey([string]$entry.action)) {
            if (-not ($entry.PSObject.Properties.Name -contains 'expected_command_path') -or -not $entry.expected_command_path) { throw 'Package action requires expected_command_path.' }
            $spec = $actionMap[[string]$entry.action]
            $commandPath = Get-TrustedCommandPath -Name $spec.Name -ExpectedPath ([string]$entry.expected_command_path)
            $active = @(Get-MatchingProcesses -LiteralPath $target -Names @($spec.Processes))
            if ($active.Count -gt 0) { throw "Active owner/tool process blocks prune: $($active.ProcessId -join ', ')" }
            $workDir = if ($entry.PSObject.Properties.Name -contains 'work_dir' -and $entry.work_dir) { Resolve-SafeTarget -LiteralPath ([string]$entry.work_dir) } else { (Get-Location).Path }
            if ([string]$entry.action -eq 'bun-cache-clean' -and -not (Test-Path -LiteralPath (Join-Path $workDir 'package.json'))) { throw 'Bun cache cleanup requires work_dir containing package.json.' }
            Push-Location -LiteralPath $workDir
            try { $queryOutput = @(& $commandPath @($spec.Query) 2>&1); $queryExit = $LASTEXITCODE }
            finally { Pop-Location }
            if ($queryExit -ne 0) { throw "Cache path query failed: $($queryOutput -join ' ')" }
            $reportedPath = @($queryOutput | ForEach-Object { [string]$_ } | Where-Object { [System.IO.Path]::IsPathRooted($_.Trim()) } | Select-Object -Last 1)
            if ($reportedPath.Count -ne 1) { throw "Cache path query did not return one absolute path: $($queryOutput -join ' ')" }
            $actualCache = Resolve-SafeTarget -LiteralPath $reportedPath[0].Trim()
            if (-not $actualCache.Equals($target, [System.StringComparison]::OrdinalIgnoreCase)) { throw "Manifest target does not match the tool's current cache path: $actualCache" }
            $targetItem = Get-Item -LiteralPath $target -Force
            $plan.CommandPath = $commandPath; $plan.Arguments = @($spec.Execute); $plan.WorkDir = $workDir; $plan.TargetLastWriteUtc = $targetItem.LastWriteTimeUtc.Ticks
            $result.Preflight = 'TARGET_BOUND_INACTIVE_COMMAND_ALLOWLISTED'
        }
        else { throw "Action is not allowlisted: $($entry.action)" }

        $plans += [pscustomobject]$plan
        $result.Status = 'PREFLIGHT_PASSED'
    }
    catch {
        $result.Status = 'BLOCKED_OR_FAILED'
        $result.Error = $_.Exception.Message
    }
    $result.CompletedAt = (Get-Date).ToString('o')
    $preflightResults += [pscustomobject]$result
}

if (@($preflightResults | Where-Object Status -eq 'BLOCKED_OR_FAILED').Count -gt 0) {
    foreach ($record in $preflightResults) { Write-ActionLog -Record $record }
    Write-ResultAndExit -Results $preflightResults -Token $null -ExitCode 2
}

$tokenPlans = @($plans | Select-Object Id, Action, Target, CommandPath, Arguments, WorkDir, TargetLastWriteUtc, OwnerRoot, Head, RemoteDefaultRef)
$tokenMaterial = [ordered]@{ ManifestHash = Get-Sha256Text -Text $manifestRaw; ApprovedIds = $requested; Plans = $tokenPlans }
$currentToken = Get-Sha256Text -Text ($tokenMaterial | ConvertTo-Json -Depth 10 -Compress)
if (-not $Apply) {
    foreach ($record in $preflightResults) { $record.Status = 'PREFLIGHT_PASSED_NOT_APPLIED'; Write-ActionLog -Record $record }
    Write-ResultAndExit -Results $preflightResults -Token $currentToken -ExitCode 0
    return
}
if (-not $PreflightToken -or -not $PreflightToken.Equals($currentToken, [System.StringComparison]::OrdinalIgnoreCase)) {
    foreach ($record in $preflightResults) { $record.Status = 'BLOCKED_OR_FAILED'; $record | Add-Member -NotePropertyName Error -NotePropertyValue 'PreflightToken is missing or stale; rerun without -Apply and approve the new token.' -Force; Write-ActionLog -Record $record }
    Write-ResultAndExit -Results $preflightResults -Token $currentToken -ExitCode 2
}

$executionResults = @()
$executionFailed = $false
foreach ($plan in $plans) {
    $record = [ordered]@{ Id = $plan.Id; StartedAt = (Get-Date).ToString('o'); Apply = $true; Status = 'EXECUTING'; Action = $plan.Action; Target = $plan.Target; BeforeFreeBytes = $plan.BeforeFreeBytes }
    try {
        if ($plan.Action -eq 'git-worktree-remove') {
            $output = @(& $plan.CommandPath -C $plan.OwnerRoot worktree remove -- $plan.Target 2>&1 | ForEach-Object { $_.ToString() })
        } else {
            Push-Location -LiteralPath $plan.WorkDir
            try { $output = @(& $plan.CommandPath @($plan.Arguments) 2>&1 | ForEach-Object { $_.ToString() }) }
            finally { Pop-Location }
        }
        $exitCode = $LASTEXITCODE
        if ($exitCode -ne 0) { throw "Semantic command failed with exit code ${exitCode}: $($output -join ' ')" }
        $record.Output = $output
        $record.AfterFreeBytes = Get-FreeBytesForPath -LiteralPath $plan.Target
        $record.ActualReleasedBytes = if ($null -ne $record.BeforeFreeBytes -and $null -ne $record.AfterFreeBytes) { [int64]$record.AfterFreeBytes - [int64]$record.BeforeFreeBytes } else { $null }
        $record.Status = 'APPLIED'
    }
    catch { $record.Status = 'BLOCKED_OR_FAILED'; $record.Error = $_.Exception.Message; $executionFailed = $true }
    $record.CompletedAt = (Get-Date).ToString('o')
    $objectRecord = [pscustomobject]$record
    $executionResults += $objectRecord
    Write-ActionLog -Record $objectRecord
    if ($executionFailed) { break }
}
Write-ResultAndExit -Results $executionResults -Token $currentToken -ExitCode $(if ($executionFailed) { 3 } else { 0 })
