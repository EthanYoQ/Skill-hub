# -*- coding: utf-8 -*-
"""report-bundle-builder · 内部共用验证阈值常量.

3 个函数的"自动验证"使用以下默认阈值。调用者可通过 auto_validate=False 关闭,
或在自己的代码里读取这些常量做更严格的检查。
"""

# build_standalone_html
HTML_MIN_SIZE_BYTES = 1 * 1024 * 1024  # 1 MB
HTML_MIN_ANCHOR_COUNT = 1  # 至少 1 个子页 anchor

# build_pdf
PDF_MIN_SIZE_BYTES = 1 * 1024 * 1024  # 1 MB
PDF_MIN_PAGES = 1

# build_xlsx
XLSX_MIN_SIZE_BYTES = 1024  # 1 KB
XLSX_MIN_SHEET_COUNT = 1
