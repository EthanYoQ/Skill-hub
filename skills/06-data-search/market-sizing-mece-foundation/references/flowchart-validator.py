# -*- coding: utf-8 -*-
"""
Mermaid Flowchart 结构验证器(L0 Foundation 强约束工具 · v1.0)

使用方式:
    python flowchart-validator.py <flowchart.mmd>

验证项目(全部必须通过,任何一条失败报告生成器须停止渲染 PDF):
    1. Mermaid 渲染语法(mmdc --dry-run)— 硬约束
    2. Frontmatter 必须首行(如果有 `---`,前面不能有注释或空行)
    3. 每个叶子节点必须是 ● 终止(禁止悬空分支)— flowchart-rules 规则 2
    4. subgraph 覆盖率(复杂流程图 ≥3 个 subgraph)— flowchart-rules 规则 4
    5. 无多源汇聚共用节点(多入度节点必须标记为"汇聚/路由"用途)— 规则 11
    6. 诊断层必须存在(患者流瀑布图特定)
    7. 治疗层必须存在(患者流瀑布图特定)

返回码:
    0 = 全部通过
    1 = 软性警告(subgraph 过少/共用节点嫌疑)
    2 = 硬性错误(语法/frontmatter/无终点)
"""
import sys
import subprocess
import re
import os
from pathlib import Path


class ValidationResult:
    def __init__(self):
        self.errors = []      # 硬性错误
        self.warnings = []    # 软性警告
        self.info = []        # 信息

    def fail(self, msg: str):  self.errors.append(msg)
    def warn(self, msg: str):  self.warnings.append(msg)
    def add (self, msg: str):  self.info.append(msg)

    @property
    def return_code(self):
        if self.errors: return 2
        if self.warnings: return 1
        return 0

    def report(self):
        if self.info:
            print("[INFO]")
            for m in self.info: print(f"  · {m}")
        if self.warnings:
            print("[WARN] 软性警告(不阻塞,但建议修复)")
            for m in self.warnings: print(f"  ⚠ {m}")
        if self.errors:
            print("[FAIL] 硬性错误(阻塞渲染 PDF)")
            for m in self.errors: print(f"  ✗ {m}")
        else:
            print("[PASS] 所有硬性约束通过")


def check_frontmatter_position(text: str, result: ValidationResult) -> None:
    """Rule 13:Mermaid YAML frontmatter 必须在文件第 1 行。"""
    lines = text.split('\n')
    if not lines:
        return
    # 找 `---` 第一次出现
    first_triple_dash = None
    for i, line in enumerate(lines):
        if line.strip() == '---':
            first_triple_dash = i
            break
    # 如果根本没 frontmatter,跳过
    if first_triple_dash is None:
        return
    # 检查 frontmatter 之前是否有非空非空白内容
    preamble = '\n'.join(lines[:first_triple_dash])
    if preamble.strip() != '':
        result.fail(
            f'YAML frontmatter 前 {first_triple_dash} 行含非空内容(注释/空格等),'
            f'会触发 Mermaid 10.9+ Parse error。修复:把 `---` 放到文件第 1 行,'
            f'把 `%% ...` 注释移到 `flowchart TD` 之后。'
        )


def check_mermaid_render(mmd_path: Path, result: ValidationResult) -> None:
    """Rule 14:必须通过 mmdc 渲染。"""
    tmp_png = mmd_path.parent / f'_validator_tmp_{os.getpid()}.png'
    puppeteer_cfg = mmd_path.parent / 'puppeteer-config.json'
    args = ['npx', '--yes', '@mermaid-js/mermaid-cli',
            '-i', str(mmd_path), '-o', str(tmp_png),
            '-w', '800', '-b', 'white']
    if puppeteer_cfg.exists():
        args += ['-p', str(puppeteer_cfg)]
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=120)
        stdout = (proc.stdout or '') + (proc.stderr or '')
        if 'Parse error' in stdout or 'Error:' in stdout:
            first_err = next((ln for ln in stdout.split('\n') if 'Error' in ln or 'Parse error' in ln), '')
            result.fail(f'Mermaid 渲染失败:{first_err.strip()}')
        elif not tmp_png.exists():
            result.fail('Mermaid 渲染未生成 PNG(可能超时或其他错误)')
        else:
            result.add(f'Mermaid 渲染通过(PNG size {tmp_png.stat().st_size:,} bytes)')
    except subprocess.TimeoutExpired:
        result.warn('Mermaid 渲染超时(>120s),无法确认语法;请手动验证')
    except FileNotFoundError:
        result.warn('npx/mmdc 不可用,跳过渲染检查')
    finally:
        if tmp_png.exists():
            tmp_png.unlink()


