<#
sync-pull.ps1
----------------------------------------------------------------------
将仓库分组结构的 skill 拉取到本地扁平化 skill 目录。

远程仓库按 12 个能力域分组：
    skills/01-agent-engineering/<skill>/
    skills/02-coding-languages/python/<skill>/
    ...

本地扁平化目标：
    <LocalTarget>/<skill>/SKILL.md

参数
    -LocalTarget  本地扁平 skill 根目录（必填，或读 $env:SKILL_HUB_LOCAL_SOURCE）
    -DryRun       仅打印会发生的操作，不写盘
    -RepoRoot     仓库根目录（默认：脚本所在目录的父目录）

用法
    # 预览
    .\sync-pull.ps1 -LocalTarget "C:\Users\me\.claude\skills" -DryRun

    # 执行
    .\sync-pull.ps1 -LocalTarget "C:\Users\me\.claude\skills"

    # 省略 -LocalTarget 时从环境变量读
    $env:SKILL_HUB_LOCAL_SOURCE = "C:\Users\me\.claude\skills"
    .\sync-pull.ps1

行为
  - 仅扫 `RepoRoot\skills\`，不扫 `projects\`（项目私有不做扁平化）。
  - 递归查找 SKILL.md 所在目录，用目录名作为扁平化后的 skill 名。
  - 冲突检测：若两个分组下出现同名 skill，报错并跳过后者。
  - 目标侧采用"清空再复制"的覆盖式同步。
#>

[CmdletBinding()]
param(
    [string]$LocalTarget = $env:SKILL_HUB_LOCAL_SOURCE,

    [string]$RepoRoot,

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Say($msg, $color = "White") { Write-Host $msg -ForegroundColor $color }

# --- 参数校验 ---------------------------------------------------------------

if (-not $RepoRoot -or $RepoRoot.Trim() -eq "") {
    $RepoRoot = Split-Path -Parent $PSScriptRoot
}

if (-not $LocalTarget) {
    Say "ERROR: -LocalTarget 必填（或设置 `$env:SKILL_HUB_LOCAL_SOURCE`）。" "Red"
    Say "示例：.\sync-pull.ps1 -LocalTarget 'C:\Users\me\.claude\skills'" "Yellow"
    exit 1
}

if (-not (Test-Path $RepoRoot)) {
    Say "ERROR: 仓库根目录不存在：$RepoRoot" "Red"
    exit 1
}

$SkillsRoot = Join-Path $RepoRoot "skills"
if (-not (Test-Path $SkillsRoot)) {
    Say "ERROR: 找不到 skills 目录：$SkillsRoot" "Red"
    exit 1
}

if (-not (Test-Path $LocalTarget)) {
    if ($DryRun) {
        Say "  [DRY] 本地目标目录不存在，将会创建：$LocalTarget" "Gray"
    } else {
        New-Item -ItemType Directory -Path $LocalTarget -Force | Out-Null
        Say "  已创建本地目标目录：$LocalTarget" "DarkGray"
    }
}

# --- 横幅 -------------------------------------------------------------------

Say "`n============================================================" "Cyan"
Say "  sync-pull  -  $( if ($DryRun) {'DRY RUN'} else {'LIVE RUN'} )" "Cyan"
Say "============================================================" "Cyan"
Say "  RepoRoot    : $RepoRoot"    "Gray"
Say "  SkillsRoot  : $SkillsRoot"  "Gray"
Say "  LocalTarget : $LocalTarget" "Gray"

# --- 扫仓库 -----------------------------------------------------------------

# 找 SKILL.md，再取其父目录作为 skill 目录
$SkillMdFiles = Get-ChildItem -Path $SkillsRoot -Recurse -File -Filter "SKILL.md" -ErrorAction SilentlyContinue

Say "  仓库内 SKILL.md：$($SkillMdFiles.Count) 个" "Gray"

# 按 skill 名聚合，检测冲突
$ByName = @{}   # name -> [full paths]
foreach ($md in $SkillMdFiles) {
    $skillDir = $md.Directory.FullName
    $skillName = $md.Directory.Name
    if (-not $ByName.ContainsKey($skillName)) {
        $ByName[$skillName] = @()
    }
    $ByName[$skillName] += $skillDir
}

Say "  唯一 skill 名：$($ByName.Count) 个" "Gray"
Say ""

# --- 同步 -------------------------------------------------------------------

$Pulled    = @()
$Conflicts = @()
$Skipped   = @()

foreach ($name in ($ByName.Keys | Sort-Object)) {
    $sources = $ByName[$name]

    if ($sources.Count -gt 1) {
        $Conflicts += [pscustomobject]@{ Name = $name; Paths = $sources }
        Say "  [!!]  $name  -- 同名冲突（$($sources.Count) 处），跳过：" "Red"
        foreach ($p in $sources) {
            $rel = $p.Substring($RepoRoot.Length).TrimStart('\')
            Say "          $rel" "Red"
        }
        continue
    }

    $srcDir = $sources[0]
    $dstDir = Join-Path $LocalTarget $name

    # 源与目标相同（指向同一路径）直接跳过
    try {
        $srcFull = (Resolve-Path $srcDir).Path
        if (Test-Path $dstDir) {
            $dstFull = (Resolve-Path $dstDir).Path
            if ($srcFull -eq $dstFull) {
                $Skipped += $name
                Say "  [=]  $name  -- 源与目标相同，跳过" "DarkGray"
                continue
            }
        }
    } catch {}

    if ($DryRun) {
        $rel = $srcDir.Substring($RepoRoot.Length).TrimStart('\')
        Say "  [DRY] $rel  ->  $name" "Gray"
        $Pulled += $name
        continue
    }

    try {
        if (Test-Path $dstDir) {
            Remove-Item -Path $dstDir -Recurse -Force
        }
        Copy-Item -Path $srcDir -Destination $dstDir -Recurse -Force
        $Pulled += $name
        $rel = $srcDir.Substring($RepoRoot.Length).TrimStart('\')
        Say "  [OK] $rel  ->  $name" "Green"
    } catch {
        Say "  [ERR] $name  -- $($_.Exception.Message)" "Red"
    }
}

# --- 统计 -------------------------------------------------------------------

Say "`n------------------------------------------------------------" "Cyan"
Say "  拉取：$($Pulled.Count)  /  冲突：$($Conflicts.Count)  /  跳过：$($Skipped.Count)" "White"
Say "------------------------------------------------------------" "Cyan"

if ($Conflicts.Count -gt 0) {
    Say "`n同名冲突（需要手工决定归属）：" "Yellow"
    foreach ($c in $Conflicts) {
        Say "    - $($c.Name)" "Yellow"
        foreach ($p in $c.Paths) {
            $rel = $p.Substring($RepoRoot.Length).TrimStart('\')
            Say "        $rel" "DarkYellow"
        }
    }
}

Say ""
if ($DryRun) {
    Say "DRY RUN 完成。重新运行时去掉 -DryRun 即可实际执行。" "Magenta"
} else {
    Say "DONE." "Green"
}
Say "============================================================`n" "Cyan"
