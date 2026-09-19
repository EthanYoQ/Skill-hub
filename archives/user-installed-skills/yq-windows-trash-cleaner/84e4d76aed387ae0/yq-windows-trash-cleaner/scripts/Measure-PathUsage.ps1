[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string[]]$Path,
    [string]$OutputPath
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

function Measure-LiteralTree([string]$LiteralPath) {
    $resolved = (Resolve-Path -LiteralPath $LiteralPath -ErrorAction Stop).Path
    $root = Get-Item -LiteralPath $resolved -Force -ErrorAction Stop
    $cursor = $root
    while ($cursor) {
        if ($cursor.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "Refusing to measure through a reparse-point path component: $($cursor.FullName)"
        }
        $cursor = $cursor.Parent
    }
    if (-not $root.PSIsContainer) {
        return [pscustomobject]@{Path=$resolved;Bytes=[int64]$root.Length;GiB=[math]::Round($root.Length/1GB,3);Files=1;Directories=0;SkippedReparsePoints=0;Errors=@()}
    }
    $bytes=[int64]0; $files=[int64]0; $directories=[int64]0; $skipped=[int64]0
    $errors=New-Object Collections.Generic.List[string]
    $stack=New-Object Collections.Generic.Stack[string]
    $stack.Push($resolved)
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
    [pscustomobject]@{Path=$resolved;Bytes=$bytes;GiB=[math]::Round($bytes/1GB,3);Files=$files;Directories=$directories;SkippedReparsePoints=$skipped;Errors=@($errors)}
}

$results=@($Path | ForEach-Object { Measure-LiteralTree $_ })
$document=[ordered]@{CapturedAt=(Get-Date).ToString('o');Measurement='logical-file-length';FollowedReparsePoints=$false;Results=$results}
if($OutputPath){$document|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $OutputPath -Encoding UTF8}
$document|ConvertTo-Json -Depth 8