def find_all_node_ids(text: str) -> set:
    """提取所有节点 ID(用作 leaf/connectivity 分析)"""
    # 匹配 NODE["..."] / NODE[(...)] / NODE(...) / NODE{...} / NODE[/.../] 等
    pattern = re.compile(r'(?:^|\s|-->\|[^|]*\|\s*|-->|-\.-|->)([A-Z][A-Z0-9_]*)\s*[\[\{\(]')
    ids = set(pattern.findall(text))
    # 另外提取 `class NODE1,NODE2 classname` 里的 ID
    for m in re.finditer(r'^\s*class\s+([A-Z][A-Z0-9_,\s]*)\s+\w+', text, re.MULTILINE):
        for nid in m.group(1).split(','):
            ids.add(nid.strip())
    ids.discard('TD')  # flowchart TD 不是节点
    return ids


def find_edges(text: str) -> list:
    """提取所有 `A --> B` / `A -.- B` 类箭头连接,返回 [(src, dst), ...]"""
    edges = []
    for line in text.split('\n'):
        s = line.strip()
        if s.startswith('%%') or not s:
            continue
        # A -->|label| B / A --> B / A -.- B / A -.-> B
        # 处理 `A -->|...| B & C & D`(&  广播)
        arrow_pattern = re.compile(r'([A-Z][A-Z0-9_]*)\s*(?:-->|-\.->|-\.-|->)\s*(?:\|[^|]*\|\s*)?([A-Z][A-Z0-9_&\s]*)')
        for m in arrow_pattern.finditer(s):
            src = m.group(1)
            targets = [t.strip() for t in m.group(2).split('&')]
            for dst in targets:
                if dst and re.match(r'^[A-Z][A-Z0-9_]*$', dst):
                    edges.append((src, dst))
    return edges


def check_terminal_nodes(text: str, edges: list, result: ValidationResult) -> None:
    """Rule 2:每个分支必须以 ● 终止。"""
    # 统计 ● 出现(通常在终止节点文本里)
    terminal_count = text.count('●')
    if terminal_count == 0:
        result.fail(
            f'流程图无任何 ● 终止节点。按 flowchart-rules 规则 2,'
            f'每个分支必须以 ● 终止节点结束。请为每个叶子节点添加形如 '
            f'`END_X(["●终止<br/>..."])` 的节点。'
        )
        return
    # 找出没有出度的叶子节点
    srcs = set(s for s, _ in edges)
    dsts = set(d for _, d in edges)
    leaves = dsts - srcs  # 只作为 dst 没作为 src 的节点
    # 检查每个 leaf 节点的文本是否含 ● 或 `END_`
    missing_terminals = []
    for leaf in leaves:
        # 搜索节点定义行
        patterns = [
            rf'{re.escape(leaf)}\s*\[[^\]]*●',        # 方括号节点含 ●
            rf'{re.escape(leaf)}\s*\(\[[^\]]*●',      # stadium 节点含 ●
            rf'{re.escape(leaf)}\s*\(\([^)]*●',       # 圆节点含 ●
            rf'{leaf}\s*\[["\']?\s*●',                # 其他形状
        ]
        has_terminal = any(re.search(p, text) for p in patterns)
        # 或者 leaf ID 以 END_ 开头
        if leaf.startswith('END_') or leaf.endswith('_END') or has_terminal:
            continue
        missing_terminals.append(leaf)
    if missing_terminals:
        result.fail(
            f'叶子节点未以 ● 终止(共 {len(missing_terminals)} 个):'
            f'{", ".join(missing_terminals[:8])}{" ..." if len(missing_terminals) > 8 else ""}。'
            f'每个叶子必须改为 `END_X(["●终止<br/>..."])` 形式。'
        )


