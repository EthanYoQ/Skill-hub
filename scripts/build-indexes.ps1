<#
build-indexes.ps1
----------------------------------------------------------------------
重建 `_meta/` 索引文件：
    _meta/skills-lock.json
    _meta/by-name.md
    _meta/by-domain.md

数据来源
  - 扫 `RepoRoot\skills\` 下所有 SKILL.md（shared 共享技能）
  - 扫 `RepoRoot\projects\` 下所有 SKILL.md（项目私有）
  - 每个 SKILL.md 的 YAML frontmatter 提供 `name` / `description`

保留策略（关键）
  - 现有 `_meta/skills-lock.json` 中 `descriptionZh` 字段为手工维护的中文简介，
    **必须优先保留**。仅当某技能在 lock 中不存在时才用英文 description 占位，
    并在 JSON 中标注 `"_todo": "需要翻译 descriptionZh"`。
  - `by-name.md` / `by-domain.md` 由 lock 派生，因此"保留中文"在 lock 层实现。

参数
    -RepoRoot  仓库根目录（默认：脚本所在目录的父目录）
    -DryRun    仅打印会发生的操作，不写盘

用法
    .\build-indexes.ps1 -DryRun
    .\build-indexes.ps1
#>

[CmdletBinding()]
param(
    [string]$RepoRoot,

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Say($msg, $color = "White") { Write-Host $msg -ForegroundColor $color }

# --- 参数 -------------------------------------------------------------------

if (-not $RepoRoot -or $RepoRoot.Trim() -eq "") {
    $RepoRoot = Split-Path -Parent $PSScriptRoot
}

if (-not (Test-Path $RepoRoot)) {
    Say "ERROR: 仓库根目录不存在：$RepoRoot" "Red"
    exit 1
}
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path

$MetaDir    = Join-Path $RepoRoot "_meta"
$LockPath   = Join-Path $MetaDir  "skills-lock.json"
$ByNamePath = Join-Path $MetaDir  "by-name.md"
$ByDomPath  = Join-Path $MetaDir  "by-domain.md"
$SkillsRoot = Join-Path $RepoRoot "skills"
$ProjRoot   = Join-Path $RepoRoot "projects"

Say "`n============================================================" "Cyan"
Say "  build-indexes - $( if ($DryRun) {'DRY RUN'} else {'LIVE RUN'} )" "Cyan"
Say "============================================================" "Cyan"
Say "  RepoRoot : $RepoRoot" "Gray"
Say "  MetaDir  : $MetaDir"  "Gray"

# --- 读现有 lock（用于保留 descriptionZh）---------------------------------

function Get-LockItems {
    param(
        [object]$Lock,
        [string[]]$Keys
    )

    $items = @()
    foreach ($key in $Keys) {
        if (-not $Lock -or -not $Lock.PSObject.Properties[$key]) { continue }
        $value = $Lock.PSObject.Properties[$key].Value
        if ($null -eq $value) { continue }

        if ($value -is [System.Array]) {
            foreach ($entry in @($value)) {
                if ($entry.name) { $items += $entry }
            }
            continue
        }

        foreach ($prop in $value.PSObject.Properties) {
            $entry = $prop.Value
            if (-not $entry.PSObject.Properties["name"]) {
                $entry | Add-Member -NotePropertyName "name" -NotePropertyValue $prop.Name -Force
            }
            $items += $entry
        }
    }

    return $items
}

$ExistingLock = $null
if (Test-Path $LockPath) {
    try {
        $ExistingLock = Get-Content $LockPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $shC = @(Get-LockItems -Lock $ExistingLock -Keys @("shared", "skills")).Count
        $prC = @(Get-LockItems -Lock $ExistingLock -Keys @("projects")).Count
        Say "  现有 lock：shared=$shC, projects=$prC" "Gray"
    } catch {
        Say "  WARN: 现有 lock 解析失败，按新建处理：$($_.Exception.Message)" "Yellow"
        $ExistingLock = $null
    }
} else {
    Say "  未找到现有 lock，按新建处理。" "Gray"
}

