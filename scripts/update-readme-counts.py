#!/usr/bin/env python3
"""从 _meta/skills-lock.json 读取 skill 数量，更新 README / _meta/README 里的数字。

在镜像 workflow 里，删除排除 skill + 重建索引后调用本脚本，
让组织仓库的 README 数字与实际保留的 skill 数量一致。

用法：
    python3 scripts/update-readme-counts.py            # 实际更新
    python3 scripts/update-readme-counts.py --dry-run  # 仅预览
"""
import json
import re
import sys
from pathlib import Path


def main():
    repo_root = Path(__file__).resolve().parent.parent
    lock_path = repo_root / "_meta" / "skills-lock.json"
    dry_run = "--dry-run" in sys.argv

    if not lock_path.exists():
        print(f"ERROR: {lock_path} not found")
        sys.exit(1)

    with open(lock_path, encoding="utf-8") as f:
        lock = json.load(f)

    shared_count = lock["counts"]["shared"]
    projects_count = lock["counts"]["projects"]
    total_count = lock["counts"]["total"]

    # 各 domain 的 shared 数
    domain_counts = {}
    for s in lock.get("shared", []):
        d = s["domain"]
        domain_counts[d] = domain_counts.get(d, 0) + 1

    non_empty_domains = len(domain_counts)

    print(f"counts: shared={shared_count} projects={projects_count} total={total_count}")
    print(f"domains: {domain_counts}")
    print(f"non_empty_domains: {non_empty_domains}")
    print()

    targets = [
        repo_root / "README.md",
        repo_root / "README_EN.md",
        repo_root / "README.en.md",
        repo_root / "_meta" / "README.md",
    ]

    for readme_path in targets:
        if not readme_path.exists():
            print(f"  [SKIP] {readme_path.name} (not found)")
            continue

        content = readme_path.read_text(encoding="utf-8")
        original = content

        # --- 1. 头部总数（中文）---
        content = re.sub(
            r'仓库当前包含 \*\*\d+\*\* 个可复用技能，其中 \*\*\d+\*\* 个共享技能[^，]*，\*\*\d+\*\* 个项目私有技能[^。]*',
            f'仓库当前包含 **{total_count}** 个可复用技能，其中 **{shared_count}** 个共享技能按能力域组织，**{projects_count}** 个项目私有技能按项目归档，便于检索、本地同步、来源追踪和持续维护',
            content,
        )

        # --- 1b. 头部总数（英文）---
        content = re.sub(
            r'currently contains \*\*\d+\*\* reusable skills: \*\*\d+\*\* shared skills[^:]*and \*\*\d+\*\* project-specific skills[^.]*',
            f'currently contains **{total_count}** reusable skills: **{shared_count}** shared skills organized by capability domain and **{projects_count}** project-specific skills archived by project for lookup, local sync, source tracking, and ongoing maintenance',
            content,
        )

        # --- 2. 能力域表格：用 skills/<domain>/ 作为锚点替换前面的数字 ---
        # README 表格的第一列是图标/类别，数量位于第二列。
        for domain, count in domain_counts.items():
            pattern = rf'(\|[^\n|]*\|\s*)\d+(\s*\|\s*`skills/{re.escape(domain)}/`\s*\|)'
            content = re.sub(pattern, rf'\g<1>{count}\g<2>', content)

        # --- 2b. 项目私有能力域行 ---
        content = re.sub(
            r'(\|[^\n|]*\|\s*)\d+(\s*\|\s*`projects/`\s*\|)',
            rf'\g<1>{projects_count}\g<2>',
            content,
        )

        # --- 3. 目录结构注释：# 数字 个共享技能，分 数字 个能力域 ---
        content = re.sub(
            r'# \d+ 个共享技能，分 \d+ 个能力域',
            f'# {shared_count} 个共享技能，分 {non_empty_domains} 个能力域',
            content,
        )

        # --- 3b. 英文目录结构注释 ---
        content = re.sub(
            r'# \d+ shared skills?(?:,?\s*\d+\s*(?:capability\s*)?domains?)?',
            f'# {shared_count} shared skills, {non_empty_domains} capability domains',
            content,
        )

        # --- 3c. projects/ 目录结构注释数字 ---
        content = re.sub(
            r'# \d+ 个项目私有技能',
            f'# {projects_count} 个项目私有技能',
            content,
        )
        content = re.sub(
            r'# \d+ project-specific skills',
            f'# {projects_count} project-specific skills',
            content,
        )

        # --- 5. _meta/README.md 特有：当前共 N 个技能（N 个共享 + N 个项目私有）---
        content = re.sub(
            r'当前共 \d+ 个技能（\d+ 个共享 \+ \d+ 个项目私有）',
            f'当前共 {total_count} 个技能（{shared_count} 个共享 + {projects_count} 个项目私有）',
            content,
        )

        if content != original:
            if dry_run:
                print(f"  [DRY] would update {readme_path}")
            else:
                readme_path.write_text(content, encoding="utf-8")
                print(f"  [OK] updated {readme_path}")
        else:
            print(f"  [=] no changes {readme_path}")


if __name__ == "__main__":
    main()
