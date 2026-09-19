#!/usr/bin/env python
"""Analyze a Xiaohongshu pharma social-listening collection."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


THEMES: dict[str, dict[str, Any]] = {
    "career_insecurity": {
        "label": "职业流动、裁员离职与求职摩擦",
        "direction": "离职、裁员、PIP、gap、投递无反馈、转行焦虑、补偿谈判和外企岗位进入门槛。",
        "keywords": ["裁员", "离职", "协商", "补偿", "赔偿", "pip", "PIP", "失业", "裸辞", "gap", "招聘", "面试", "offer", "内推", "转行", "优化", "被裁", "劝退", "0个面试", "无反馈"],
        "unverified": "是否集中于特定公司、地区、年龄段、产品线或市场周期未证实。",
    },
    "sales_admin_kpi": {
        "label": "药代管理压力、KPI与流程内耗",
        "direction": "表格、打卡、扫码、会议、考试、晨访、复盘、领导PUA占用销售/客户时间。",
        "keywords": ["作业", "表格", "填表", "打卡", "KPI", "kpi", "扫码", "早会", "晚会", "复盘", "会议", "考试", "pua", "PUA", "晨访", "拜访", "指标", "药代", "医药代表", "领导"],
        "unverified": "哪些属于公司制度、区域执行或经理个人管理风格未证实。",
    },
    "compliance_meeting": {
        "label": "合规高压、会议规则收紧与责任下沉",
        "direction": "SOP、审批、审计、飞检、讲者、参会人数、线上摄像头、报销垫付与责任下沉。",
        "keywords": ["合规", "SOP", "sop", "审批", "飞检", "讲者", "会议", "摄像头", "参会", "外部", "内审", "审计", "报销", "垫付", "发票", "责任", "新规"],
        "qualifier_any": ["合规", "SOP", "sop", "审批", "飞检", "讲者", "摄像头", "参会", "内审", "审计", "报销", "垫付", "发票", "新规"],
        "unverified": "具体公司政策真实性、适用范围和执行强度未证实。",
    },
    "medical_ai": {
        "label": "医学部、MA/MSL/临床岗位的AI与外包压力",
        "direction": "AI压缩文献、医学写作、问询、MSL准备、CRA/DM/RWE等知识工作，同时存在审计和归责反驳。",
        "keywords": ["AI", "ai", "人工智能", "医学部", "MSL", "msl", "MA", "ma", "CRA", "cra", "DM", "dm", "文献", "医学写作", "medical", "RWE", "rwe", "临床", "研究", "问询", "外包", "压价", "替代"],
        "qualifier_any": ["医学部", "MSL", "msl", "MA", "ma", "CRA", "cra", "DM", "dm", "文献", "医学写作", "问询", "外包", "压价", "替代", "绞杀", "药代", "临床"],
        "unverified": "AI是否已经导致裁撤、压价或岗位重构，以及哪些任务可被合规替代未证实。",
    },
    "role_boundary": {
        "label": "MA/MSL/市场/销售的角色边界混杂",
        "direction": "MA、MSL、sales、市场、CRO、全球数据和AE答复等工作边界不清，夹心压力上升。",
        "keywords": ["夹心", "职责", "边界", "cross", "sales", "销售", "市场部", "mkt", "MKT", "MA", "MSL", "BD", "PM", "CRO", "AE", "insight", "策略", "材料审核"],
        "unverified": "角色混杂是否普遍，以及成因是组织设计、资源不足还是合规要求未证实。",
    },
    "info_asymmetry": {
        "label": "药企黑话、公司口碑与信息不透明",
        "direction": "P司/N司/NN司/LL司/AZ/R司/S司等黑话用于吃瓜、规避直呼公司名和判断雇主口碑。",
        "keywords": ["P司", "N司", "NN司", "LL司", "L司", "AZ", "R司", "S司", "M司", "J司", "B司", "花名", "缩写", "大瓜", "瓜", "排名", "待遇排名", "哪家", "refe", "refer"],
        "unverified": "简称稳定性、跨圈层通用性、多义简称消歧未证实。",
    },
    "compensation_benefits": {
        "label": "薪资、奖金、福利与费用压力",
        "direction": "待遇、奖金、福利、N+补偿、报销周期、垫付现金流与薪资性价比。",
        "keywords": ["薪资", "工资", "待遇", "奖金", "福利", "N+", "n+", "base", "报销", "垫付", "补偿", "赔偿", "低薪", "无奖金", "底薪"],
        "unverified": "实际薪酬水平、福利政策和费用周期需要公司/岗位/地区维度验证。",
    },
    "data_learning_curve": {
        "label": "药企数据、临床与RWE学习曲线",
        "direction": "临床试验、终点、AE、RWE、数据质量、解释性、合规周期造成跨界/数据岗位学习负担。",
        "keywords": ["数据", "RWE", "rwe", "endpoint", "终点", "AE", "临床试验", "data quality", "数据质量", "解释性", "合规周期", "建模", "模型", "统计"],
        "qualifier_any": ["RWE", "rwe", "endpoint", "终点", "AE", "临床试验", "data quality", "数据质量", "解释性", "合规周期", "建模", "模型", "统计"],
        "unverified": "目前多为专业岗位单点经验，是否行业普遍未证实。",
    },
}

ROLE_TERMS = ["药代", "医药代表", "MSL", "MA", "医学部", "合规", "HR", "市场", "mkt", "临床", "CRA", "BD", "药企打工", "外企", "药企"]
FIRST_PERSON_TERMS = ["我", "本人", "入职", "离职", "待了", "工作", "面试", "协商", "裸辞", "投递", "转行", "被裁"]
NEGATIVE_TERMS = ["惨", "焦虑", "绝望", "裁员", "离职", "被裁", "PIP", "pua", "PUA", "压价", "绞杀", "劝退", "无奖金", "失业", "太狠", "大乱", "避雷"]
FOREIGN_COMPANY_TERMS = ["外资", "外企", "诺华", "辉瑞", "礼来", "诺和", "诺和诺德", "阿斯利康", "罗氏", "赛诺菲", "默沙东", "强生", "GSK", "武田", "拜耳", "安进", "艾伯维", "BMS", "吉利德", "P司", "N司", "NN司", "LL司", "AZ", "R司", "S司", "M司", "J司"]


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def comment_key(row: dict[str, Any]) -> str:
    """Match the collector's stable comment deduplication key."""
    if row.get("comment_id"):
        return str(row["comment_id"])
    return "|".join([
        str(row.get("note_id") or row.get("note_url") or ""),
        str(row.get("userId") or row.get("author") or ""),
        str(row.get("time") or ""),
        str(row.get("text") or "")[:160],
    ])