# 查表：旧的描述（按 name）
$OldZhByName = @{}
if ($ExistingLock) {
    foreach ($entry in @(Get-LockItems -Lock $ExistingLock -Keys @("shared", "skills", "projects"))) {
        if ($entry.name -and $entry.descriptionZh) {
            $OldZhByName[$entry.name] = $entry.descriptionZh
        }
    }
}

# --- YAML frontmatter 解析 --------------------------------------------------

function Read-Frontmatter {
    param([string]$Path)

    $result = [pscustomobject]@{
        Name        = $null
        Description = $null
    }

    if (-not (Test-Path $Path)) { return $result }

    $lines = Get-Content $Path -Encoding UTF8 -ErrorAction SilentlyContinue
    if (-not $lines -or $lines.Count -lt 2) { return $result }

    # 第一行必须是 "---"
    if ($lines[0].Trim() -ne "---") { return $result }

    $end = -1
    for ($i = 1; $i -lt [Math]::Min($lines.Count, 200); $i++) {
        if ($lines[$i].Trim() -eq "---") { $end = $i; break }
    }
    if ($end -lt 0) { return $result }

    # 非常简单的 YAML 解析：只取顶层 "key: value"
    # description 可能跨行（YAML block scalar），先按单行处理，够用
    for ($i = 1; $i -lt $end; $i++) {
        $line = $lines[$i]
        if ($line -match '^\s*([A-Za-z0-9_-]+)\s*:\s*(.*)$') {
            $k = $Matches[1].Trim()
            $v = $Matches[2].Trim()
            # 去掉包裹引号
            if ($v.Length -ge 2 -and (
                ($v.StartsWith('"') -and $v.EndsWith('"')) -or
                ($v.StartsWith("'") -and $v.EndsWith("'"))
            )) {
                $v = $v.Substring(1, $v.Length - 2)
            }
            switch ($k) {
                "name"        { $result.Name        = $v }
                "description" { $result.Description = $v }
            }
        }
    }

    return $result
}

# --- 扫 shared skills -------------------------------------------------------

$Shared = @()   # [{name, domain, subdomain, repoPath, description, descriptionZh, todo}]

