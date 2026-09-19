[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateNotNullOrEmpty()]
    [string]$ProjectRoot = (Get-Location).Path,

    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'

function Get-PropertyValue {
    param(
        [AllowNull()]$Object,
        [Parameter(Mandatory = $true)][string]$Name
    )

    if ($null -eq $Object) { return $null }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Get-DependencyVersion {
    param(
        [AllowNull()]$Package,
        [Parameter(Mandatory = $true)][string]$Name
    )

    foreach ($sectionName in @('dependencies', 'devDependencies', 'optionalDependencies')) {
        $section = Get-PropertyValue -Object $Package -Name $sectionName
        $value = Get-PropertyValue -Object $section -Name $Name
        if ($null -ne $value) { return [string]$value }
    }
    return $null
}

function Get-RelativeProjectPath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Path
    )

    $rootUri = New-Object System.Uri(([System.IO.Path]::GetFullPath($Root).TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar))
    $pathUri = New-Object System.Uri([System.IO.Path]::GetFullPath($Path))
    return [System.Uri]::UnescapeDataString($rootUri.MakeRelativeUri($pathUri).ToString()).Replace('/', '\\')
}

function Get-ProjectFiles {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [string[]]$Extensions = @(),
        [string[]]$Names = @()
    )

    $skipNames = @('.git', 'node_modules', '.venv', 'venv', 'dist', 'build', 'release', 'out', 'target', '.next')
    $resolvedRoot = [System.IO.Path]::GetFullPath($Root).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    $rootPrefix = $resolvedRoot + [System.IO.Path]::DirectorySeparatorChar
    $visitedDirectories = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    $files = New-Object System.Collections.Generic.List[System.IO.FileInfo]
    $directories = New-Object System.Collections.Generic.Queue[System.IO.DirectoryInfo]
    $directories.Enqueue((New-Object System.IO.DirectoryInfo($resolvedRoot)))

    while ($directories.Count -gt 0) {
        $directory = $directories.Dequeue()
        try {
            $directoryPath = [System.IO.Path]::GetFullPath($directory.FullName)
            if (-not ($directoryPath.Equals($resolvedRoot, [System.StringComparison]::OrdinalIgnoreCase) -or $directoryPath.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase))) {
                continue
            }
            if (($directory.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                continue
            }
            if (-not $visitedDirectories.Add($directoryPath)) {
                continue
            }
            foreach ($childDirectory in $directory.GetDirectories()) {
                $childPath = [System.IO.Path]::GetFullPath($childDirectory.FullName)
                $insideRoot = $childPath.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)
                $isReparsePoint = (($childDirectory.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)
                if ($skipNames -notcontains $childDirectory.Name -and $insideRoot -and -not $isReparsePoint) {
                    $directories.Enqueue($childDirectory)
                }
            }
            foreach ($file in $directory.GetFiles()) {
                $filePath = [System.IO.Path]::GetFullPath($file.FullName)
                $insideRoot = $filePath.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)
                $isReparsePoint = (($file.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)
                if (-not $insideRoot -or $isReparsePoint) {
                    continue
                }
                $extensionMatches = $Extensions.Count -eq 0 -or $Extensions -contains $file.Extension.ToLowerInvariant()
                $nameMatches = $Names.Count -eq 0 -or $Names -contains $file.Name
                if ($extensionMatches -and $nameMatches) {
                    $files.Add($file)
                }
            }
        }
        catch [System.UnauthorizedAccessException] {
            continue
        }
        catch [System.IO.IOException] {
            continue
        }
    }

    return @($files)
}

function Invoke-ReadOnlyGit {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    $git = Get-Command git -ErrorAction SilentlyContinue
    if ($null -eq $git) {
        return [pscustomobject]@{ available = $false; exitCode = $null; output = @() }
    }

    $priorOptionalLocks = $env:GIT_OPTIONAL_LOCKS
    try {
        $env:GIT_OPTIONAL_LOCKS = '0'
        $output = @(& $git.Source --no-optional-locks -c core.fsmonitor=false -C $Root @Arguments 2>$null)
        $exitCode = $LASTEXITCODE
    }
    finally {
        if ($null -eq $priorOptionalLocks) {
            Remove-Item Env:\GIT_OPTIONAL_LOCKS -ErrorAction SilentlyContinue
        }
        else {
            $env:GIT_OPTIONAL_LOCKS = $priorOptionalLocks
        }
    }
    return [pscustomobject]@{ available = $true; exitCode = $exitCode; output = $output }
}

$resolvedProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
if (-not (Test-Path -LiteralPath $resolvedProjectRoot -PathType Container)) {
    throw "ProjectRoot does not exist or is not a directory: $resolvedProjectRoot"
}

$warnings = New-Object System.Collections.Generic.List[string]
$signals = New-Object System.Collections.Generic.List[string]
$adapters = New-Object System.Collections.Generic.List[string]
$stackCandidates = New-Object System.Collections.Generic.List[string]

$packagePath = Join-Path $resolvedProjectRoot 'package.json'
$package = $null
$packageReadError = $null
if (Test-Path -LiteralPath $packagePath -PathType Leaf) {
    try {
        $package = Get-Content -LiteralPath $packagePath -Raw | ConvertFrom-Json
    }
    catch {
        $packageReadError = $_.Exception.Message
        $warnings.Add('package.json exists but could not be parsed as JSON.')
    }
}

$electronVersion = Get-DependencyVersion -Package $package -Name 'electron'
$electronBuilderVersion = Get-DependencyVersion -Package $package -Name 'electron-builder'
$tauriCliVersion = Get-DependencyVersion -Package $package -Name '@tauri-apps/cli'
$buildConfig = Get-PropertyValue -Object $package -Name 'build'
$buildConfigText = if ($null -ne $buildConfig) { $buildConfig | ConvertTo-Json -Depth 20 -Compress } else { '' }
$scripts = Get-PropertyValue -Object $package -Name 'scripts'
$scriptsText = if ($null -ne $scripts) { $scripts | ConvertTo-Json -Depth 20 -Compress } else { '' }

$isElectron = ($null -ne $electronVersion) -or ($null -ne $electronBuilderVersion) -or ($scriptsText -match '(?i)electron-builder')
$isNsis = $isElectron -and (($buildConfigText -match '(?i)\bnsis\b') -or ($scriptsText -match '(?i)\bnsis\b'))
if ($isElectron) {
    $stackCandidates.Add('electron')
    $signals.Add('electron dependency or build command detected')
    if ($isNsis) {
        $adapters.Add('electron-nsis')
        $signals.Add('electron-builder NSIS target detected')
    }
    else {
        $adapters.Add('electron')
    }
}

$tauriConfigCandidates = @(
    (Join-Path $resolvedProjectRoot 'tauri.conf.json'),
    (Join-Path $resolvedProjectRoot 'tauri.conf.json5'),
    (Join-Path $resolvedProjectRoot 'src-tauri\\tauri.conf.json'),
    (Join-Path $resolvedProjectRoot 'src-tauri\\tauri.conf.json5')
)
$hasTauriConfig = @($tauriConfigCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf }).Count -gt 0
$hasTauriCargo = Test-Path -LiteralPath (Join-Path $resolvedProjectRoot 'src-tauri\\Cargo.toml') -PathType Leaf
if ($hasTauriConfig -or $hasTauriCargo -or ($null -ne $tauriCliVersion)) {
    $stackCandidates.Add('tauri')
    $adapters.Add('tauri')
    $signals.Add('Tauri configuration, Cargo manifest, or CLI dependency detected')
}

$specFiles = Get-ProjectFiles -Root $resolvedProjectRoot -Extensions @('.spec')
$pyprojectPath = Join-Path $resolvedProjectRoot 'pyproject.toml'
$requirementsPath = Join-Path $resolvedProjectRoot 'requirements.txt'
$isPyInstaller = $specFiles.Count -gt 0
if (-not $isPyInstaller -and (Test-Path -LiteralPath $pyprojectPath -PathType Leaf)) {
    $pyprojectText = Get-Content -LiteralPath $pyprojectPath -Raw
    $isPyInstaller = $pyprojectText -match '(?im)^\s*pyinstaller\s*[<=>]'
}
if (-not $isPyInstaller -and (Test-Path -LiteralPath $requirementsPath -PathType Leaf)) {
    $requirementsText = Get-Content -LiteralPath $requirementsPath -Raw
    $isPyInstaller = $requirementsText -match '(?im)^\s*pyinstaller\s*([<=>]|$)'
}
if ($isPyInstaller) {
    $stackCandidates.Add('pyinstaller')
    $adapters.Add('pyinstaller')
    $signals.Add('PyInstaller spec or dependency detected')
}

