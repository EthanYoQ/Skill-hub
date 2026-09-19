[CmdletBinding()]
param(
    [ValidateSet('Inventory', 'Validate')]
    [string]$Mode = 'Inventory',
    [ValidateSet('All', '1', '2', '3')]
    [string]$Batch = 'All'
)

$ErrorActionPreference = 'Stop'
$registryPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'references\tool-registry.json'

if (-not (Test-Path -LiteralPath $registryPath)) {
    throw "Missing tool registry: $registryPath"
}

$registry = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json
$tools = @($registry.tools)

function Resolve-ToolCommand([string]$Name) {
    $preferredPath = Join-Path $env:USERPROFILE (".local\\bin\\$Name.exe")
    if (Test-Path -LiteralPath $preferredPath) {
        return [PSCustomObject]@{ Definition = $preferredPath; CommandType = 'Application' }
    }

    $commands = @(Get-Command $Name -All -ErrorAction SilentlyContinue)
    $application = $commands | Where-Object CommandType -eq 'Application' | Select-Object -First 1
    if ($application) {
        return $application
    }

    return $commands | Select-Object -First 1
}

if ($tools.Count -ne 15) {
    throw "The fixed registry must contain exactly 15 tools; found $($tools.Count)."
}

if (@($tools.id | Select-Object -Unique).Count -ne $tools.Count) {
    throw 'Every registry tool id must be unique.'
}

if ($Mode -eq 'Validate') {
    $tools |
        Group-Object group |
        Sort-Object Name |
        ForEach-Object {
            [PSCustomObject]@{
                Group = $_.Name
                Tools = ($_.Group.name -join ', ')
                Count = $_.Count
            }
        } |
        Format-Table -AutoSize
    return
}

$selected = if ($Batch -eq 'All') { $tools } else { @($tools | Where-Object group -eq $Batch) }

foreach ($tool in $selected) {
    $command = Resolve-ToolCommand $tool.executable
    if (-not $command) {
        [PSCustomObject]@{
            Group = $tool.group
            Tool = $tool.name
            State = 'Not installed'
            Version = ''
            Source = $tool.source
            Next = $tool.updateStrategy
            Risk = $tool.risk
        }
        continue
    }

    try {
        $probe = if ($tool.versionCommand) { Resolve-ToolCommand $tool.versionCommand.executable } else { $command }
        if (-not $probe) {
            throw "Version probe command is unavailable for $($tool.name)."
        }

        if ($tool.versionCommand) {
            $probeArgs = @($tool.versionCommand.args)
        } else {
            $probeArgs = @($tool.versionArgs)
        }
        $global:LASTEXITCODE = 0
        $output = & ($probe.Definition) @probeArgs 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Version probe exited with code $LASTEXITCODE."
        }

        if ($tool.versionCommand -and $tool.versionCommand.match) {
            $match = @($output | Where-Object { "$_" -match $tool.versionCommand.match } | Select-Object -First 1)
            if (-not $match) {
                throw "Version probe did not return a matching version entry for $($tool.name)."
            }
            $version = $match[0].ToString().Trim()
        } else {
            $version = (($output | Select-Object -First 2) -join ' ').Trim()
        }
        [PSCustomObject]@{
            Group = $tool.group
            Tool = $tool.name
            State = 'Installed'
            Version = $version
            Source = $tool.source
            Next = $tool.updateStrategy
            Risk = $tool.risk
        }
    } catch {
        [PSCustomObject]@{
            Group = $tool.group
            Tool = $tool.name
            State = 'Probe failed'
            Version = $_.Exception.Message
            Source = $tool.source
            Next = $tool.updateStrategy
            Risk = $tool.risk
        }
    }
}
