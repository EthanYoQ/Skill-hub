[CmdletBinding()]
param(
    [string]$OutputDirectory,
    [string[]]$PoolTags = @('EtwB','FMfn','File','IoFE','SQSF','Ntfc','IoNm','Toke','NtfF','DAL3'),
    [int]$TopProcessCount = 20
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

if (-not [Environment]::Is64BitProcess) {
    throw 'Pool tag collection requires a 64-bit PowerShell process.'
}

if (-not ('WindowsMemoryDiskHealthNative' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class WindowsMemoryDiskHealthNative {
  [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
  public class MEMORYSTATUSEX {
    public uint dwLength = (uint)Marshal.SizeOf(typeof(MEMORYSTATUSEX));
    public uint dwMemoryLoad;
    public ulong ullTotalPhys, ullAvailPhys, ullTotalPageFile, ullAvailPageFile;
    public ulong ullTotalVirtual, ullAvailVirtual, ullAvailExtendedVirtual;
  }
  [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
  public static extern bool GlobalMemoryStatusEx([In, Out] MEMORYSTATUSEX buffer);
  [DllImport("ntdll.dll")]
  public static extern int NtQuerySystemInformation(int informationClass, IntPtr information, int length, out int returnLength);
}
'@
}

function Get-UnsignedNtStatusHex([int]$Status) {
    $bytes = [BitConverter]::GetBytes([int32]$Status)
    return ('0x{0:X8}' -f [BitConverter]::ToUInt32($bytes, 0))
}

function Get-PoolRows {
    $length = 8MB
    $pointer = [IntPtr]::Zero
    try {
        $status = -1
        for ($attempt = 0; $attempt -lt 6; $attempt++) {
            if ($pointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::FreeHGlobal($pointer) }
            $pointer = [Runtime.InteropServices.Marshal]::AllocHGlobal($length)
            $returnLength = 0
            $status = [WindowsMemoryDiskHealthNative]::NtQuerySystemInformation(22, $pointer, $length, [ref]$returnLength)
            if ($status -eq 0) { break }
            $length = if ($returnLength -gt $length) { $returnLength + 1MB } else { $length * 2 }
        }
        if ($status -ne 0) { throw "SystemPoolTagInformation failed: $(Get-UnsignedNtStatusHex $status)" }

        $count = [Runtime.InteropServices.Marshal]::ReadInt32($pointer, 0)
        $baseAddress = $pointer.ToInt64() + 8
        for ($index = 0; $index -lt $count; $index++) {
            $entry = [IntPtr]($baseAddress + 40L * $index)
            $tagBytes = New-Object byte[] 4
            [Runtime.InteropServices.Marshal]::Copy($entry, $tagBytes, 0, 4)
            $tag = [Text.Encoding]::ASCII.GetString($tagBytes)
            $pagedBytes = [uint64][Runtime.InteropServices.Marshal]::ReadInt64($entry, 16)
            $nonPagedBytes = [uint64][Runtime.InteropServices.Marshal]::ReadInt64($entry, 32)
            if ($pagedBytes -gt 0) { [pscustomobject]@{Tag=$tag;Type='Paged';Bytes=$pagedBytes;MB=[math]::Round($pagedBytes/1MB,2)} }
            if ($nonPagedBytes -gt 0) { [pscustomobject]@{Tag=$tag;Type='NonPaged';Bytes=$nonPagedBytes;MB=[math]::Round($nonPagedBytes/1MB,2)} }
        }
    }
    finally {
        if ($pointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::FreeHGlobal($pointer) }
    }
}

$now = Get-Date
$os = Get-CimInstance Win32_OperatingSystem
$memory = New-Object WindowsMemoryDiskHealthNative+MEMORYSTATUSEX
if (-not [WindowsMemoryDiskHealthNative]::GlobalMemoryStatusEx($memory)) {
    throw "GlobalMemoryStatusEx failed: $([Runtime.InteropServices.Marshal]::GetLastWin32Error())"
}

$counter = Get-Counter '\Memory\Pool Nonpaged Bytes','\Memory\Pool Paged Bytes','\Processor(_Total)\% Processor Time' -MaxSamples 1 -ErrorAction SilentlyContinue
$validCounters = @($counter.CounterSamples | Where-Object Status -eq 0)
$nonPaged = ($validCounters | Where-Object Path -like '*\memory\pool nonpaged bytes' | Select-Object -First 1).CookedValue
$paged = ($validCounters | Where-Object Path -like '*\memory\pool paged bytes' | Select-Object -First 1).CookedValue
$cpu = ($validCounters | Where-Object Path -like '*\processor(_total)*' | Select-Object -First 1).CookedValue

$poolError = $null
$poolRows = @()
try { $poolRows = @(Get-PoolRows) } catch { $poolError = $_.Exception.Message }
$tagMetrics = [ordered]@{}
foreach ($tag in $PoolTags) {
    $tagMetrics[$tag] = [math]::Round([double](($poolRows | Where-Object Tag -ieq $tag | Measure-Object MB -Sum).Sum),2)
}
$fileFamily = 0.0
foreach ($tag in @('FMfn','File','IoFE')) { if ($tagMetrics.Contains($tag)) { $fileFamily += [double]$tagMetrics[$tag] } }

$processes = @(Get-Process -ErrorAction SilentlyContinue)
$topProcesses = @($processes | Sort-Object PrivateMemorySize64 -Descending | Select-Object -First $TopProcessCount | ForEach-Object {
    [pscustomobject]@{
        Name=$_.ProcessName; Id=$_.Id
        WorkingSetMB=[math]::Round($_.WorkingSet64/1MB,2)
        PrivateMB=[math]::Round($_.PrivateMemorySize64/1MB,2)
        CPUSeconds=if ($null -eq $_.CPU) {$null} else {[math]::Round([double]$_.CPU,2)}
    }
})

$volume = Get-Volume -DriveLetter C -ErrorAction SilentlyContinue
$fastStartup = (Get-ItemProperty -LiteralPath 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Power' -Name HiberbootEnabled -ErrorAction SilentlyContinue).HiberbootEnabled
$snapshot = [ordered]@{
    CapturedAt=$now.ToString('o')
    BootTime=([datetime]$os.LastBootUpTime).ToString('o')
    UptimeHours=[math]::Round(($now-[datetime]$os.LastBootUpTime).TotalHours,2)
    Memory=[ordered]@{
        TotalGB=[math]::Round($memory.ullTotalPhys/1GB,2)
        AvailableGB=[math]::Round($memory.ullAvailPhys/1GB,2)
        UsedPercent=[double]$memory.dwMemoryLoad
        ProcessWorkingSetGB=[math]::Round([double](($processes|Measure-Object WorkingSet64 -Sum).Sum)/1GB,2)
        ProcessPrivateGB=[math]::Round([double](($processes|Measure-Object PrivateMemorySize64 -Sum).Sum)/1GB,2)
        PoolNonPagedMB=if($null -eq $nonPaged){$null}else{[math]::Round($nonPaged/1MB,2)}
        PoolPagedMB=if($null -eq $paged){$null}else{[math]::Round($paged/1MB,2)}
        PoolTotalMB=if($null -eq $nonPaged -or $null -eq $paged){$null}else{[math]::Round(($nonPaged+$paged)/1MB,2)}
        PoolTags=$tagMetrics
        FileFamilyMB=[math]::Round($fileFamily,2)
        PoolTagError=$poolError
    }
    CPUPercent=if($null -eq $cpu){$null}else{[math]::Round($cpu,2)}
    CDrive=if($volume){[ordered]@{SizeGB=[math]::Round($volume.Size/1GB,2);FreeGB=[math]::Round($volume.SizeRemaining/1GB,2)}}else{$null}
    HiberbootEnabled=$fastStartup
    TopProcesses=$topProcesses
}

if ($OutputDirectory) {
    New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
    $stamp = $now.ToString('yyyyMMdd-HHmmss')
    $snapshot | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $OutputDirectory "snapshot-$stamp.json") -Encoding UTF8
    $poolRows | Sort-Object Bytes -Descending | Select-Object -First 100 | Export-Csv -LiteralPath (Join-Path $OutputDirectory "pool-tags-$stamp.csv") -NoTypeInformation -Encoding UTF8
}
$snapshot | ConvertTo-Json -Depth 10