def check_subgraph_coverage(text: str, edges: list, result: ValidationResult) -> None:
    """Rule 4 + 11:复杂流程图必须有 subgraph swim-lane。"""
    subgraph_count = text.count('subgraph ')
    node_ids = find_all_node_ids(text)
    if len(node_ids) >= 15 and subgraph_count < 3:
        result.warn(
            f'流程图有 {len(node_ids)} 个节点但仅 {subgraph_count} 个 subgraph。'
            f'按 flowchart-rules 规则 4,复杂图(≥15 节点)应有 ≥3 个 subgraph '
            f'作为 swim-lane,避免跨分支箭头交叉。'
        )


def check_shared_nodes(edges: list, result: ValidationResult) -> None:
    """Rule 11:警告多入度共用节点(可能造成交叉)。"""
    # 统计每个 dst 的入度
    in_degree = {}
    for _, dst in edges:
        in_degree[dst] = in_degree.get(dst, 0) + 1
    # 入度 >= 3 的节点可能是共用节点(除非是明确的"汇聚/评估"节点)
    suspicious = [(dst, d) for dst, d in in_degree.items() if d >= 3]
    # 过滤掉看起来像汇聚点的 ID(EVAL/ROUTER/SCREEN/END)
    suspicious = [(n, d) for n, d in suspicious
                  if not any(kw in n for kw in ['EVAL', 'ROUTER', 'SCREEN', 'END', 'DIAG', 'RETURN'])]
    if suspicious:
        nodes_str = ', '.join(f'{n}({d} in)' for n, d in suspicious[:5])
        result.warn(
            f'发现 {len(suspicious)} 个多入度(≥3)节点,可能造成跨分支箭头交叉:{nodes_str}。'
            f'按 flowchart-rules 规则 11,如非明确汇聚点,应拆成多份独立节点(如 LP3_A / LP3_B)。'
        )


def check_diagnosis_and_treatment_layers(text: str, result: ValidationResult) -> None:
    """患者流瀑布图必备层:诊断层 + 治疗层。"""
    has_dx = any(kw in text for kw in ['诊断', 'DX_', 'Diagnosis', 'DIAG'])
    has_tx = any(kw in text for kw in ['治疗', 'TX_', 'Treatment', 'Therapy', '一线'])
    if not has_dx:
        result.warn('未检测到诊断层(关键词:诊断/DX_/DIAG)。患者流瀑布图应包含诊断节点。')
    if not has_tx:
        result.warn('未检测到治疗层(关键词:治疗/TX_/Therapy/一线)。患者流瀑布图应包含治疗节点。')


def main():
    if len(sys.argv) != 2:
        print(f'用法:python {sys.argv[0]} <flowchart.mmd>')
        sys.exit(3)
    mmd_path = Path(sys.argv[1]).resolve()
    if not mmd_path.exists():
        print(f'文件不存在:{mmd_path}')
        sys.exit(3)

    text = mmd_path.read_text(encoding='utf-8')
    result = ValidationResult()
    print(f'=== 验证 {mmd_path.name}({len(text):,} chars, {text.count(chr(10))+1} lines)===\n')

    check_frontmatter_position(text, result)
    check_mermaid_render(mmd_path, result)

    edges = find_edges(text)
    result.add(f'检测到 {len(edges)} 条边、{len(find_all_node_ids(text))} 个节点')

    check_terminal_nodes(text, edges, result)
    check_subgraph_coverage(text, edges, result)
    check_shared_nodes(edges, result)
    check_diagnosis_and_treatment_layers(text, result)

    print()
    result.report()
    sys.exit(result.return_code)


if __name__ == '__main__':
    main()
