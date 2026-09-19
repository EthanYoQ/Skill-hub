<#
setup-junctions.ps1
----------------------------------------------------------------------
建立 Windows Directory Junction，让多个 AI Agent 共享同一份 Global
技能库（单一源）。

用法
    # 预览
    .\setup-junctions.ps1 -Source <本地单源目录> -DryRun

    # 执行
    .\setup-junctions.ps1 -Source <本地单源目录>

    # 自定义 Junction 目标（以分号分隔）
    .\setup-junctions.ps1 `
        -Source <本地单源目录> `
        -Targets "$env:USERPROFILE\.claude\skills;$env:USERPROFILE\.codex\skills"

    # 省略 -Source 时，从环境变量 SKILL_HUB_SOURCE 读取
    $env:SKILL_HUB_SOURCE = "D:\path\to\local\skills"
    .\setup-junctions.ps1

行为
  - 目标已存在时备份为 <path>.old-<timestamp>
  - 用 cmd /c mklink /J 创建 Junction（无需管理员权限）
  - 最后对比源与每个 Junction 里的 SKILL.md 数量做验证
#>

[CmdletBinding()]
param(
    [string]$Source = $env:SKILL_HUB_SOURCE,

    [string]$Targets = @(
        "$env:USERPROFILE\.claude\skills",
        "$env:USERPROFILE\.antigravity\skills",
        "$env:USERPROFILE\.gemini\antigravity\skills",
        "$env:USERPROFILE\.codex\skills"
    ) -join ";",

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

if (-not $Source) {
    Write-Host "ERROR: -Source is required (or set `$env:SKILL_HUB_SOURCE`)." -ForegroundColor Red
    Write-Host "Example: .\setup-junctions.ps1 -Source 'D:\path\to\local\skills'" -ForegroundColor Yellow
    exit 1
}

$Ts = Get-Date -Format "yyyyMMdd-HHmmss"
$TargetList = $Targets -split ";" | Where-Object { $_ -and $_.Trim() }

function Say($msg, $color = "White") { Write-Host $msg -ForegroundColor $color }

Say "`n============================================================" "Cyan"
Say "  Junction setup - $( if ($DryRun) {'DRY RUN'} else {'LIVE RUN'} )" "Cyan"
Say "============================================================" "Cyan"
Say "`n  Source: $Source" "Gray"

if (-not (Test-Path $Source)) {
    Say "`nERROR: Source dir missing: $Source" "Red"
    exit 1
}

$srcSkillCount = (Get-ChildItem $Source -Directory |
    Where-Object { $_.Name -notmatch '^\.' -and (Test-Path (Join-Path $_.FullName 'SKILL.md')) }
).Count
Say "  Source skill count: $srcSkillCount" "White"

foreach ($path in $TargetList) {
    $path = $path.Trim()
    Say "`n--- $path ---" "Cyan"

    $parent = Split-Path $path -Parent
    if (-not (Test-Path $parent)) {
        if ($DryRun) {
            Say "  [DRY] would create parent: $parent" "Gray"
        } else {
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
            Say "  created parent: $parent" "DarkGray"
        }
    }

    if (Test-Path $path) {
        $item = Get-Item $path -Force
        $isReparse = ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0
        if ($isReparse) {
            try {
                $target = (Get-Item $path -Force).Target
                if ($target -and ($target -eq $Source)) {
                    Say "  [OK] Junction already correct - SKIP" "Green"
                    continue
                }
            } catch {}
            Say "  Existing reparse point points elsewhere." "Yellow"
        } else {
            Say "  Existing real directory." "Yellow"
        }
        $backup = "$path.old-$Ts"
        if ($DryRun) {
            Say "  [DRY] would rename existing to: $backup" "Gray"
        } else {
            try {
                Rename-Item -Path $path -NewName (Split-Path $backup -Leaf) -Force
                Say "  renamed existing -> $(Split-Path $backup -Leaf)" "DarkYellow"
            } catch {
                Say "  rename failed, trying removal..." "DarkYellow"
                cmd /c "rmdir `"$path`"" 2>$null
                if (Test-Path $path) {
                    Remove-Item $path -Recurse -Force -ErrorAction Stop
                }
                Say "  removed stale link" "DarkYellow"
            }
        }
    }

    if ($DryRun) {
        Say "  [DRY] would create junction: $path -> $Source" "Gray"
    } else {
        $out = cmd /c "mklink /J `"$path`" `"$Source`"" 2>&1
        if ($LASTEXITCODE -ne 0) {
            Say "  ERROR creating junction:" "Red"
            Say "  $out" "Red"
            continue
        }
        Say "  [OK] junction created" "Green"
    }
}

if (-not $DryRun) {
    Say "`n--- Verification ---" "Cyan"
    foreach ($path in $TargetList) {
        $path = $path.Trim()
        if (-not (Test-Path $path)) {
            Say "  MISSING: $path" "Red"
            continue
        }
        $count = (Get-ChildItem $path -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -notmatch '^\.' -and (Test-Path (Join-Path $_.FullName 'SKILL.md')) }
        ).Count
        $status = if ($count -eq $srcSkillCount) { "[OK] " } else { "[WARN]" }
        $color  = if ($count -eq $srcSkillCount) { "Green" } else { "Yellow" }
        Say ("  {0} {1,3} skills  ({2})" -f $status, $count, $path) $color
    }
}

Say "`n============================================================" "Cyan"
if ($DryRun) {
    Say "  DRY RUN complete. Re-run without -DryRun to apply.`n" "Magenta"
} else {
    Say "  DONE. Target paths share the same source.`n" "Green"
}
Say "============================================================`n" "Cyan"
