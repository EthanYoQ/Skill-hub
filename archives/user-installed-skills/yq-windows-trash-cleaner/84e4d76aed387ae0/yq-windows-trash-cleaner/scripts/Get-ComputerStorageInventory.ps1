[CmdletBinding()]
param(
    [string]$ProjectInventoryPath,
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'
$items = New-Object System.Collections.Generic.List[object]
$errors = New-Object System.Collections.Generic.List[string]
$measureScript = Join-Path $PSScriptRoot 'Measure-PathUsage.ps1'
$processes = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine })

function Add-InventoryItem {
    param(
        [string]$Id,
        [string]$Path,
        [string]$Owner,
        [string]$Class,
        [string]$Action,
        [string]$Recovery,
        [Nullable[int64]]$KnownBytes = $null,
        [string[]]$ToolProcessNames = @()
    )
    if (-not $Path -or -not (Test-Path -LiteralPath $Path)) { return }
    try {
        $resolved = (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path
        $entry = Get-Item -LiteralPath $resolved -Force -ErrorAction Stop
        $cursor = $entry
        while ($cursor) {
            if ($cursor.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
                throw "Refusing an inventory path through a reparse point: $($cursor.FullName)"
            }
            $cursor = $cursor.Parent
        }
        $bytes = $KnownBytes
        $files = $null
        $directories = $null
        $measureErrors = @()
        if ($null -eq $bytes) {
            if ($entry.PSIsContainer) {
                $measured = (& $measureScript -Path @($resolved) | ConvertFrom-Json).Results | Select-Object -First 1
                $bytes = [int64]$measured.Bytes
                $files = $measured.Files
                $directories = $measured.Directories
                $measureErrors = @($measured.Errors)
            }
            else { $bytes = [int64]$entry.Length; $files = 1; $directories = 0 }
        }
        $active = @($processes | Where-Object {
            ($_.CommandLine -and $_.CommandLine.IndexOf($resolved, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) -or
            ($_.ExecutablePath -and $_.ExecutablePath.IndexOf($resolved, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) -or
            ($ToolProcessNames.Count -gt 0 -and $ToolProcessNames -contains ([System.IO.Path]::GetFileNameWithoutExtension([string]$_.Name).ToLowerInvariant()))
        } | Select-Object ProcessId, Name, ExecutablePath)
        $effectiveClass = if ($Class -eq 'SAFE_REBUILDABLE' -and $active.Count -gt 0) { 'REVIEW_REQUIRED' } else { $Class }
        $items.Add([pscustomobject]@{
            Id = $Id
            Path = $resolved
            Owner = $Owner
            Class = $effectiveClass
            Action = $Action
            Recovery = $Recovery
            Bytes = [int64]$bytes
            Files = $files
            Directories = $directories
            LastWriteTime = $entry.LastWriteTime.ToString('o')
            Attributes = [string]$entry.Attributes
            ActiveProcesses = @($active)
            ActivityState = if ($active.Count -gt 0) { 'ACTIVE_OR_TOOL_IN_USE' } else { 'NO_DIRECT_MATCH_DETECTED' }
            MeasurementErrors = $measureErrors
        })
    }
    catch { $errors.Add("$Path :: $($_.Exception.Message)") }
}

$volumes = @(Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' -ErrorAction SilentlyContinue | ForEach-Object {
    [pscustomobject]@{
        DeviceId = $_.DeviceID
        VolumeName = $_.VolumeName
        FileSystem = $_.FileSystem
        SizeBytes = [int64]$_.Size
        FreeBytes = [int64]$_.FreeSpace
    }
})

$profile = $env:USERPROFILE
$local = $env:LOCALAPPDATA
$roaming = $env:APPDATA
$known = @(
    @('user-temp', (Join-Path $local 'Temp'), 'Windows/user applications', 'REVIEW_REQUIRED', 'expired-temp-directories', 'Applications recreate temporary data'),
    @('npm-cache', (Join-Path $local 'npm-cache'), 'npm', 'SAFE_REBUILDABLE', 'npm-cache-verify-or-clean', 'npm redownloads packages', @('node','npm','npx')),
    @('pnpm-store', (Join-Path $local 'pnpm\store'), 'pnpm', 'REVIEW_REQUIRED', 'pnpm-store-prune', 'pnpm redownloads pruned packages'),
    @('pnpm-cache', (Join-Path $local 'pnpm-cache'), 'pnpm legacy cache', 'REVIEW_REQUIRED', 'review-obsolete-store', 'pnpm redownloads packages'),
    @('pip-cache', (Join-Path $local 'pip\Cache'), 'pip', 'SAFE_REBUILDABLE', 'pip-cache-purge', 'pip redownloads packages', @('python','pythonw','pip')),
    @('uv-cache', (Join-Path $local 'uv\cache'), 'uv', 'SAFE_REBUILDABLE', 'uv-cache-prune', 'uv redownloads packages', @('uv','python','pythonw')),
    @('yarn-cache', (Join-Path $local 'Yarn\Cache'), 'Yarn', 'SAFE_REBUILDABLE', 'yarn-cache-clean', 'Yarn redownloads packages', @('node','yarn')),
    @('bun-cache', (Join-Path $profile '.bun\install\cache'), 'Bun', 'SAFE_REBUILDABLE', 'bun-cache-clean', 'Bun redownloads packages', @('bun')),
    @('nuget-cache', (Join-Path $profile '.nuget\packages'), 'NuGet', 'REVIEW_REQUIRED', 'nuget-locals-clear', 'NuGet redownloads packages'),
    @('gradle-cache', (Join-Path $profile '.gradle\caches'), 'Gradle', 'REVIEW_REQUIRED', 'gradle-cache-review', 'Gradle redownloads dependencies'),
    @('maven-cache', (Join-Path $profile '.m2\repository'), 'Maven', 'REVIEW_REQUIRED', 'maven-cache-review', 'Maven redownloads dependencies'),
    @('cargo-home', (Join-Path $profile '.cargo'), 'Cargo', 'REVIEW_REQUIRED', 'cargo-cache-review', 'May contain installed binaries and registry cache'),
    @('rustup-home', (Join-Path $profile '.rustup'), 'rustup', 'KEEP_USER_OR_EVIDENCE', 'keep-toolchains', 'Reinstall required toolchains'),
    @('codex-sessions', (Join-Path $profile '.codex\sessions'), 'Codex', 'KEEP_USER_OR_EVIDENCE', 'review-or-transparent-compress', 'Session history is user data'),
    @('codex-runtimes', (Join-Path $profile '.cache\codex-runtimes'), 'Codex', 'KEEP_USER_OR_EVIDENCE', 'keep-current-runtime', 'Runtime is managed and may be active'),
    @('superpowers-worktrees', (Join-Path $profile '.config\superpowers\worktrees'), 'Git/Superpowers', 'KEEP_USER_OR_EVIDENCE', 'git-worktree-review', 'Preserve dirty or unmerged work'),
    @('windows-update-download', 'C:\Windows\SoftwareDistribution\Download', 'Windows Update', 'SYSTEM_MANAGED_DO_NOT_DELETE', 'official-windows-cleanup-only', 'Windows manages update state'),
    @('windows-temp', 'C:\Windows\Temp', 'Windows', 'SYSTEM_MANAGED_DO_NOT_DELETE', 'official-windows-cleanup-only', 'Requires system-aware cleanup'),
    @('windows-wer', 'C:\ProgramData\Microsoft\Windows\WER', 'Windows Error Reporting', 'REVIEW_REQUIRED', 'diagnostic-retention-review', 'May contain crash evidence'),
    @('user-crash-dumps', (Join-Path $local 'CrashDumps'), 'Windows Error Reporting', 'REVIEW_REQUIRED', 'diagnostic-retention-review', 'May contain crash evidence'),
    @('package-cache', 'C:\ProgramData\Package Cache', 'Windows installers', 'SYSTEM_MANAGED_DO_NOT_DELETE', 'keep-installer-cache', 'Required for repair or uninstall'),
    @('windows-installer', 'C:\Windows\Installer', 'Windows Installer', 'SYSTEM_MANAGED_DO_NOT_DELETE', 'keep-installer-cache', 'Required for repair or uninstall'),
    @('recycle-bin', 'C:\$Recycle.Bin', 'Windows Recycle Bin', 'REVIEW_REQUIRED', 'user-confirmed-recycle-bin-empty', 'Items remain recoverable until emptied'),
    @('amd-installers', 'C:\AMD', 'AMD installer', 'REVIEW_REQUIRED', 'driver-install-residue-review', 'Keep until install success and rollback needs are known'),
    @('chrome-local-model', (Join-Path $local 'Google\Chrome\User Data\OptGuideOnDeviceModel'), 'Google Chrome', 'REVIEW_REQUIRED', 'chrome-model-review', 'Chrome may redownload and local features may regress')
)

foreach ($row in $known) {
    $toolNames = if ($row.Count -gt 6) { @($row[6..($row.Count - 1)] | ForEach-Object { ([string]$_) -split '\s+' } | Where-Object { $_ }) } else { @() }
    Add-InventoryItem -Id $row[0] -Path $row[1] -Owner $row[2] -Class $row[3] -Action $row[4] -Recovery $row[5] -ToolProcessNames $toolNames
}

foreach ($updater in Get-ChildItem -LiteralPath $local -Directory -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'updater$' }) {
    $installer = Join-Path $updater.FullName 'installer.exe'
    if (Test-Path -LiteralPath $installer) {
        Add-InventoryItem -Id ("updater-" + $updater.Name) -Path $installer -Owner $updater.Name -Class 'REVIEW_REQUIRED' -Action 'app-updater-installer-review' -Recovery 'Application can download the installer again'
    }
}

foreach ($file in @('C:\pagefile.sys', 'C:\hiberfil.sys', 'C:\swapfile.sys', 'C:\Windows\MEMORY.DMP')) {
    if (Test-Path -LiteralPath $file) {
        $id = [System.IO.Path]::GetFileName($file).Replace('.', '-')
        $class = if ($file -like '*MEMORY.DMP') { 'REVIEW_REQUIRED' } else { 'SYSTEM_MANAGED_DO_NOT_DELETE' }
        Add-InventoryItem -Id $id -Path $file -Owner 'Windows' -Class $class -Action 'official-system-control-only' -Recovery 'Windows manages this file'
    }
}

$dockerVhd = Join-Path $local 'Docker\wsl\disk\docker_data.vhdx'
if (Test-Path -LiteralPath $dockerVhd) {
    Add-InventoryItem -Id 'docker-data-vhdx' -Path $dockerVhd -Owner 'Docker Desktop' -Class 'REVIEW_REQUIRED' -Action 'docker-inventory-then-vhdx-compact' -Recovery 'Retain all logical Docker objects; compaction only after shutdown'
}

try {
    foreach ($key in Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' -ErrorAction Stop) {
        $distro = Get-ItemProperty $key.PSPath
        if ($distro.BasePath) {
            $vhd = Join-Path (($distro.BasePath -replace '^\\\\\?\\', '')) 'ext4.vhdx'
            if (Test-Path -LiteralPath $vhd) {
                Add-InventoryItem -Id ("wsl-" + $distro.DistributionName) -Path $vhd -Owner ("WSL " + $distro.DistributionName) -Class 'REVIEW_REQUIRED' -Action 'wsl-inventory-then-vhdx-compact' -Recovery 'Retain distro; compact only after shutdown'
            }
        }
    }
}
catch { $errors.Add("WSL registry :: $($_.Exception.Message)") }

if ($ProjectInventoryPath -and (Test-Path -LiteralPath $ProjectInventoryPath)) {
    try {
        $projectInventory = Get-Content -LiteralPath $ProjectInventoryPath -Raw | ConvertFrom-Json
        $index = 0
        foreach ($project in $projectInventory.Projects) {
            foreach ($candidate in $project.CacheCandidates) {
                $index++
                $class = if ($candidate.Class -eq 'SAFE_REBUILDABLE_CANDIDATE') { 'REVIEW_REQUIRED' } else { 'REVIEW_REQUIRED' }
                Add-InventoryItem -Id ("project-cache-{0:d4}" -f $index) -Path $candidate.Path -Owner $project.Root -Class $class -Action 'project-semantic-review' -Recovery 'Use the project manifest and lockfile to regenerate' -KnownBytes ([int64]$candidate.Bytes)
            }
        }
    }
    catch { $errors.Add("Project inventory :: $($_.Exception.Message)") }
}

$result = [pscustomobject]@{
    CapturedAt = (Get-Date).ToString('o')
    ComputerName = $env:COMPUTERNAME
    Measurement = 'logical-file-length; reparse-points-skipped-by-directory-measurer'
    Volumes = $volumes
    Items = @($items | Sort-Object Bytes -Descending | ForEach-Object { $_ })
    Errors = @($errors | ForEach-Object { $_ })
}

$json = $result | ConvertTo-Json -Depth 10
if ($OutputPath) {
    $parent = Split-Path -Parent $OutputPath
    if ($parent -and -not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    [System.IO.File]::WriteAllText($OutputPath, $json, (New-Object System.Text.UTF8Encoding($false)))
}
$json
