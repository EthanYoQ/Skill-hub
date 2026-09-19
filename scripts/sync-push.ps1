<#
sync-push.ps1
----------------------------------------------------------------------
将本地扁平化 skill 目录推送到仓库的分组结构。

远程仓库按 12 个能力域分组：
    skills/01-agent-engineering/<skill>/
    skills/02-coding-languages/python/<skill>/
    ...

本地使用者习惯扁平结构：
    <LocalSource>/<skill>/SKILL.md

本脚本读取 `_meta/skills-lock.json` 建立 {name -> repoPath} 映射，
然后把本地每个 skill 覆盖式同步到仓库对应子目录。

参数
    -LocalSource  本地扁平 skill 根目录（必填，或读 $env:SKILL_HUB_LOCAL_SOURCE）
    -DryRun       仅打印会发生的操作，不写盘
    -RepoRoot     仓库根目录（默认：脚本所在目录的父目录）

用法
    # 预览
    .\sync-push.ps1 -LocalSource "C:\Users\me\.claude\skills" -DryRun

    # 执行
    .\sync-push.ps1 -LocalSource "C:\Users\me\.claude\skills"

    # 省略 -LocalSource 时从环境变量读
    $env:SKILL_HUB_LOCAL_SOURCE = "C:\Users\me\.claude\skills"
    .\sync-push.ps1

行为
  - 仅处理 `_meta/skills-lock.json` 中的 `shared` / `skills` 段（共享技能）。
    `projects` 段是项目私有，不参与扁平化。
  - 本地 skill 在 lock 中查不到 → 收集到"未映射列表"，最后一次性报出。
    不自动归类，避免错误分类。
  - 目标侧采用"清空再复制"的覆盖式同步，保证目标与本地一致。
#>

[CmdletBinding()]
param(
    [string]$LocalSource = $env:SKILL_HUB_LOCAL_SOURCE,

    [string]$RepoRoot,

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Say($msg, $color = "White") { Write-Host $msg -ForegroundColor $color }

# --- 参数校验与默认值 -------------------------------------------------------

if (-not $RepoRoot -or $RepoRoot.Trim() -eq "") {
    $RepoRoot = Split-Path -Parent $PSScriptRoot
}

if (-not $LocalSource) {
    Say "ERROR: -LocalSource 必填（或设置 `$env:SKILL_HUB_LOCAL_SOURCE`）。" "Red"
    Say "示例：.\sync-push.ps1 -LocalSource 'C:\Users\me\.claude\skills'" "Yellow"
    exit 1
}

if (-not (Test-Path $LocalSource)) {
    Say "ERROR: 本地源目录不存在：$LocalSource" "Red"
    exit 1
}

if (-not (Test-Path $RepoRoot)) {
    Say "ERROR: 仓库根目录不存在：$RepoRoot" "Red"
    exit 1
}

$LockPath = Join-Path $RepoRoot "_meta\skills-lock.json"
if (-not (Test-Path $LockPath)) {
    Say "ERROR: 找不到 skills-lock.json：$LockPath" "Red"
    exit 1
}

# --- 横幅 -------------------------------------------------------------------

Say "`n============================================================" "Cyan"
Say "  sync-push  -  $( if ($DryRun) {'DRY RUN'} else {'LIVE RUN'} )" "Cyan"
Say "============================================================" "Cyan"
Say "  LocalSource : $LocalSource" "Gray"
Say "  RepoRoot    : $RepoRoot"    "Gray"
Say "  Lock        : $LockPath"    "Gray"

# --- 读 lock 建立映射 -------------------------------------------------------

$Lock = Get-Content $LockPath -Raw -Encoding UTF8 | ConvertFrom-Json

# 建立 {name -> repoPath} 映射（仅 shared skills，不含 projects）
$NameToRepoPath = @{}

if ($Lock.shared) {
    foreach ($entry in @($Lock.shared)) {
        $name = $entry.name
        $path = if ($entry.path) { $entry.path } else { $entry.repoPath }
        if ($name -and $path) {
            $NameToRepoPath[$name] = $path
        }
    }
} elseif ($Lock.skills) {
    foreach ($prop in $Lock.skills.PSObject.Properties) {
        $name = $prop.Name
        $entry = $prop.Value
        $path = if ($entry.path) { $entry.path } else { $entry.repoPath }
        if ($path) {
            $NameToRepoPath[$name] = $path
        }
    }
}

if ($NameToRepoPath.Count -eq 0) {
    Say "ERROR: skills-lock.json 缺少可用的 shared/skills 映射。" "Red"
    exit 1
}
Say "  共享技能映射：$($NameToRepoPath.Count) 条" "Gray"

# --- 扫本地 -----------------------------------------------------------------

$LocalDirs = Get-ChildItem -Path $LocalSource -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -notmatch '^\.' -and (Test-Path (Join-Path $_.FullName 'SKILL.md')) }

Say "  本地 skill 目录：$($LocalDirs.Count) 个" "Gray"
Say ""

# --- 同步 -------------------------------------------------------------------

$Pushed    = @()
$Unmapped  = @()
$Skipped   = @()

foreach ($dir in $LocalDirs) {
    $name = $dir.Name

    if (-not $NameToRepoPath.ContainsKey($name)) {
        $Unmapped += $name
        Say "  [?]  $name  -- 未在 lock 中找到，跳过（需手工归类）" "Yellow"
        continue
    }

    $repoRel  = $NameToRepoPath[$name].TrimEnd('/').TrimEnd('\')
    $repoDest = Join-Path $RepoRoot ($repoRel -replace '/', '\')

    # 源与目标相同（比如本地就是仓库内某子目录）直接跳过
    $srcFull = (Resolve-Path $dir.FullName).Path
    $dstFullExists = Test-Path $repoDest
    if ($dstFullExists) {
        try {
            $dstFull = (Resolve-Path $repoDest).Path
            if ($srcFull -eq $dstFull) {
                $Skipped += $name
                Say "  [=]  $name  -- 源与目标相同，跳过" "DarkGray"
                continue
            }
        } catch {}
    }

    if ($DryRun) {
        Say "  [DRY] $name  ->  $repoRel" "Gray"
        $Pushed += $name
        continue
    }

    # 清空目标目录（保留父目录），再整体复制
    try {
        if (Test-Path $repoDest) {
            Remove-Item -Path $repoDest -Recurse -Force
        }
        $parent = Split-Path -Parent $repoDest
        if (-not (Test-Path $parent)) {
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
        }
        Copy-Item -Path $dir.FullName -Destination $repoDest -Recurse -Force
        $Pushed += $name
        Say "  [OK] $name  ->  $repoRel" "Green"
    } catch {
        Say "  [ERR] $name  -- $($_.Exception.Message)" "Red"
    }
}

# --- 统计 -------------------------------------------------------------------

Say "`n------------------------------------------------------------" "Cyan"
Say "  推送：$($Pushed.Count)  /  未映射：$($Unmapped.Count)  /  跳过：$($Skipped.Count)" "White"
Say "------------------------------------------------------------" "Cyan"

if ($Unmapped.Count -gt 0) {
    Say "`n未映射列表（需在 _meta/skills-lock.json 中手工添加归属）：" "Yellow"
    foreach ($n in ($Unmapped | Sort-Object)) {
        Say "    - $n" "Yellow"
    }
}

Say ""
if ($DryRun) {
    Say "DRY RUN 完成。重新运行时去掉 -DryRun 即可实际执行。" "Magenta"
} else {
    Say "DONE." "Green"
}
Say "============================================================`n" "Cyan"
