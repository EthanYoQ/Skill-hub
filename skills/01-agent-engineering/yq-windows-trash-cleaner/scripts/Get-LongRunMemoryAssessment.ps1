[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$SamplesPath,
    [double]$WarningPoolTotalMB = 4096,
    [double]$WarningFileFamilyMB = 1024,
    [double]$WarningSQSFMB = 256,
    [double]$WarningEtwBMB = 1024,
    [double]$MaximumGapMinutes = 90,
    [double]$RequiredHours = 48,
    [double]$MaximumPoolGrowthMBPerHour = 64,
    [double]$MaximumFileFamilyGrowthMBPerHour = 32,
    [switch]$RepresentativeWorkloadCompleted,
    [switch]$PostWorkloadObservationCompleted,
    [switch]$FunctionalGatesPassed,
    [switch]$EventLogGatesPassed
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$rows = @(Import-Csv -LiteralPath $SamplesPath)
if ($rows.Count -eq 0) { throw 'Samples file is empty.' }
foreach ($required in @('Timestamp','BootTime','PoolTotalMB','FileFamilyMB')) {
    if (-not ($rows[0].PSObject.Properties.Name -contains $required)) { throw "Missing column: $required" }
}

$bootSummaries = @()
foreach ($group in ($rows | Group-Object BootTime | Sort-Object { [datetime]$_.Name })) {
    $samples = @($group.Group | Sort-Object { [datetime]$_.Timestamp })
    $firstTime = [datetime]$samples[0].Timestamp
    $lastTime = [datetime]$samples[-1].Timestamp
    $maxGap = 0.0
    for ($index=1; $index -lt $samples.Count; $index++) {
        $gap = (([datetime]$samples[$index].Timestamp)-([datetime]$samples[$index-1].Timestamp)).TotalMinutes
        if ($gap -gt $maxGap) { $maxGap = $gap }
    }
    $warningRows = @($samples | Where-Object {
        [double]$_.PoolTotalMB -ge $WarningPoolTotalMB -or
        [double]$_.FileFamilyMB -ge $WarningFileFamilyMB -or
        (($_.PSObject.Properties.Name -contains 'SQSFMB') -and [double]$_.SQSFMB -ge $WarningSQSFMB) -or
        (($_.PSObject.Properties.Name -contains 'EtwBMB') -and [double]$_.EtwBMB -ge $WarningEtwBMB) -or
        (($_.PSObject.Properties.Name -contains 'Status') -and $_.Status -in @('WARNING','CRITICAL'))
    })
    $tail = @($samples | Select-Object -Last ([math]::Min(3,$samples.Count)))
    $tailPoolIncreasing = $tail.Count -ge 3 -and [double]$tail[0].PoolTotalMB -lt [double]$tail[1].PoolTotalMB -and [double]$tail[1].PoolTotalMB -lt [double]$tail[2].PoolTotalMB
    $tailFileIncreasing = $tail.Count -ge 3 -and [double]$tail[0].FileFamilyMB -lt [double]$tail[1].FileFamilyMB -and [double]$tail[1].FileFamilyMB -lt [double]$tail[2].FileFamilyMB
    $coverageHours = ($lastTime-$firstTime).TotalHours
    $poolGrowthRate = if ($coverageHours -gt 0) { ([double]$samples[-1].PoolTotalMB - [double]$samples[0].PoolTotalMB) / $coverageHours } else { 0.0 }
    $fileGrowthRate = if ($coverageHours -gt 0) { ([double]$samples[-1].FileFamilyMB - [double]$samples[0].FileFamilyMB) / $coverageHours } else { 0.0 }
    $bootSummaries += [pscustomobject]@{
        BootTime=$group.Name; SampleCount=$samples.Count
        CoverageHours=[math]::Round(($lastTime-$firstTime).TotalHours,2)
        MaximumGapMinutes=[math]::Round($maxGap,1)
        CoverageValid=($maxGap -le $MaximumGapMinutes)
        WarningSampleCount=$warningRows.Count
        FirstPoolTotalMB=[double]$samples[0].PoolTotalMB
        LastPoolTotalMB=[double]$samples[-1].PoolTotalMB
        MaxPoolTotalMB=[double](($samples|Measure-Object PoolTotalMB -Maximum).Maximum)
        FirstFileFamilyMB=[double]$samples[0].FileFamilyMB
        LastFileFamilyMB=[double]$samples[-1].FileFamilyMB
        MaxFileFamilyMB=[double](($samples|Measure-Object FileFamilyMB -Maximum).Maximum)
        TailPoolIncreasing=$tailPoolIncreasing
        TailFileFamilyIncreasing=$tailFileIncreasing
        PoolGrowthMBPerHour=[math]::Round($poolGrowthRate,2)
        FileFamilyGrowthMBPerHour=[math]::Round($fileGrowthRate,2)
        SustainedGrowthExceeded=($poolGrowthRate -gt $MaximumPoolGrowthMBPerHour -or $fileGrowthRate -gt $MaximumFileFamilyGrowthMBPerHour)
    }
}

$latest = $bootSummaries[-1]
$historicalWarningCount = [int](($bootSummaries | Measure-Object WarningSampleCount -Sum).Sum)
$decision = if ($latest.WarningSampleCount -gt 0 -or $latest.TailPoolIncreasing -or $latest.TailFileFamilyIncreasing -or $latest.SustainedGrowthExceeded) {
    'WARNING_REVIEW_REQUIRED'
} elseif (
    $latest.CoverageValid -and $latest.CoverageHours -ge $RequiredHours -and
    $RepresentativeWorkloadCompleted -and $PostWorkloadObservationCompleted -and
    $FunctionalGatesPassed -and $EventLogGatesPassed
) {
    'VERIFIED_FIXED'
} elseif ($historicalWarningCount -gt 0) {
    'WARNING_REVIEW_REQUIRED'
} else {
    'HEALTHY_SO_FAR_PENDING_LONG_RUN'
}

[ordered]@{
    GeneratedAt=(Get-Date).ToString('o')
    Decision=$decision
    RootCauseConclusion='ROOT_CAUSE_NOT_PROVEN_WITHOUT_REPEATABLE_COMPONENT_AB'
    VerificationGates=[ordered]@{
        RepresentativeWorkloadCompleted=[bool]$RepresentativeWorkloadCompleted
        PostWorkloadObservationCompleted=[bool]$PostWorkloadObservationCompleted
        FunctionalGatesPassed=[bool]$FunctionalGatesPassed
        EventLogGatesPassed=[bool]$EventLogGatesPassed
    }
    RequiredHours=$RequiredHours
    MaximumAllowedGapMinutes=$MaximumGapMinutes
    MaximumPoolGrowthMBPerHour=$MaximumPoolGrowthMBPerHour
    MaximumFileFamilyGrowthMBPerHour=$MaximumFileFamilyGrowthMBPerHour
    LatestBoot=$latest
    Boots=$bootSummaries
} | ConvertTo-Json -Depth 8
