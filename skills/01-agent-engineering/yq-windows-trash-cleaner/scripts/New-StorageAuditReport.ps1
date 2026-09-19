[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$StorageInventoryPath,
    [string]$ProjectInventoryPath,
    [Parameter(Mandatory = $true)][string]$OutputPath,
    [string]$Title = 'Windows storage and project health audit'
)

$ErrorActionPreference = 'Stop'

function ConvertTo-HtmlText {
    param([AllowNull()][object]$Value)
    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

function Format-Bytes {
    param([Nullable[int64]]$Bytes)
    if ($null -eq $Bytes) { return 'unknown' }
    if ($Bytes -ge 1TB) { return ('{0:N2} TiB' -f ($Bytes / 1TB)) }
    if ($Bytes -ge 1GB) { return ('{0:N2} GiB' -f ($Bytes / 1GB)) }
    if ($Bytes -ge 1MB) { return ('{0:N2} MiB' -f ($Bytes / 1MB)) }
    return ('{0:N0} bytes' -f $Bytes)
}

$storage = Get-Content -LiteralPath $StorageInventoryPath -Raw | ConvertFrom-Json
$projects = $null
if ($ProjectInventoryPath -and (Test-Path -LiteralPath $ProjectInventoryPath)) {
    $projects = Get-Content -LiteralPath $ProjectInventoryPath -Raw | ConvertFrom-Json
}

$classOrder = @('SAFE_REBUILDABLE', 'REVIEW_REQUIRED', 'KEEP_USER_OR_EVIDENCE', 'SYSTEM_MANAGED_DO_NOT_DELETE', 'ADMIN_EVIDENCE_REQUIRED')
$classLabel = @{
    SAFE_REBUILDABLE = 'Safe rebuildable candidates'
    REVIEW_REQUIRED = 'Review required'
    KEEP_USER_OR_EVIDENCE = 'Keep user work or evidence'
    SYSTEM_MANAGED_DO_NOT_DELETE = 'System managed - do not delete manually'
    ADMIN_EVIDENCE_REQUIRED = 'Administrator evidence required'
}

$volumeHtml = New-Object System.Text.StringBuilder
foreach ($volume in $storage.Volumes) {
    $used = [int64]$volume.SizeBytes - [int64]$volume.FreeBytes
    $pct = if ([int64]$volume.SizeBytes -gt 0) { [math]::Round(($used / [double]$volume.SizeBytes) * 100, 1) } else { 0 }
    [void]$volumeHtml.AppendLine("<section class='volume'><h2>$(ConvertTo-HtmlText $volume.DeviceId) $(ConvertTo-HtmlText $volume.VolumeName)</h2><p>$(ConvertTo-HtmlText (Format-Bytes $used)) used of $(ConvertTo-HtmlText (Format-Bytes ([int64]$volume.SizeBytes))); $(ConvertTo-HtmlText (Format-Bytes ([int64]$volume.FreeBytes))) free; filesystem $(ConvertTo-HtmlText $volume.FileSystem).</p><div class='bar'><span style='width:$pct%'></span></div></section>")
}

$topHtml = New-Object System.Text.StringBuilder
foreach ($item in @($storage.Items | Sort-Object Bytes -Descending | Select-Object -First 8)) {
    [void]$topHtml.AppendLine("<tr><td>$(ConvertTo-HtmlText (Format-Bytes ([int64]$item.Bytes)))</td><td>$(ConvertTo-HtmlText $item.Owner)</td><td><code>$(ConvertTo-HtmlText $item.Path)</code></td><td>$(ConvertTo-HtmlText $item.Class)</td></tr>")
}

$groupsHtml = New-Object System.Text.StringBuilder
foreach ($class in $classOrder) {
    $members = @($storage.Items | Where-Object Class -eq $class | Sort-Object Bytes -Descending)
    if ($members.Count -eq 0) { continue }
    $sum = [int64](($members | Measure-Object Bytes -Sum).Sum)
    [void]$groupsHtml.AppendLine("<details class='group $class' open><summary><strong>$(ConvertTo-HtmlText $classLabel[$class])</strong><span>$(ConvertTo-HtmlText (Format-Bytes $sum)) across $($members.Count) items</span></summary><div class='cards'>")
    foreach ($item in $members) {
        $active = if (@($item.ActiveProcesses).Count -gt 0) { 'active process match detected' } else { 'no direct process command-line match' }
        $pathBytes = [System.Text.Encoding]::UTF8.GetBytes([string]$item.Path)
        $pathForData = [Convert]::ToBase64String($pathBytes)
        [void]$groupsHtml.AppendLine(@"
<article class='item'>
  <div class='item-head'><code>$(ConvertTo-HtmlText $item.Id)</code><strong>$(ConvertTo-HtmlText (Format-Bytes ([int64]$item.Bytes)))</strong></div>
  <p class='path'>$(ConvertTo-HtmlText $item.Path)</p>
  <p><b>Owner:</b> $(ConvertTo-HtmlText $item.Owner) &middot; <b>Activity:</b> $(ConvertTo-HtmlText $active)</p>
  <p><b>Proposed action:</b> $(ConvertTo-HtmlText $item.Action)</p>
  <p><b>Recovery:</b> $(ConvertTo-HtmlText $item.Recovery)</p>
  <button type='button' class='copy-path' data-path-b64='$(ConvertTo-HtmlText $pathForData)'>Copy path</button>
</article>
"@)
    }
    [void]$groupsHtml.AppendLine('</div></details>')
}

$projectHtml = New-Object System.Text.StringBuilder
if ($projects) {
    $dirty = @($projects.Projects | Where-Object Dirty)
    $active = @($projects.Projects | Where-Object { @($_.ActiveProcesses).Count -gt 0 })
    [void]$projectHtml.AppendLine("<p>Projects discovered: $(@($projects.Projects).Count). Dirty: $($dirty.Count). With direct process matches: $($active.Count). Scan errors: $(@($projects.Errors).Count).</p>")
    [void]$projectHtml.AppendLine('<table><thead><tr><th>Root</th><th>Git</th><th>Dirty</th><th>Branch</th><th>Cache candidates</th></tr></thead><tbody>')
    foreach ($project in @($projects.Projects | Sort-Object Root)) {
        [void]$projectHtml.AppendLine("<tr><td><code>$(ConvertTo-HtmlText $project.Root)</code></td><td>$(ConvertTo-HtmlText $project.IsGit)</td><td>$(ConvertTo-HtmlText $project.Dirty)</td><td>$(ConvertTo-HtmlText $project.Branch)</td><td>$(@($project.CacheCandidates).Count)</td></tr>")
    }
    [void]$projectHtml.AppendLine('</tbody></table>')
}
else { [void]$projectHtml.AppendLine('<p>No project inventory was supplied.</p>') }

$coverage = if (@($storage.Errors).Count -eq 0) { 'No storage-inventory access errors were recorded.' } else { "$(@($storage.Errors).Count) storage-inventory errors were recorded; inspect the JSON before claiming full coverage." }
$html = @"
<!doctype html>
<html lang='en'>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>$(ConvertTo-HtmlText $Title)</title>
<style>
:root{color-scheme:light dark;--bg:#f5f7fb;--panel:#fff;--text:#172033;--muted:#657087;--line:#dbe1ec;--blue:#3157d5;--safe:#16794d;--review:#9b6100;--keep:#9f2f2f;--system:#4e5564}
@media(prefers-color-scheme:dark){:root{--bg:#10131a;--panel:#181d27;--text:#eef2fb;--muted:#aab3c6;--line:#30384a;--blue:#83a2ff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.55 system-ui,Segoe UI,sans-serif}main{max-width:1180px;margin:auto;padding:32px 22px 70px}h1{font-size:30px;margin:0 0 8px}h2{margin:0 0 8px}.muted{color:var(--muted)}.volume,.panel,.group{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px;margin:16px 0}.bar{height:10px;background:var(--line);border-radius:8px;overflow:hidden}.bar span{display:block;height:100%;background:var(--blue)}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:9px;border-bottom:1px solid var(--line);vertical-align:top}code{overflow-wrap:anywhere}.group summary{display:flex;justify-content:space-between;cursor:pointer}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:12px;margin-top:16px}.item{border:1px solid var(--line);border-left:5px solid var(--system);border-radius:10px;padding:14px}.SAFE_REBUILDABLE .item{border-left-color:var(--safe)}.REVIEW_REQUIRED .item{border-left-color:var(--review)}.KEEP_USER_OR_EVIDENCE .item{border-left-color:var(--keep)}.item-head{display:flex;justify-content:space-between;gap:12px}.path{color:var(--muted);overflow-wrap:anywhere}button{border:1px solid var(--line);background:transparent;color:inherit;border-radius:8px;padding:7px 10px;cursor:pointer}button:hover{border-color:var(--blue)}
</style>
</head>
<body><main>
<header><h1>$(ConvertTo-HtmlText $Title)</h1><p class='muted'>Captured $(ConvertTo-HtmlText $storage.CapturedAt). Read-only report: it contains no delete action.</p></header>
$volumeHtml
<section class='panel'><h2>Coverage</h2><p>$(ConvertTo-HtmlText $coverage)</p><p class='muted'>Sizes are $(ConvertTo-HtmlText $storage.Measurement). Candidate size is not released space.</p></section>
<section class='panel'><h2>Top measured items</h2><table><thead><tr><th>Size</th><th>Owner</th><th>Path</th><th>Class</th></tr></thead><tbody>$topHtml</tbody></table></section>
<section><h2>Decision inventory</h2>$groupsHtml</section>
<section class='panel'><h2>Project inventory</h2>$projectHtml</section>
<section class='panel'><h2>Execution boundary</h2><p>Generate an exact cleanup manifest, obtain approval for candidate IDs, recheck drift, then execute semantic actions through the owning tool. Colors and this report do not authorize deletion.</p></section>
</main><script>
function decodePath(value){const binary=atob(value);const bytes=Uint8Array.from(binary,c=>c.charCodeAt(0));return new TextDecoder().decode(bytes)}
document.addEventListener('click',async event=>{const button=event.target.closest('.copy-path');if(!button)return;try{await navigator.clipboard.writeText(decodePath(button.dataset.pathB64));button.textContent='Copied';setTimeout(()=>button.textContent='Copy path',1200)}catch(e){button.textContent='Copy failed'}})
</script></body></html>
"@

$parent = Split-Path -Parent $OutputPath
if ($parent -and -not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
[System.IO.File]::WriteAllText($OutputPath, $html, (New-Object System.Text.UTF8Encoding($false)))
Get-Item -LiteralPath $OutputPath | Select-Object FullName, Length, LastWriteTime