$csprojFiles = Get-ProjectFiles -Root $resolvedProjectRoot -Extensions @('.csproj')
$slnFiles = Get-ProjectFiles -Root $resolvedProjectRoot -Extensions @('.sln')
$wixFiles = Get-ProjectFiles -Root $resolvedProjectRoot -Extensions @('.wxs')
$msixFiles = Get-ProjectFiles -Root $resolvedProjectRoot -Names @('Package.appxmanifest', 'AppxManifest.xml')
$isDotnet = $csprojFiles.Count -gt 0 -or $slnFiles.Count -gt 0
if ($isDotnet) {
    $stackCandidates.Add('dotnet')
    if ($wixFiles.Count -gt 0) { $adapters.Add('dotnet-wix') }
    if ($msixFiles.Count -gt 0) { $adapters.Add('dotnet-msix') }
    $signals.Add('.NET project file detected')
}

$lockfileNames = @('pnpm-lock.yaml', 'package-lock.json', 'yarn.lock', 'Cargo.lock', 'poetry.lock', 'uv.lock', 'packages.lock.json')
$lockfiles = New-Object System.Collections.Generic.List[object]
foreach ($lockfileName in $lockfileNames) {
    $lockfilePath = Join-Path $resolvedProjectRoot $lockfileName
    if (Test-Path -LiteralPath $lockfilePath -PathType Leaf) {
        $lockfiles.Add([pscustomobject]@{
            path = Get-RelativeProjectPath -Root $resolvedProjectRoot -Path $lockfilePath
            sizeBytes = (Get-Item -LiteralPath $lockfilePath).Length
            textHashEligible = $true
        })
    }
}

$packageManager = $null
$packageManagerProperty = Get-PropertyValue -Object $package -Name 'packageManager'
if ($null -ne $packageManagerProperty) {
    $packageManager = ([string]$packageManagerProperty -split '@', 2)[0]
}
if ([string]::IsNullOrWhiteSpace($packageManager)) {
    if (Test-Path -LiteralPath (Join-Path $resolvedProjectRoot 'pnpm-lock.yaml')) { $packageManager = 'pnpm' }
    elseif (Test-Path -LiteralPath (Join-Path $resolvedProjectRoot 'package-lock.json')) { $packageManager = 'npm' }
    elseif (Test-Path -LiteralPath (Join-Path $resolvedProjectRoot 'yarn.lock')) { $packageManager = 'yarn' }
    elseif (Test-Path -LiteralPath (Join-Path $resolvedProjectRoot 'Cargo.lock')) { $packageManager = 'cargo' }
}

$nativeModuleNames = @('better-sqlite3', 'sqlite3', 'sharp', 'canvas', 'node-gyp', 'node-pre-gyp', 'ffi-napi', 'keytar')
$nativeModules = New-Object System.Collections.Generic.List[string]
foreach ($name in $nativeModuleNames) {
    if ($null -ne (Get-DependencyVersion -Package $package -Name $name)) {
        $nativeModules.Add($name)
    }
}

$workflowRoot = Join-Path $resolvedProjectRoot '.github\\workflows'
$workflows = New-Object System.Collections.Generic.List[object]
if (Test-Path -LiteralPath $workflowRoot -PathType Container) {
    foreach ($workflow in Get-ChildItem -LiteralPath $workflowRoot -File -ErrorAction Stop | Where-Object { $_.Extension -in @('.yml', '.yaml') }) {
        $workflows.Add([pscustomobject]@{
            path = Get-RelativeProjectPath -Root $resolvedProjectRoot -Path $workflow.FullName
            sizeBytes = $workflow.Length
        })
    }
}