if (Test-Path $SkillsRoot) {
    $mds = Get-ChildItem -Path $SkillsRoot -Recurse -File -Filter "SKILL.md" -ErrorAction SilentlyContinue
    foreach ($md in $mds) {
        # Evaluation fixtures may include SKILL.md examples; they are not catalog entries.
        if ($md.FullName -match '[\\/]evals[\\/]') { continue }
        $fm = Read-Frontmatter -Path $md.FullName
        $skillDir = $md.Directory

        # 仓库内相对路径：skills/<domain>/[<subdomain>/]<skill>/
        $rel = $skillDir.FullName.Substring($RepoRoot.Length).Trim('\','/').Replace('\', '/')
        $parts = $rel.Split('/')

        # 期望：skills / domain / (subdomain /)? skill
        if ($parts.Length -lt 3 -or $parts[0] -ne 'skills') {
            Say "  WARN: 意外路径结构，跳过：$rel" "Yellow"
            continue
        }

        $domain    = $parts[1]
        $subdomain = $null
        if ($parts.Length -ge 4) {
            $subdomain = $parts[2]
        }

        $name = if ($fm.Name) { $fm.Name } else { $skillDir.Name }

        $zh = $null
        $todo = $null
        if ($OldZhByName.ContainsKey($name)) {
            $zh = $OldZhByName[$name]
        } elseif ($fm.Description) {
            $zh = $fm.Description
            $todo = "需要翻译 descriptionZh"
        }

        $Shared += [pscustomobject]@{
            Name          = $name
            Domain        = $domain
            Subdomain     = $subdomain
            RepoPath      = "$rel/"
            Description   = $fm.Description
            DescriptionZh = $zh
            Todo          = $todo
        }
    }
}

Say "  共享技能：$($Shared.Count)" "Gray"

# --- 扫 projects ------------------------------------------------------------

$Projects = @()

if (Test-Path $ProjRoot) {
    $mds = Get-ChildItem -Path $ProjRoot -Recurse -File -Filter "SKILL.md" -ErrorAction SilentlyContinue
    foreach ($md in $mds) {
        # Evaluation fixtures may include SKILL.md examples; they are not catalog entries.
        if ($md.FullName -match '[\\/]evals[\\/]') { continue }
        $fm = Read-Frontmatter -Path $md.FullName
        $skillDir = $md.Directory

        $rel = $skillDir.FullName.Substring($RepoRoot.Length).Trim('\','/').Replace('\', '/')
        $parts = $rel.Split('/')
        # 期望：projects / <project> / <skill>
        if ($parts.Length -lt 3 -or $parts[0] -ne 'projects') {
            Say "  WARN: 意外项目路径结构，跳过：$rel" "Yellow"
            continue
        }

        $project = $parts[1]
        $name    = if ($fm.Name) { $fm.Name } else { $skillDir.Name }

        $zh = $null
        $todo = $null
        if ($OldZhByName.ContainsKey($name)) {
            $zh = $OldZhByName[$name]
        } elseif ($fm.Description) {
            $zh = $fm.Description
            $todo = "需要翻译 descriptionZh"
        }

        $Projects += [pscustomobject]@{
            Name          = $name
            Project       = $project
            RepoPath      = "$rel/"
            Description   = $fm.Description
            DescriptionZh = $zh
            Todo          = $todo
        }
    }
}

Say "  项目私有技能：$($Projects.Count)" "Gray"
Say ""

# --- 构造新的 lock JSON -----------------------------------------------------

$sharedArr   = @()
$projectsArr = @()

foreach ($s in ($Shared | Sort-Object Domain, Subdomain, Name)) {
    $entry = [ordered]@{
        name   = $s.Name
        domain = $s.Domain
        path   = $s.RepoPath
    }
    if ($s.Subdomain)     { $entry.subdomain     = $s.Subdomain }
    if ($s.DescriptionZh) { $entry.descriptionZh = $s.DescriptionZh }
    if ($s.Todo)          { $entry["_todo"]       = $s.Todo }
    $sharedArr += [pscustomobject]$entry
}

foreach ($p in ($Projects | Sort-Object Project, Name)) {
    $entry = [ordered]@{
        name    = $p.Name
        project = $p.Project
        path    = $p.RepoPath
    }
    if ($p.DescriptionZh) { $entry.descriptionZh = $p.DescriptionZh }
    if ($p.Todo)          { $entry["_todo"]       = $p.Todo }
    $projectsArr += [pscustomobject]$entry
}

$NewLock = [ordered]@{
    version      = "2.0"
    generated_at = (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz")
    note         = "Rebuilt indexes from repository SKILL.md files. Total: $($Shared.Count) shared + $($Projects.Count) projects = $($Shared.Count + $Projects.Count) total"
    counts       = [ordered]@{
        shared   = $Shared.Count
        projects = $Projects.Count
        total    = ($Shared.Count + $Projects.Count)
    }
    shared       = $sharedArr
    projects     = $projectsArr
}

$NewLockJson = $NewLock | ConvertTo-Json -Depth 10

# --- 能力域中文名（用于 by-domain.md）-----------------------------------

$DomainLabels = [ordered]@{
    "01-agent-engineering" = "01 Agent 工程"
    "02-coding-languages"  = "02 编程语言"
    "03-frameworks"        = "03 框架与技术栈"
    "06-data-search"       = "06 数据与检索"
    "07-media-content"     = "07 媒体与内容制作"
    "08-writing-marketing" = "08 写作与营销"
    "10-business-industry" = "10 行业与业务"
}

# 锚点对照（与既有索引保持一致的 GitHub Anchor 规则）
$DomainAnchors = @{
    "01-agent-engineering" = "01-agent-工程"
    "02-coding-languages"  = "02-编程语言"
    "03-frameworks"        = "03-框架与技术栈"
    "06-data-search"       = "06-数据与检索"
    "07-media-content"     = "07-媒体与内容制作"
    "08-writing-marketing" = "08-写作与营销"
    "10-business-industry" = "10-行业与业务"
}

# --- 构造 by-name.md --------------------------------------------------------

function Build-ByName {
    param($Shared, $Projects)

    $all = @()
    foreach ($s in $Shared) {
        $all += [pscustomobject]@{
            Name = $s.Name
            Path = $s.RepoPath
            Desc = if ($s.DescriptionZh) { $s.DescriptionZh } else { "(待补中文简介)" }
            IsProject = $false
        }
    }
    foreach ($p in $Projects) {
        $all += [pscustomobject]@{
            Name = $p.Name
            Path = $p.RepoPath
            Desc = if ($p.DescriptionZh) { $p.DescriptionZh } else { "(待补中文简介)" }
            IsProject = $true
        }
    }

    $sorted = $all | Sort-Object Name

    $sb = [System.Text.StringBuilder]::new()
    [void]$sb.AppendLine("# 按技能名 A-Z 索引")
    [void]$sb.AppendLine()
    [void]$sb.AppendLine("共 $($sorted.Count) 个技能（$($Shared.Count) 个共享 + $($Projects.Count) 个项目私有）。项目私有技能以 *(项目)* 标注。")
    [void]$sb.AppendLine()
    [void]$sb.AppendLine("| # | 技能名 | 路径 | 中文简介 |")
    [void]$sb.AppendLine("|---|---|---|---|")

    $i = 0
    foreach ($row in $sorted) {
        $i++
        $suffix = if ($row.IsProject) { " *(项目)*" } else { "" }
        $line = "| $i | **$($row.Name)**$suffix | [$($row.Path)](../$($row.Path)) | $($row.Desc) |"
        [void]$sb.AppendLine($line)
    }

    return $sb.ToString()
}

# --- 构造 by-domain.md ------------------------------------------------------

function Build-ByDomain {
    param($Shared, $Projects, $DomainLabels, $DomainAnchors)

    # 按 domain 分组（用 @() 包裹确保始终是数组，避免单元素 Count 为空）
    $byDomain = @{}
    foreach ($s in $Shared) {
        if (-not $byDomain.ContainsKey($s.Domain)) { $byDomain[$s.Domain] = @() }
        $byDomain[$s.Domain] = @($byDomain[$s.Domain]) + $s
    }

    # 项目按 project 分组
    $byProject = @{}
    foreach ($p in $Projects) {
        if (-not $byProject.ContainsKey($p.Project)) { $byProject[$p.Project] = @() }
        $byProject[$p.Project] = @($byProject[$p.Project]) + $p
    }

    # 计算非空能力域数量
    $nonEmptyDomains = 0
    foreach ($k in $DomainLabels.Keys) {
        if ($byDomain.ContainsKey($k) -and @($byDomain[$k]).Count -gt 0) { $nonEmptyDomains++ }
    }

    $sb = [System.Text.StringBuilder]::new()
    $total = $Shared.Count + $Projects.Count
    [void]$sb.AppendLine("# 按能力域索引")
    [void]$sb.AppendLine()
    [void]$sb.AppendLine("共 $total 个技能，按 $nonEmptyDomains 个能力域 + projects（项目私有）分组。")
    [void]$sb.AppendLine()
    [void]$sb.AppendLine("## 目录")
    [void]$sb.AppendLine()

    foreach ($k in $DomainLabels.Keys) {
        $count = if ($byDomain.ContainsKey($k)) { @($byDomain[$k]).Count } else { 0 }
        if ($count -eq 0) { continue }
        $anchor = $DomainAnchors[$k]
        [void]$sb.AppendLine("- [$($DomainLabels[$k])](#$anchor)（$count）")
    }
    [void]$sb.AppendLine("- [Projects 项目私有](#projects-项目私有)（$(@($Projects).Count)）")
    [void]$sb.AppendLine()

    foreach ($k in $DomainLabels.Keys) {
        if ($byDomain.ContainsKey($k)) {
            $list = @($byDomain[$k])
        } else {
            $list = @()
        }
        if ($list.Count -eq 0) { continue }
        [void]$sb.AppendLine("## $($DomainLabels[$k])（$($list.Count)）")
        [void]$sb.AppendLine()
        [void]$sb.AppendLine("| 技能名 | 路径 | 中文简介 |")
        [void]$sb.AppendLine("|---|---|---|")
        foreach ($s in ($list | Sort-Object Name)) {
            $desc = if ($s.DescriptionZh) { $s.DescriptionZh } else { "(待补中文简介)" }
            [void]$sb.AppendLine("| **$($s.Name)** | [$($s.RepoPath)](../$($s.RepoPath)) | $desc |")
        }
        [void]$sb.AppendLine()
    }

    # Projects
    $projCount = @($Projects).Count
    [void]$sb.AppendLine("## Projects 项目私有（$projCount）")
    [void]$sb.AppendLine()
    if ($projCount -eq 0) {
        [void]$sb.AppendLine("_暂无项目私有技能。_")
        [void]$sb.AppendLine()
    } else {
        foreach ($proj in ($byProject.Keys | Sort-Object)) {
            $list = @($byProject[$proj])
            [void]$sb.AppendLine("### $proj（$($list.Count)）")
            [void]$sb.AppendLine()
            [void]$sb.AppendLine("| 技能名 | 路径 | 中文简介 |")
            [void]$sb.AppendLine("|---|---|---|")
            foreach ($p in ($list | Sort-Object Name)) {
                $desc = if ($p.DescriptionZh) { $p.DescriptionZh } else { "(待补中文简介)" }
                [void]$sb.AppendLine("| **$($p.Name)** | [$($p.RepoPath)](../$($p.RepoPath)) | $desc |")
            }
            [void]$sb.AppendLine()
        }
    }

    return $sb.ToString()
}

# --- 生成内容 ---------------------------------------------------------------

$ByNameContent   = Build-ByName   -Shared $Shared -Projects $Projects
$ByDomainContent = Build-ByDomain -Shared $Shared -Projects $Projects `
                                  -DomainLabels $DomainLabels -DomainAnchors $DomainAnchors

# --- 写出 -------------------------------------------------------------------

function Write-FileUtf8NoBom {
    param([string]$Path, [string]$Content)
    $enc = New-Object System.Text.UTF8Encoding($false)
    $normalized = $Content.TrimEnd([char[]]"`r`n") + [Environment]::NewLine
    [System.IO.File]::WriteAllText($Path, $normalized, $enc)
}

function Report-Write {
    param([string]$Path, [string]$Content, [switch]$DryRun, [string]$Label)
    if ($DryRun) {
        $lines = ($Content -split "`n").Count
        Say "  [DRY] 将写 $Label ($lines 行)：$Path" "Gray"
        return
    }
    Write-FileUtf8NoBom -Path $Path -Content $Content
    Say "  [OK] 已写 $Label：$Path" "Green"
}

Say "生成结果：" "Cyan"

# 1. skills-lock.json
Report-Write -Path $LockPath -Content $NewLockJson -DryRun:$DryRun -Label "skills-lock.json"

# 2. by-name.md
Report-Write -Path $ByNamePath -Content $ByNameContent -DryRun:$DryRun -Label "by-name.md"

# 3. by-domain.md
Report-Write -Path $ByDomPath -Content $ByDomainContent -DryRun:$DryRun -Label "by-domain.md"

Say ""
if ($DryRun) {
    Say "DRY RUN 完成。重新运行时去掉 -DryRun 即可实际执行。" "Magenta"
} else {
    Say "DONE." "Green"
}
Say "============================================================`n" "Cyan"
