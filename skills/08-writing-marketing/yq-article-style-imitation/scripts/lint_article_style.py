#!/usr/bin/env python3
"""Scan publishable article drafts for source leakage and AI/report language."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PATTERNS: list[tuple[str, str]] = [
    ("naked URL", r"https?://|www\."),
    ("inline source label", r"来源[:：]"),
    ("known-facts label", r"已知事实"),
    ("candidate-hypothesis label", r"候选假设"),
    ("verification-path label", r"验证路径"),
    ("risk-gate label", r"风险门|Public Risk Gate"),
    ("quality metadata", r"Quality Score|质量评分|Safe Publication Notes"),
    ("AI/report word: root cause", r"根因"),
    ("AI/report word: write dead", r"写死"),
    ("AI/report word: boundary", r"边界"),
    ("AI-ish triad from failed draft", r"清楚、可查、负责任"),
    ("AI-ish experience phrasing", r"经验里"),
    ("failed-draft sentence", r"这也是这篇文章目前能走到的边界"),
    ("meta-writing: writing this topic", r"所以[，,]\s*写|写[\"“][^\"”]{2,40}[\"”]"),
    ("meta-writing: this article", r"这篇文章|本文|这篇稿|这次写作"),
    ("meta-investigation: if we want to clarify", r"如果要把.{0,20}查清楚|要把.{0,20}查清楚"),
    ("meta-investigation: start from big word", r"不能从.{0,20}这个大词开始|从.{0,20}这个大词开始"),
    ("report-like warning", r"最危险的是"),
    ("abstract accountability closer", r"责任才找得到位置"),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("article", type=Path)
    args = parser.parse_args()

    text = args.article.read_text(encoding="utf-8")
    lines = text.splitlines()
    findings: list[str] = []

    for label, pattern in PATTERNS:
        regex = re.compile(pattern, re.IGNORECASE)
        for idx, line in enumerate(lines, start=1):
            if regex.search(line):
                findings.append(f"{args.article}:{idx}: {label}: {line.strip()}")

    if findings:
        print("\n".join(findings))
        return 1

    print(f"OK: no source leakage or AI/report-language markers found in {args.article}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
