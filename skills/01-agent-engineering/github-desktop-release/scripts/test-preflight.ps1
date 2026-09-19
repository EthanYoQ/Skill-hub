[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Assert-Condition {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if (-not $Condition) { throw "Assertion failed: $Message" }
}

function Write-FixtureFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )

    $directory = [System.IO.Path]::GetDirectoryName($Path)
    [System.IO.Directory]::CreateDirectory($directory) | Out-Null
    [System.IO.File]::WriteAllText($Path, $Content, (New-Object System.Text.UTF8Encoding($false)))
}

function Invoke-PreflightJson {
    param(
        [Parameter(Mandatory = $true)][string]$ScriptPath,
        [Parameter(Mandatory = $true)][string]$ProjectRoot,
        [string]$OutputPath
    )

    $lines = if ([string]::IsNullOrWhiteSpace($OutputPath)) {
        @(& $ScriptPath -ProjectRoot $ProjectRoot)
    }
    else {
        @(& $ScriptPath -ProjectRoot $ProjectRoot -OutputPath $OutputPath)
    }
    if ($LASTEXITCODE -ne 0) { throw "Preflight exited with code $LASTEXITCODE" }
    return (($lines -join [Environment]::NewLine) | ConvertFrom-Json)
}

function Get-TreeFingerprint {
    param([Parameter(Mandatory = $true)][string]$Root)

    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd([System.IO.Path]::DirectorySeparatorChar)
    $prefix = $rootFull + [System.IO.Path]::DirectorySeparatorChar
    return @(
        Get-ChildItem -LiteralPath $rootFull -Force -Recurse -File | ForEach-Object {
            $relative = $_.FullName.Substring($prefix.Length).Replace('\', '/')
            '{0}|{1}|{2}' -f $relative, $_.Length, (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        } | Sort-Object
    )
}

function Initialize-TestGitRepository {
    param([Parameter(Mandatory = $true)][string]$Root)

    $git = Get-Command git -ErrorAction SilentlyContinue
    if ($null -eq $git) { throw 'git is required for the no-write preflight test.' }
    foreach ($arguments in @(
        @('init', '--quiet'),
        @('config', 'user.email', 'fixture@example.invalid'),
        @('config', 'user.name', 'Windows Cloud Release Fixture'),
        @('add', '--all'),
        @('commit', '--quiet', '--no-gpg-sign', '-m', 'fixture')
    )) {
        & $git.Source -C $Root @arguments
        if ($LASTEXITCODE -ne 0) { throw "git $($arguments -join ' ') failed with $LASTEXITCODE" }
    }
    return $git.Source
}

$scriptRoot = [System.IO.Path]::GetDirectoryName($PSCommandPath)
$preflight = Join-Path $scriptRoot 'preflight-windows-release.ps1'
$temporaryRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('windows-cloud-release-preflight-' + [Guid]::NewGuid().ToString('N'))
$temporaryRootFull = [System.IO.Path]::GetFullPath($temporaryRoot)
$temporaryBaseFull = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$junctions = New-Object System.Collections.Generic.List[string]

if (-not $temporaryRootFull.StartsWith($temporaryBaseFull, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Refusing to create a test fixture outside the system temporary directory.'
}

try {
    [System.IO.Directory]::CreateDirectory($temporaryRootFull) | Out-Null

    $electronRoot = Join-Path $temporaryRootFull 'electron-nsis'
    Write-FixtureFile -Path (Join-Path $electronRoot 'package.json') -Content @'
{
  "name": "fixture-electron",
  "packageManager": "pnpm@9.15.0",
  "scripts": { "build:win": "electron-builder --win nsis" },
  "devDependencies": {
    "electron": "31.0.0",
    "electron-builder": "25.1.0",
    "better-sqlite3": "11.0.0"
  },
  "build": { "win": { "target": ["nsis"] } }
}
'@
    Write-FixtureFile -Path (Join-Path $electronRoot 'pnpm-lock.yaml') -Content ("lockfileVersion: '9.0'" + [Environment]::NewLine)
    Write-FixtureFile -Path (Join-Path $electronRoot '.github\workflows\release.yml') -Content ("name: fixture" + [Environment]::NewLine)
    $gitPath = Initialize-TestGitRepository -Root $electronRoot

    $hookSentinel = Join-Path $temporaryRootFull 'hook-invoked.txt'
    $preCommitHook = Join-Path $electronRoot '.git\hooks\pre-commit'
    Write-FixtureFile -Path $preCommitHook -Content '@echo invoked > "%WCR_TEST_HOOK_SENTINEL%"'
    $fsmonitorHook = Join-Path $electronRoot '.git\hooks\fsmonitor-test.cmd'
    Write-FixtureFile -Path $fsmonitorHook -Content '@echo invoked > "%WCR_TEST_HOOK_SENTINEL%"'
    & $gitPath -C $electronRoot config core.fsmonitor $fsmonitorHook
    if ($LASTEXITCODE -ne 0) { throw 'Unable to configure the fixture fsmonitor hook.' }

    $beforeFiles = Get-TreeFingerprint -Root $electronRoot
    $priorHookSentinel = $env:WCR_TEST_HOOK_SENTINEL
    $env:WCR_TEST_HOOK_SENTINEL = $hookSentinel
    try {
        $electron = Invoke-PreflightJson -ScriptPath $preflight -ProjectRoot $electronRoot
    }
    finally {
        if ($null -eq $priorHookSentinel) {
            Remove-Item Env:\WCR_TEST_HOOK_SENTINEL -ErrorAction SilentlyContinue
        }
        else {
            $env:WCR_TEST_HOOK_SENTINEL = $priorHookSentinel
        }
    }
    $afterFiles = Get-TreeFingerprint -Root $electronRoot
    Assert-Condition -Condition ($electron.scanMode -eq 'read-only') -Message 'Electron scan must report read-only mode.'
    Assert-Condition -Condition ($electron.detection.primaryStack -eq 'electron') -Message 'Electron fixture must select electron.'
    Assert-Condition -Condition (@($electron.detection.adapters) -contains 'electron-nsis') -Message 'Electron fixture must select electron-nsis only from explicit NSIS evidence.'
    Assert-Condition -Condition ($electron.package.packageManager -eq 'pnpm') -Message 'Electron fixture must detect pnpm.'
    Assert-Condition -Condition (@($electron.package.nativeModuleSignals) -contains 'better-sqlite3') -Message 'Electron fixture must expose native module signal.'
    Assert-Condition -Condition (@($electron.lockfiles | Where-Object { $_.path -eq 'pnpm-lock.yaml' }).Count -eq 1) -Message 'Electron fixture must report lockfile metadata as JSON.'
    $workflowRecords = @($electron.workflows)
    Assert-Condition -Condition ($workflowRecords.Count -eq 1 -and [int64]$workflowRecords[0].sizeBytes -gt 0) -Message 'Electron fixture must report workflow metadata as JSON.'
    Assert-Condition -Condition (($beforeFiles -join [Environment]::NewLine) -eq ($afterFiles -join [Environment]::NewLine)) -Message 'Default preflight must not modify the project tree or .git contents.'
    Assert-Condition -Condition (-not (Test-Path -LiteralPath $hookSentinel)) -Message 'Default preflight must not invoke git hooks or the configured fsmonitor command.'

    $outputPath = Join-Path $temporaryRootFull 'evidence\preflight.json'
    $electronWithOutput = Invoke-PreflightJson -ScriptPath $preflight -ProjectRoot $electronRoot -OutputPath $outputPath
    Assert-Condition -Condition (Test-Path -LiteralPath $outputPath -PathType Leaf) -Message 'Explicit OutputPath must create a JSON file.'
    $saved = Get-Content -LiteralPath $outputPath -Raw | ConvertFrom-Json
    Assert-Condition -Condition ($saved.detection.primaryStack -eq $electronWithOutput.detection.primaryStack) -Message 'Saved JSON must match stdout report.'

    $electronWinOnlyRoot = Join-Path $temporaryRootFull 'electron-win-only'
    Write-FixtureFile -Path (Join-Path $electronWinOnlyRoot 'package.json') -Content @'
{
  "devDependencies": { "electron": "31.0.0", "electron-builder": "25.1.0" },
  "scripts": { "build:win": "electron-builder --win" }
}
'@
    $electronWinOnly = Invoke-PreflightJson -ScriptPath $preflight -ProjectRoot $electronWinOnlyRoot
    Assert-Condition -Condition (@($electronWinOnly.detection.adapters) -contains 'electron') -Message 'Electron --win fixture must retain the generic Electron adapter.'
    Assert-Condition -Condition (-not (@($electronWinOnly.detection.adapters) -contains 'electron-nsis')) -Message 'Electron --win alone must not select electron-nsis.'

    $tauriRoot = Join-Path $temporaryRootFull 'tauri'
    Write-FixtureFile -Path (Join-Path $tauriRoot 'package.json') -Content '{ "devDependencies": { "@tauri-apps/cli": "2.0.0" } }'
    Write-FixtureFile -Path (Join-Path $tauriRoot 'src-tauri\Cargo.toml') -Content ("[package]" + [Environment]::NewLine + "name = 'fixture'" + [Environment]::NewLine)
    Write-FixtureFile -Path (Join-Path $tauriRoot 'src-tauri\tauri.conf.json') -Content '{ "bundle": { "active": true } }'
    $tauri = Invoke-PreflightJson -ScriptPath $preflight -ProjectRoot $tauriRoot
    Assert-Condition -Condition ($tauri.detection.primaryStack -eq 'tauri') -Message 'Tauri fixture must select tauri.'
    Assert-Condition -Condition (-not (@($tauri.detection.adapters) -contains 'electron-nsis')) -Message 'Tauri fixture must not inherit Electron/NSIS adapter.'

    $pythonRoot = Join-Path $temporaryRootFull 'pyinstaller'
    Write-FixtureFile -Path (Join-Path $pythonRoot 'app.spec') -Content '# PyInstaller spec fixture'
    Write-FixtureFile -Path (Join-Path $pythonRoot 'requirements.txt') -Content ('PyInstaller==6.0' + [Environment]::NewLine)
    $python = Invoke-PreflightJson -ScriptPath $preflight -ProjectRoot $pythonRoot
    Assert-Condition -Condition ($python.detection.primaryStack -eq 'pyinstaller') -Message 'PyInstaller fixture must select pyinstaller.'

    $dotnetPlainRoot = Join-Path $temporaryRootFull 'dotnet-plain'
    Write-FixtureFile -Path (Join-Path $dotnetPlainRoot 'App.csproj') -Content '<Project Sdk="Microsoft.NET.Sdk"></Project>'
    $dotnetPlain = Invoke-PreflightJson -ScriptPath $preflight -ProjectRoot $dotnetPlainRoot
    Assert-Condition -Condition ($dotnetPlain.detection.primaryStack -eq 'dotnet') -Message 'Plain .NET fixture must identify the .NET stack.'
    Assert-Condition -Condition (@($dotnetPlain.detection.adapters).Count -eq 0) -Message 'Plain .csproj must not select a .NET installer adapter.'

    $dotnetRoot = Join-Path $temporaryRootFull 'dotnet-installer'
    Write-FixtureFile -Path (Join-Path $dotnetRoot 'App.csproj') -Content '<Project Sdk="Microsoft.NET.Sdk"></Project>'
    Write-FixtureFile -Path (Join-Path $dotnetRoot 'installer\Product.wxs') -Content '<Wix></Wix>'
    Write-FixtureFile -Path (Join-Path $dotnetRoot 'installer\Package.appxmanifest') -Content '<Package></Package>'
    $dotnet = Invoke-PreflightJson -ScriptPath $preflight -ProjectRoot $dotnetRoot
    Assert-Condition -Condition ($dotnet.detection.primaryStack -eq 'dotnet') -Message '.NET fixture must select dotnet.'
    Assert-Condition -Condition (@($dotnet.detection.adapters) -contains 'dotnet-wix') -Message '.NET fixture must find WiX.'
    Assert-Condition -Condition (@($dotnet.detection.adapters) -contains 'dotnet-msix') -Message '.NET fixture must find MSIX.'

    $reparseRoot = Join-Path $temporaryRootFull 'reparse-guard'
    $outsideRoot = Join-Path $temporaryRootFull 'outside-of-project'
    Write-FixtureFile -Path (Join-Path $reparseRoot 'App.csproj') -Content '<Project Sdk="Microsoft.NET.Sdk"></Project>'
    Write-FixtureFile -Path (Join-Path $outsideRoot 'escaped.wxs') -Content '<Wix></Wix>'
    $outsideLink = Join-Path $reparseRoot 'outside-link'
    $loopLink = Join-Path $reparseRoot 'loop-link'
    try {
        New-Item -ItemType Junction -Path $outsideLink -Target $outsideRoot -ErrorAction Stop | Out-Null
        $junctions.Add($outsideLink)
        New-Item -ItemType Junction -Path $loopLink -Target $reparseRoot -ErrorAction Stop | Out-Null
        $junctions.Add($loopLink)
    }
    catch {
        throw "The reparse-point guard requires a temporary junction fixture: $($_.Exception.Message)"
    }
    $reparse = Invoke-PreflightJson -ScriptPath $preflight -ProjectRoot $reparseRoot
    Assert-Condition -Condition (@($reparse.files.wixSources).Count -eq 0) -Message 'Preflight must not enumerate WiX sources through an outside junction.'
    Assert-Condition -Condition (-not (@($reparse.files.wixSources) -match 'outside-link|loop-link')) -Message 'Preflight must skip reparse points rather than traversing outside or looping.'

    [Console]::Out.WriteLine('{"passed":true,"fixtures":7,"checks":"git-no-write,no-hooks,electron-nsis,electron-win-negative,tauri,pyinstaller,dotnet-negative,dotnet-installer,reparse-guard,explicit-output"}')
}
finally {
    foreach ($junction in @($junctions | Sort-Object -Descending)) {
        if (Test-Path -LiteralPath $junction) {
            Remove-Item -LiteralPath $junction -Force -ErrorAction SilentlyContinue
        }
    }
    if (Test-Path -LiteralPath $temporaryRootFull) {
        Remove-Item -LiteralPath $temporaryRootFull -Recurse -Force
    }
}
