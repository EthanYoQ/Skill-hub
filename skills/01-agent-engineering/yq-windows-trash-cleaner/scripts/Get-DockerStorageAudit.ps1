[CmdletBinding()]
param(
    [string[]]$VhdxPath = @(
        (Join-Path $env:LOCALAPPDATA 'Docker\wsl\disk\docker_data.vhdx'),
        (Join-Path $env:LOCALAPPDATA 'Docker\wsl\main\ext4.vhdx')
    ),
    [string]$OutputPath
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$dockerCommand=Get-Command docker.exe -ErrorAction SilentlyContinue
$engineAvailable=$false
$engineError=$null
$systemDf=$null; $containers=@(); $images=@(); $volumes=@(); $builders=@()
if($dockerCommand) {
    $info=@(& $dockerCommand.Source info --format '{{json .}}' 2>&1)
    if($LASTEXITCODE -eq 0) {
        $engineAvailable=$true
        $systemDf=@(& $dockerCommand.Source system df -v 2>&1)
        $containers=@(& $dockerCommand.Source ps -a --no-trunc --format '{{json .}}' 2>&1)
        $images=@(& $dockerCommand.Source image ls --no-trunc --digests --format '{{json .}}' 2>&1)
        $volumeNames=@(& $dockerCommand.Source volume ls -q 2>&1)
        foreach($name in $volumeNames) {
            if([string]::IsNullOrWhiteSpace($name)){continue}
            $inspect=@(& $dockerCommand.Source volume inspect $name 2>&1)
            $mountCount=@(& $dockerCommand.Source ps -a --filter "volume=$name" -q 2>&1).Count
            $volumes += [pscustomobject]@{Name=$name;MountedContainerCount=$mountCount;Inspect=$inspect}
        }
        $builders=@(& $dockerCommand.Source buildx ls 2>&1)
    } else { $engineError=($info -join [Environment]::NewLine) }
} else { $engineError='docker.exe not found' }

$vhdx=@()
foreach($candidate in $VhdxPath | Select-Object -Unique) {
    if(Test-Path -LiteralPath $candidate) {
        $item=Get-Item -LiteralPath $candidate -Force
        $vhdx += [pscustomobject]@{
            Path=$item.FullName
            LengthBytes=[int64]$item.Length
            LengthGiB=[math]::Round($item.Length/1GB,3)
            AllocatedBytes=$null
            AllocatedBytesStatus='UNKNOWN_NOT_MEASURED'
            LastWriteTime=$item.LastWriteTime.ToString('o')
        }
    }
}

$audit=[ordered]@{
    CapturedAt=(Get-Date).ToString('o')
    ReadOnly=$true
    DockerCliFound=[bool]$dockerCommand
    EngineAvailable=$engineAvailable
    EngineError=$engineError
    SystemDf=$systemDf
    Containers=$containers
    Images=$images
    Volumes=$volumes
    Builders=$builders
    Vhdx=$vhdx
    Warning='Unmounted or dangling volumes are not automatically safe to delete.'
}
if($OutputPath){$audit|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $OutputPath -Encoding UTF8}
$audit|ConvertTo-Json -Depth 12
