[CmdletBinding()]
param(
    [string]$Root = '.',
    [ValidateRange(1, 200)][int]$Top = 25,
    [switch]$Json,
    [switch]$IncludeProcesses,
    [switch]$HashReleaseArtifacts
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

function Get-CanonicalProjectRoot([string]$LiteralPath) {
    $resolved = (Resolve-Path -LiteralPath $LiteralPath -ErrorAction Stop).Path
    $item = Get-Item -LiteralPath $resolved -Force -ErrorAction Stop
    if (-not $item.PSIsContainer) { throw "Project root must be a directory: $resolved" }
    if ($resolved.TrimEnd('\') -eq [IO.Path]::GetPathRoot($resolved).TrimEnd('\')) {
        throw "Refusing a filesystem root; use the whole-computer inventory scripts instead: $resolved"
    }
    $cursor = $item
    while ($cursor) {
        if ($cursor.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "Refusing a project root reached through a reparse point: $($cursor.FullName)"
        }
        $cursor = $cursor.Parent
    }
    return $resolved.TrimEnd('\')
}

function Invoke-GitLines([string]$WorkingDirectory, [string[]]$GitArgs) {
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'SilentlyContinue'
    try {
        $output = & git -C $WorkingDirectory @GitArgs 2>$null
        $exitCode = $LASTEXITCODE
    }
    finally { $ErrorActionPreference = $previous }
    if ($exitCode -eq 0) { return @($output) }
    return @()
}

function Protect-RemoteText([string]$Text) {
    if (-not $Text) { return $Text }
    return [regex]::Replace($Text, '(https?://)[^/@\s]+@', '$1[redacted]@')
}

function Get-RelativePath([string]$BasePath, [string]$ChildPath) {
    $prefix = $BasePath.TrimEnd('\') + '\'
    if ($ChildPath.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        return $ChildPath.Substring($prefix.Length)
    }
    return $ChildPath
}

function Measure-SafeTree([string]$LiteralPath) {
    $item = Get-Item -LiteralPath $LiteralPath -Force -ErrorAction Stop
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        return [pscustomobject]@{bytes=[int64]0;files=0;directories=0;skipped_reparse_points=1;errors=@('target-is-reparse-point')}
    }
    if (-not $item.PSIsContainer) {
        return [pscustomobject]@{bytes=[int64]$item.Length;files=1;directories=0;skipped_reparse_points=0;errors=@()}
    }
    $bytes=[int64]0; $files=0; $directories=0; $skipped=0
    $errors=New-Object Collections.Generic.List[string]
    $stack=New-Object Collections.Generic.Stack[string]
    $stack.Push($item.FullName)
    while($stack.Count -gt 0) {
        $current=$stack.Pop(); $directories++
        try { $children=@(Get-ChildItem -LiteralPath $current -Force -ErrorAction Stop) }
        catch { $errors.Add("$current :: $($_.Exception.Message)"); continue }
        foreach($child in $children) {
            if($child.Attributes -band [IO.FileAttributes]::ReparsePoint) { $skipped++; continue }
            if($child.PSIsContainer) { $stack.Push($child.FullName) }
            else { $files++; $bytes += [int64]$child.Length }
        }
    }
    return [pscustomobject]@{bytes=$bytes;files=$files;directories=$directories;skipped_reparse_points=$skipped;errors=@($errors)}
}

function Convert-ToMB([int64]$Bytes) { return [math]::Round($Bytes / 1MB, 2) }

function Get-TopLevelSizes([string]$RootPath, [int]$Limit) {
    $rows=@()
    foreach($item in Get-ChildItem -LiteralPath $RootPath -Force -ErrorAction SilentlyContinue) {
        $measurement=Measure-SafeTree $item.FullName
        $rows += [pscustomobject]@{
            path=$item.Name
            type=if($item.PSIsContainer){'dir'}else{'file'}
            size_mb=Convert-ToMB $measurement.bytes
            skipped_reparse_points=$measurement.skipped_reparse_points
            error_count=$measurement.errors.Count
            last_write_time=$item.LastWriteTime.ToString('s')
        }
    }
    return @($rows | Sort-Object size_mb -Descending | Select-Object -First $Limit)
}

function Get-CandidateDirectories([string]$RootPath, [int]$Limit) {
    $names=@('node_modules','target','dist','build','out','.next','.nuxt','.svelte-kit','.turbo','.vite','.parcel-cache','coverage','diagnostics','output','logs','tmp','temp','.worktrees','.pytest_cache','.mypy_cache','.tox','.venv','venv','__pycache__')
    $cacheNames=@('node_modules','.next','.nuxt','.svelte-kit','.turbo','.vite','.parcel-cache','.pytest_cache','.mypy_cache','.tox','__pycache__')
    $queue=New-Object Collections.Generic.Queue[object]
    $queue.Enqueue([pscustomobject]@{path=$RootPath;depth=0})
    $rows=@()
    while($queue.Count -gt 0) {
        $node=$queue.Dequeue()
        if($node.depth -ge 4){continue}
        try{$dirs=@(Get-ChildItem -LiteralPath $node.path -Directory -Force -ErrorAction Stop)}catch{continue}
        foreach($dir in $dirs) {
            if($dir.Attributes -band [IO.FileAttributes]::ReparsePoint){continue}
            if($dir.Name -eq '.git'){continue}
            $queue.Enqueue([pscustomobject]@{path=$dir.FullName;depth=($node.depth+1)})
            if($names -notcontains $dir.Name){continue}
            $measurement=Measure-SafeTree $dir.FullName
            $cacheLike=$cacheNames -contains $dir.Name
            $rows += [pscustomobject]@{
                path=Get-RelativePath $RootPath $dir.FullName
                size_mb=Convert-ToMB $measurement.bytes
                classification=if($cacheLike){'generated_cache_candidate'}else{'review_required_candidate'}
                confidence=if($cacheLike){'medium'}else{'low'}
                reason=if($cacheLike){'Conventional cache name; manifest, inactivity, Git scope, and regeneration still require proof.'}else{'The name may contain release, runtime, evidence, or user data and cannot establish disposability.'}
                recommended_action=if($cacheLike){'verify_manifest_owner_and_dry_run_before_manifesting'}else{'inspect_contents_ownership_and_recovery'}
                skipped_reparse_points=$measurement.skipped_reparse_points
                error_count=$measurement.errors.Count
                last_write_time=$dir.LastWriteTime.ToString('s')
            }
        }
    }
    return @($rows | Sort-Object size_mb -Descending | Select-Object -First $Limit)
}

function Convert-GitCleanLineToPath([string]$Line) {
    $prefix='Would remove '
    if(-not $Line -or -not $Line.StartsWith($prefix,[StringComparison]::Ordinal)){return $null}
    return $Line.Substring($prefix.Length).TrimEnd('/','\')
}

function Get-ReviewRequiredIgnoredPaths([string[]]$CleanLines) {
    $rows=@()
    foreach($line in $CleanLines) {
        $path=Convert-GitCleanLineToPath $line
        if(-not $path){continue}
        $normalized=$path.Replace('\','/').TrimEnd('/')
        $reasons=New-Object Collections.Generic.List[string]
        if($normalized -match '(^|/)\.(codex|codegraph|gstack|claude)($|/)'){$reasons.Add('agent_context_or_index')}
        if($normalized -match '(^|/)(\.runtime|test_dataset|manual_(frontend|program)_runs|raw_documents|mailbox|truth|dataset|extracted_invoices)($|/|_)'){$reasons.Add('local_data_or_validation_evidence')}
        if($normalized -match '(^|/)(dist|release[-_][^/]*|[^/]+\.(zip|exe|msi|dmg|pkg|app))($|/)'){$reasons.Add('release_artifact')}
        if($normalized -match '(^|/)(\.env($|\.)|[^/]+\.(pem|key|crt|pfx|p12|kdbx))($|/)'){$reasons.Add('credential_or_secret_candidate')}
        if($reasons.Count -gt 0){$rows += [pscustomobject]@{path=$path;reasons=@($reasons)}}
    }
    return @($rows)
}

function Get-SelectedPathSummary([string]$RootPath, [string]$RelativePath, [switch]$HashFile) {
    $full=Join-Path $RootPath $RelativePath
    if(-not (Test-Path -LiteralPath $full)){return [pscustomobject]@{path=$RelativePath;exists=$false}}
    $item=Get-Item -LiteralPath $full -Force
    $measurement=Measure-SafeTree $full
    $hash=$null
    if($HashFile -and -not $item.PSIsContainer){$hash=(Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash}
    return [pscustomobject]@{
        path=$RelativePath;exists=$true;type=if($item.PSIsContainer){'dir'}else{'file'}
        file_count=$measurement.files;dir_count=$measurement.directories;size_mb=Convert-ToMB $measurement.bytes
        skipped_reparse_points=$measurement.skipped_reparse_points;error_count=$measurement.errors.Count
        last_write_time=$item.LastWriteTime.ToString('s');sha256=$hash
    }
}

function Get-ContextSummaries([string]$RootPath) {
    $rows=@()
    foreach($path in @('.codex','.claude','.codegraph','.gstack','.runtime','test_dataset','.pytest_cache','.venv','__pycache__')) {
        $rows += Get-SelectedPathSummary $RootPath $path
    }
    return @($rows)
}

function Get-ReleaseSummaries([string]$RootPath, [switch]$HashArtifacts) {
    $rows=@()
    foreach($relative in @('dist','build','output')) {
        $full=Join-Path $RootPath $relative
        if(Test-Path -LiteralPath $full){$rows += Get-SelectedPathSummary $RootPath $relative}
    }
    foreach($item in Get-ChildItem -LiteralPath $RootPath -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'release-*' -or $_.Extension -match '^\.(zip|exe|msi)$' }) {
        $relative=Get-RelativePath $RootPath $item.FullName
        $hashIt=$HashArtifacts -and -not $item.PSIsContainer -and $item.Extension -match '^\.(zip|exe|msi)$'
        $rows += Get-SelectedPathSummary $RootPath $relative -HashFile:$hashIt
    }
    return @($rows)
}

function Get-WorkspaceProcesses([string]$RootPath) {
    $rows=@()
    foreach($process in Get-CimInstance Win32_Process -ErrorAction SilentlyContinue) {
        $matched=$false
        if($process.CommandLine -and $process.CommandLine.IndexOf($RootPath,[StringComparison]::OrdinalIgnoreCase) -ge 0){$matched=$true}
        if(-not $matched -and $process.ExecutablePath -and $process.ExecutablePath.IndexOf($RootPath,[StringComparison]::OrdinalIgnoreCase) -ge 0){$matched=$true}
        if($matched){$rows += [pscustomobject]@{process_id=$process.ProcessId;name=$process.Name;executable_path=$process.ExecutablePath;project_path_match=$true}}
    }
    return @($rows)
}

$rootPath=Get-CanonicalProjectRoot $Root
$gitTop=@(Invoke-GitLines $rootPath @('rev-parse','--show-toplevel'))
$isGit=$gitTop.Count -gt 0
$status=@();$worktrees=@();$ignored=@();$untracked=@();$remotes=@();$branch=$null;$head=$null
if($isGit){
    $status=@(Invoke-GitLines $rootPath @('status','--short'))
    $worktrees=@(Invoke-GitLines $rootPath @('worktree','list','--porcelain'))
    $ignored=@(Invoke-GitLines $rootPath @('clean','-ndX'))
    $untracked=@(Invoke-GitLines $rootPath @('clean','-nd'))
    $remotes=@(Invoke-GitLines $rootPath @('remote','-v') | ForEach-Object { Protect-RemoteText $_ })
    $branchLines=@(Invoke-GitLines $rootPath @('branch','--show-current')); if($branchLines.Count){$branch=$branchLines[0]}
    $headLines=@(Invoke-GitLines $rootPath @('rev-parse','HEAD')); if($headLines.Count){$head=$headLines[0]}
}
$reviewRequired=@(Get-ReviewRequiredIgnoredPaths $ignored)
$processes=if($IncludeProcesses){@(Get-WorkspaceProcesses $rootPath)}else{@()}
$report=[ordered]@{
    schema_version=1;generated_at=(Get-Date).ToString('o');audit_only=$true;root=$rootPath;followed_reparse_points=$false
    git=[ordered]@{is_git=$isGit;top_level=if($isGit){$gitTop[0]}else{$null};branch=$branch;head=$head;remotes=$remotes;status=$status;worktrees=$worktrees;ignored_clean_dry_run=$ignored;untracked_clean_dry_run=$untracked;review_required_ignored_paths=$reviewRequired}
    top_level_sizes=@(Get-TopLevelSizes $rootPath $Top)
    cleanup_candidate_dirs=@(Get-CandidateDirectories $rootPath $Top)
    protected_context_and_data=@(Get-ContextSummaries $rootPath)
    release_artifacts=@(Get-ReleaseSummaries $rootPath -HashArtifacts:$HashReleaseArtifacts)
    workspace_processes=$processes
}
if($Json){$report|ConvertTo-Json -Depth 10;return}
Write-Output '# Project Cleanup Audit'
Write-Output "Root: $rootPath"
Write-Output "Audit only: $($report.audit_only)"
Write-Output "Git repository: $isGit; branch: $branch; status entries: $($status.Count)"
Write-Output '## Top-level sizes';$report.top_level_sizes|Format-Table -AutoSize|Out-String -Width 240|Write-Output
Write-Output '## Candidate directories';$report.cleanup_candidate_dirs|Format-Table -AutoSize|Out-String -Width 280|Write-Output
Write-Output '## Review-required ignored paths';$reviewRequired|Format-Table -AutoSize|Out-String -Width 240|Write-Output
Write-Output '## Protected context and data';$report.protected_context_and_data|Format-Table -AutoSize|Out-String -Width 240|Write-Output
Write-Output '## Release artifacts';$report.release_artifacts|Format-Table -AutoSize|Out-String -Width 240|Write-Output
if($IncludeProcesses){Write-Output '## Project-owned process evidence';$processes|Format-Table -AutoSize|Out-String -Width 240|Write-Output}