$gitRoot = Invoke-ReadOnlyGit -Root $resolvedProjectRoot -Arguments @('rev-parse', '--show-toplevel')
$gitCommit = Invoke-ReadOnlyGit -Root $resolvedProjectRoot -Arguments @('rev-parse', 'HEAD')
$gitBranch = Invoke-ReadOnlyGit -Root $resolvedProjectRoot -Arguments @('branch', '--show-current')
$gitStatus = Invoke-ReadOnlyGit -Root $resolvedProjectRoot -Arguments @('status', '--porcelain=v1')
$gitInfo = [ordered]@{
    available = $gitRoot.available
    repositoryRoot = if ($gitRoot.exitCode -eq 0) { [string]($gitRoot.output | Select-Object -First 1) } else { $null }
    commit = if ($gitCommit.exitCode -eq 0) { [string]($gitCommit.output | Select-Object -First 1) } else { $null }
    branch = if ($gitBranch.exitCode -eq 0) { [string]($gitBranch.output | Select-Object -First 1) } else { $null }
    dirty = if ($gitStatus.exitCode -eq 0) { @($gitStatus.output).Count -gt 0 } else { $null }
}

$uniqueStacks = @($stackCandidates | Select-Object -Unique)
$primaryStack = if ($uniqueStacks.Count -eq 0) { 'unknown' } elseif ($uniqueStacks.Count -eq 1) { $uniqueStacks[0] } else { 'mixed' }
if ($primaryStack -eq 'unknown') {
    $warnings.Add('No supported desktop stack was detected; inspect project configuration before selecting a workflow template.')
}
if ($primaryStack -eq 'mixed') {
    $warnings.Add('Multiple desktop stack signals were detected; select one release surface before changing workflows.')
}
if ($packageReadError) {
    $warnings.Add('Package parsing error: ' + $packageReadError)
}

$packageJsonRelativePath = $null
if (Test-Path -LiteralPath $packagePath -PathType Leaf) {
    $packageJsonRelativePath = 'package.json'
}

$result = [ordered]@{
    schemaVersion = 1
    scanMode = 'read-only'
    scannedAtUtc = [DateTime]::UtcNow.ToString('o')
    projectRoot = $resolvedProjectRoot
    git = $gitInfo
    detection = [ordered]@{
        primaryStack = $primaryStack
        stackCandidates = $uniqueStacks
        adapters = @($adapters | Select-Object -Unique)
        signals = @($signals | Select-Object -Unique)
        requiresOfficialDocumentationCheck = $true
    }
    package = [ordered]@{
        packageJson = $packageJsonRelativePath
        packageManager = $packageManager
        electron = $electronVersion
        electronBuilder = $electronBuilderVersion
        tauriCli = $tauriCliVersion
        nativeModuleSignals = @($nativeModules)
    }
    lockfiles = $lockfiles.ToArray()
    workflows = $workflows.ToArray()
    files = [ordered]@{
        pyInstallerSpecs = @($specFiles | ForEach-Object { Get-RelativeProjectPath -Root $resolvedProjectRoot -Path $_.FullName })
        dotnetProjects = @($csprojFiles | ForEach-Object { Get-RelativeProjectPath -Root $resolvedProjectRoot -Path $_.FullName })
        solutions = @($slnFiles | ForEach-Object { Get-RelativeProjectPath -Root $resolvedProjectRoot -Path $_.FullName })
        wixSources = @($wixFiles | ForEach-Object { Get-RelativeProjectPath -Root $resolvedProjectRoot -Path $_.FullName })
        msixManifests = @($msixFiles | ForEach-Object { Get-RelativeProjectPath -Root $resolvedProjectRoot -Path $_.FullName })
    }
    warnings = @($warnings)
}

$json = $result | ConvertTo-Json -Depth 12
if (-not [string]::IsNullOrWhiteSpace($OutputPath)) {
    $resolvedOutputPath = [System.IO.Path]::GetFullPath($OutputPath)
    $outputDirectory = [System.IO.Path]::GetDirectoryName($resolvedOutputPath)
    if (-not [string]::IsNullOrWhiteSpace($outputDirectory)) {
        [System.IO.Directory]::CreateDirectory($outputDirectory) | Out-Null
    }
    [System.IO.File]::WriteAllText($resolvedOutputPath, $json + [Environment]::NewLine, (New-Object System.Text.UTF8Encoding($false)))
}

Write-Output $json
Set-Variable -Name LASTEXITCODE -Scope Global -Value 0