def parse_count(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip().replace(",", "")
    mult = 1
    if text.endswith("万"):
        mult = 10000
        text = text[:-1]
    elif text.endswith("k") or text.endswith("K"):
        mult = 1000
        text = text[:-1]
    try:
        return int(float(text) * mult)
    except ValueError:
        nums = re.findall(r"\d+", text)
        return int(nums[0]) if nums else 0


def norm_text(*parts: Any) -> str:
    return " ".join(str(p or "") for p in parts)


def contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def hit_count(text: str, terms: list[str]) -> int:
    return sum(text.count(term) for term in terms)


def note_record(row: dict[str, Any]) -> dict[str, Any]:
    detail = row.get("detail") or {}
    title = detail.get("title") or row.get("search_title") or ""
    content = detail.get("content") or ""
    author = detail.get("author") or row.get("search_author") or ""
    likes = parse_count(detail.get("likes") or row.get("search_likes"))
    collects = parse_count(detail.get("collects"))
    comments = parse_count(detail.get("comments"))
    tags = detail.get("tags") or ""
    return {
        "note_id": row.get("note_id"),
        "url": row.get("url"),
        "queries": row.get("queries") or [],
        "title": title,
        "content": content,
        "author": author,
        "likes": likes,
        "collects": collects,
        "comment_count": comments,
        "tags": tags,
        "has_detail": True,
        "text": norm_text(title, content, tags, " ".join(row.get("queries") or [])),
    }


def search_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "note_id": row.get("note_id"),
        "url": row.get("url"),
        "queries": [row.get("query")] if row.get("query") else [],
        "title": row.get("title") or "",
        "content": "",
        "author": row.get("author") or "",
        "likes": parse_count(row.get("likes")),
        "collects": 0,
        "comment_count": 0,
        "tags": "",
        "has_detail": False,
        "text": norm_text(row.get("title"), row.get("author"), row.get("query")),
    }


