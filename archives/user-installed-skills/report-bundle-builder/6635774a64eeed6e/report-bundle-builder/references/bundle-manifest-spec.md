# delivery_manifest.json 规范

`build_all_deliverables` 输出的 JSON 文件,记录三件交付物状态。

## 完整 schema

```json
{
  "deliverables": {
    "html": {
      "ok": true,
      "out_path": "out/report_standalone.html",
      "size_mb": 9.34,
      "png_count": 8,
      "missing_pngs": [],
      "validation": {
        "size_ok": true,
        "size_bytes": 9803264,
        "anchor_count": 6,
        "anchor_target": 6,
        "base64_png_count": 8
      }
    },
    "pdf": {
      "ok": true,
      "out_path": "out/report_standalone.pdf",
      "size_mb": 9.56,
      "pages": 32,
      "mode": "two-pass",
      "validation": {
        "size_ok": true,
        "size_bytes": 10024096,
        "pages": 32,
        "pages_unknown": false,
        "pages_ok": true
      }
    },
    "xlsx": {
      "ok": false,
      "error": "FileNotFoundError: schema.yaml missing",
      "label": "xlsx"
    }
  },
  "generated_at": "2026-04-25T18:30:00+00:00",
  "skill_version": "report-bundle-builder/1.0",
  "disease_slug": "lung-tb-china",
  "input_dir": "/path/to/report_dir",
  "output_dir": "/path/to/out_dir",
  "manifest_path": "out/delivery_manifest.json"
}
```

## 字段说明

### 顶层

| 字段 | 类型 | 说明 |
|------|------|------|
| `deliverables` | dict | 三件交付物状态,key = "html" / "pdf" / "xlsx" |
| `generated_at` | ISO 8601 | UTC 时间戳 |
| `skill_version` | str | `report-bundle-builder/1.0` |
| `disease_slug` | str | 调用方传入(默认 `"unknown"`) |
| `input_dir` | str | report_dir 绝对路径 |
| `output_dir` | str | out_dir 绝对路径 |
| `manifest_path` | str | 本 manifest 文件路径(只在返回 dict 中,不写入文件本身) |

### deliverables.html

| 字段 | 类型 | 说明 |
|------|------|------|
| `ok` | bool | 文件已生成且验证通过 |
| `out_path` | str | 输出 HTML 路径 |
| `size_mb` | float | 文件大小,2 位小数 |
| `png_count` | int | 内嵌的 PNG 数 |
| `missing_pngs` | list[str] | 主页/子页中引用但找不到的 PNG src 路径 |
| `validation` | dict | 见下 |

`html.validation` 子键:`size_ok`、`size_bytes`、`anchor_count`、`anchor_target`、`base64_png_count`。

### deliverables.pdf

| 字段 | 类型 | 说明 |
|------|------|------|
| `ok` | bool | 文件已生成且验证通过 |
| `out_path` | str | 输出 PDF 路径 |
| `size_mb` | float | 文件大小 |
| `pages` | int \| None | 页数(pypdf/PyPDF2 都不可用时为 None) |
| `mode` | str | `"one-pass"`(无 toc_anchors)\| `"two-pass"`(注入页码) |
| `fallback_input` | bool? | 仅 HTML 失败 fallback 渲染 main_html 时存在并为 true |
| `fallback_reason` | str? | 仅 fallback 时存在,值 `"html_build_failed_used_main_html"` |
| `validation` | dict | 见下 |

`pdf.validation` 子键:`size_ok`、`size_bytes`、`pages`、`pages_unknown`、`pages_ok`。

### deliverables.xlsx

成功时与 html/pdf 类似(`ok` / `out_path` / `size_mb` / `sheets: list[str]` / `validation`)。

跳过时(`xlsx_schema` 或 `xlsx_data` 缺失):
```json
{
  "ok": false,
  "error": "xlsx_schema or xlsx_data missing — skipped",
  "label": "xlsx"
}
```

任一函数抛异常时(由 `_safe_call` 包成):
```json
{
  "ok": false,
  "error": "FileNotFoundError: schema.yaml missing",
  "label": "xlsx"
}
```

## 用法示例

```python
import json
from pathlib import Path

manifest = json.loads(Path("out/delivery_manifest.json").read_text(encoding="utf-8"))

# 检查全部就绪
all_ok = all(d["ok"] for d in manifest["deliverables"].values())
if not all_ok:
    print("失败的交付物:")
    for k, d in manifest["deliverables"].items():
        if not d["ok"]:
            print(f"  - {k}: {d.get('error', 'unknown')}")

# 拿 HTML 路径直接发邮件
if manifest["deliverables"]["html"]["ok"]:
    html_path = manifest["deliverables"]["html"]["out_path"]
    print(f"可发送: {html_path}")
```