def classify_text(text: str) -> list[str]:
    hits = []
    for key, theme in THEMES.items():
        if not contains_any(text, theme["keywords"]):
            continue
        qualifier = theme.get("qualifier_any")
        if qualifier and not contains_any(text, qualifier):
            continue
        if key == "medical_ai" and ("AI" in text or "ai" in text or "人工智能" in text):
            pressure_terms = ["压价", "替代", "绞杀", "外包", "裁员", "问询", "文献", "医学写作", "MSL", "MA", "CRA", "DM", "医学部", "药代"]
            if not contains_any(text, pressure_terms):
                continue
        if key == "career_insecurity":
            weak_terms = ["面试", "offer", "内推", "招聘"]
            strong_terms = ["裁员", "离职", "协商", "补偿", "赔偿", "pip", "PIP", "失业", "裸辞", "gap", "转行", "优化", "被裁", "劝退", "0个面试", "无反馈"]
            if contains_any(text, weak_terms) and not contains_any(text, strong_terms + ROLE_TERMS):
                continue
        hits.append(key)
    return hits


def scale_log(value: int, max_value: int, points: int) -> float:
    if value <= 0 or max_value <= 0:
        return 0.0
    return min(points, points * math.log1p(value) / math.log1p(max_value))


def pct(value: float) -> str:
    return f"{value:.1f}"


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def top_terms(texts: list[str], limit: int = 20) -> list[tuple[str, int]]:
    tokens: Counter[str] = Counter()
    pattern = re.compile(r"[A-Za-z]{2,}|[\u4e00-\u9fff]{2,6}")
    stop = {"药企", "外企", "外资", "医药", "代表", "一个", "现在", "真的", "可以", "没有", "什么", "怎么", "工作", "公司", "这个", "就是", "还是"}
    for text in texts:
        for token in pattern.findall(text):
            if token not in stop:
                tokens[token] += 1
    return tokens.most_common(limit)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--top-links", type=int, default=12)
    parser.add_argument("--top-comments", type=int, default=12)
    args = parser.parse_args()

    in_dir = Path(args.input_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    search_rows = read_jsonl(in_dir / "search_results.jsonl")
    detail_rows = read_jsonl(in_dir / "note_details.jsonl")
    comments = read_jsonl(in_dir / "comments.jsonl")
    errors = read_jsonl(in_dir / "errors.jsonl")

    notes_by_id: dict[str, dict[str, Any]] = {}
    for row in search_rows:
        rec = search_record(row)
        if rec["note_id"] and rec["note_id"] not in notes_by_id:
            notes_by_id[rec["note_id"]] = rec
    for row in detail_rows:
        rec = note_record(row)
        if rec["note_id"]:
            base = notes_by_id.get(rec["note_id"], {})
            queries = list(dict.fromkeys((base.get("queries") or []) + (rec.get("queries") or [])))
            rec["queries"] = queries
            notes_by_id[rec["note_id"]] = rec

    note_theme_hits: dict[str, set[str]] = defaultdict(set)
    comment_theme_hits: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for note_id, note in notes_by_id.items():
        for theme in classify_text(note["text"]):
            note_theme_hits[theme].add(note_id)

    for c in comments:
        text = str(c.get("text") or "")
        for theme in classify_text(text):
            comment_theme_hits[theme].append(c)

    max_heat = 1
    theme_raw: dict[str, dict[str, Any]] = {}
    for key in THEMES:
        note_ids = note_theme_hits.get(key, set())
        theme_comments = comment_theme_hits.get(key, [])
        theme_notes = [notes_by_id[nid] for nid in note_ids if nid in notes_by_id]
        heat = sum(n["likes"] + n["collects"] + n["comment_count"] for n in theme_notes)
        heat += sum(parse_count(c.get("likes")) for c in theme_comments)
        max_heat = max(max_heat, heat)
        theme_raw[key] = {
            "notes": theme_notes,
            "comments": theme_comments,
            "heat": heat,
            "comment_count": len(theme_comments),
            "note_count": len(theme_notes),
        }

    score_rows: list[dict[str, Any]] = []
    for key, data in theme_raw.items():
        theme = THEMES[key]
        notes = data["notes"]
        comments_for_theme = data["comments"]
        note_count = data["note_count"]
        comment_count = data["comment_count"]
        detail_note_count = sum(1 for n in notes if n.get("has_detail"))
        search_only_count = note_count - detail_note_count
        heat = data["heat"]
        all_texts = [n["text"] for n in notes] + [str(c.get("text") or "") for c in comments_for_theme]
        combined = "\n".join(all_texts)

        heat_score = scale_log(heat, max_heat, 20)
        weighted_note_count = detail_note_count + search_only_count * 0.35
        repetition_score = min(20.0, weighted_note_count * 1.3 + min(comment_count, 80) * 0.12)
        role_hits = sum(1 for n in notes if contains_any(n["text"], ROLE_TERMS))
        first_person_hits = sum(1 for n in notes if contains_any(n["text"], FIRST_PERSON_TERMS))
        source_score = min(15.0, role_hits * 1.4 + first_person_hits * 1.4 + min(note_count, 8) * 0.7)
        comment_validation_score = min(15.0, comment_count * 0.22 + len({c.get("userId") or c.get("author") for c in comments_for_theme}) * 0.08)
        specificity_score = min(15.0, hit_count(combined, theme["keywords"]) * 0.35 + min(note_count, 8) * 0.8)
        negative_score = min(10.0, hit_count(combined, NEGATIVE_TERMS) * 0.5)
        confidence_score = min(5.0, 1.0 + note_count * 0.45 + min(comment_count, 40) * 0.04)
        total = heat_score + repetition_score + source_score + comment_validation_score + specificity_score + negative_score + confidence_score

        foreign_notes = sum(1 for n in notes if contains_any(n["text"], FOREIGN_COMPANY_TERMS))
        confidence_label = "高" if note_count >= 8 and comment_count >= 30 else "中" if note_count >= 3 and comment_count >= 8 else "低"
        score_rows.append({
            "theme_key": key,
            "痛点主题": theme["label"],
            "讨论方向": theme["direction"],
            "笔记数": note_count,
            "正文笔记数": detail_note_count,
            "评论证据数": comment_count,
            "互动热度": heat,
            "外资/公司信号笔记数": foreign_notes,
            "heat_score": round(heat_score, 2),
            "repetition_score": round(repetition_score, 2),
            "source_proximity_score": round(source_score, 2),
            "comment_validation_score": round(comment_validation_score, 2),
            "specificity_score": round(specificity_score, 2),
            "negative_intensity_score": round(negative_score, 2),
            "confidence_score": round(confidence_score, 2),
            "排序评分": round(total, 1),
            "置信度": confidence_label,
            "未证实点": theme["unverified"],
            "高频词": "、".join([term for term, _ in top_terms(all_texts, 12)]),
        })

    score_rows.sort(key=lambda r: r["排序评分"], reverse=True)
    for idx, row in enumerate(score_rows, start=1):
        row["排名"] = idx

    note_evidence_rows: list[dict[str, Any]] = []
    comment_evidence_rows: list[dict[str, Any]] = []
    used_note_evidence: set[str] = set()
    used_comment_evidence: set[str] = set()
    for row in score_rows:
        key = row["theme_key"]
        notes = sorted(theme_raw[key]["notes"], key=lambda n: (bool(n.get("has_detail")), n["likes"] + n["collects"] + n["comment_count"]), reverse=True)
        added_notes = 0
        for n in notes:
            evidence_key = str(n.get("note_id") or n.get("url") or "")
            if evidence_key in used_note_evidence:
                continue
            used_note_evidence.add(evidence_key)
            note_evidence_rows.append({
                "theme_key": key,
                "痛点主题": row["痛点主题"],
                "title": n["title"],
                "author": n["author"],
                "url": n["url"],
                "likes": n["likes"],
                "collects": n["collects"],
                "comments": n["comment_count"],
                "queries": ";".join(n.get("queries") or []),
                "source_level": "detail" if n.get("has_detail") else "search",
                "excerpt": (n["content"] or n["title"])[:240],
            })
            added_notes += 1
            if added_notes >= args.top_links:
                break
        comments_sorted = sorted(theme_raw[key]["comments"], key=lambda c: parse_count(c.get("likes")), reverse=True)
        added_comments = 0
        for c in comments_sorted:
            evidence_key = comment_key(c)
            if evidence_key in used_comment_evidence:
                continue
            used_comment_evidence.add(evidence_key)
            comment_evidence_rows.append({
                "theme_key": key,
                "痛点主题": row["痛点主题"],
                "note_title": c.get("note_title"),
                "note_url": c.get("note_url"),
                "comment_author": c.get("author"),
                "comment_likes": parse_count(c.get("likes")),
                "is_reply": c.get("is_reply"),
                "text": str(c.get("text") or "")[:260],
            })
            added_comments += 1
            if added_comments >= args.top_comments:
                break

    collection_row_count = len(search_rows) + len(detail_rows) + len(comments)
    independent_evidence_count = len(notes_by_id) + len({comment_key(c) for c in comments if comment_key(c)})
    summary = {
        "generated_at": now_iso(),
        "input_dir": str(in_dir),
        "search_result_rows": len(search_rows),
        "note_detail_rows": len(detail_rows),
        "comment_rows": len(comments),
        "collection_row_count": collection_row_count,
        "raw_item_count": collection_row_count,
        "unique_notes": len(notes_by_id),
        "independent_evidence_count": independent_evidence_count,
        "dedup_raw_items": independent_evidence_count,
        "evidence_notes_rows": len(note_evidence_rows),
        "evidence_comments_rows": len(comment_evidence_rows),
        "evidence_dedupe_rule": "Representative evidence tables are globally deduplicated across topics by note key and comment key. Topic counts still count every classified theme hit.",
        "error_rows": len(errors),
        "topics": len(score_rows),
        "scoring": "heat20 + repetition20 + source_proximity15 + comment_validation15 + specificity15 + negative_intensity10 + confidence5",
    }

    write_csv(out_dir / "topic_scores.csv", score_rows, [
        "排名", "theme_key", "痛点主题", "讨论方向", "笔记数", "正文笔记数", "评论证据数", "互动热度", "外资/公司信号笔记数",
        "heat_score", "repetition_score", "source_proximity_score", "comment_validation_score",
        "specificity_score", "negative_intensity_score", "confidence_score", "排序评分", "置信度", "高频词", "未证实点",
    ])
    write_csv(out_dir / "evidence_notes.csv", note_evidence_rows, [
        "theme_key", "痛点主题", "title", "author", "url", "likes", "collects", "comments", "queries", "source_level", "excerpt",
    ])
    write_csv(out_dir / "evidence_comments.csv", comment_evidence_rows, [
        "theme_key", "痛点主题", "note_title", "note_url", "comment_author", "comment_likes", "is_reply", "text",
    ])
    (out_dir / "dataset_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines: list[str] = []
    lines.append("# 小红书外资药企员工痛点 Social Listening 报告")
    lines.append("")
    lines.append(f"生成时间：{summary['generated_at']}")
    lines.append("")
    lines.append("## 监测范围与样本")
    lines.append("")
    lines.append(f"- 搜索结果行：{summary['search_result_rows']}")
    lines.append(f"- 笔记详情行：{summary['note_detail_rows']}")
    lines.append(f"- 评论行：{summary['comment_rows']}")
    lines.append(f"- 采集记录行合计：{summary['collection_row_count']}（搜索行 + 详情行 + 评论行）")
    lines.append(f"- 去重笔记数：{summary['unique_notes']}")
    lines.append(f"- 独立证据项：{summary['independent_evidence_count']}（去重笔记 + 去重评论；详情行只丰富笔记，不重复计数）")
    lines.append(f"- 采集错误记录：{summary['error_rows']}")
    lines.append(f"- 代表证据表已跨主题去重：笔记 {summary['evidence_notes_rows']} 条，评论 {summary['evidence_comments_rows']} 条。")
    lines.append("")
    lines.append("结论边界：这是基于当前关键词矩阵和 OpenCLI 可见结果的样本内 social listening，不是小红书全平台总量统计。博主身份、公司政策真实性、公司/地区/产品线代表性均需另行验证。")
    lines.append("")
    lines.append("## 痛点排序总览")
    lines.append("")
    lines.append("| 排名 | 痛点主题 | 匹配笔记 | 正文笔记 | 评论证据 | 热度 | 评分 | 置信度 |")
    lines.append("|---:|---|---:|---:|---:|---:|---:|---|")
    for row in score_rows:
        lines.append(f"| {row['排名']} | {row['痛点主题']} | {row['笔记数']} | {row['正文笔记数']} | {row['评论证据数']} | {row['互动热度']} | {row['排序评分']} | {row['置信度']} |")
    lines.append("")
    lines.append("## 主题洞察")
    for row in score_rows:
        key = row["theme_key"]
        lines.append("")
        lines.append(f"### {row['排名']}. {row['痛点主题']}（{row['排序评分']}分，{row['置信度']}置信）")
        lines.append("")
        lines.append(f"- 讨论方向：{row['讨论方向']}")
        lines.append(f"- 样本信号：{row['笔记数']} 条匹配笔记，其中 {row['正文笔记数']} 条有正文详情；{row['评论证据数']} 条评论证据；互动热度 {row['互动热度']}。")
        lines.append(f"- 评分拆解：热度 {row['heat_score']} / 重复 {row['repetition_score']} / 来源贴近 {row['source_proximity_score']} / 评论验证 {row['comment_validation_score']} / 具体性 {row['specificity_score']} / 负向强度 {row['negative_intensity_score']} / 置信 {row['confidence_score']}。")
        lines.append(f"- 高频词：{row['高频词']}")
        lines.append(f"- 未证实点：{row['未证实点']}")
        lines.append("")
        lines.append("代表笔记：")
        notes = [n for n in note_evidence_rows if n["theme_key"] == key][:5]
        if notes:
            for n in notes:
                lines.append(f"- [{n['title']}]({n['url']})，作者：{n['author']}，赞/藏/评：{n['likes']}/{n['collects']}/{n['comments']}。")
        else:
            lines.append("- 无足够代表笔记。")
        comments_for_key = [c for c in comment_evidence_rows if c["theme_key"] == key][:5]
        if comments_for_key:
            lines.append("")
            lines.append("评论证据摘录：")
            for c in comments_for_key:
                text = str(c["text"]).replace("\n", " ")
                lines.append(f"- {text}（来自 [{c['note_title']}]({c['note_url']}), 评论赞 {c['comment_likes']}）")
    lines.append("")
    lines.append("## 方法附录")
    lines.append("")
    lines.append("评分公式：heat20 + repetition20 + source_proximity15 + comment_validation15 + specificity15 + negative_intensity10 + confidence5。当前没有可比历史窗口，因此未加入趋势突增分。")
    lines.append("")
    lines.append("证据纪律：没有足够证据时，不给确定原因或解决方案；只给已知事实、候选假设、验证路径，并标注未证实。")

    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
