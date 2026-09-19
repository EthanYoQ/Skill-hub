# PPT-Nano Skill — 多风格版

名称: PPT-Nano
路径: `skills/ppt-nano/`

---

## 风格选择（生成PPT前必选）

用户触发 ppt-nano 后，**先让用户选择风格**：

```
📋 请选择PPT风格：
1️⃣  白板板书风格 — 专业白板marker，蓝/红/黑三色，手绘图标
2️⃣  龙虾插画风格 — 傅盛龙虾吉祥物，蓝色单线条插图
3️⃣  极简文字风格 — 纯文字版，严肃商务场景
```

---

## 风格详情

### 1️⃣ 白板板书风格（推荐）
- **参考图**: `styles/whiteboard/combined_ref.jpg`（5张拼合）
- **特征**: 银色边框白板照片，蓝色大标题，黑色正文，红色重点，手绘简笔图标
- **适合**: 演讲汇报、专业分享、对外展示
- **Style Prompt**:
  ```
  realistic whiteboard marker illustration style, same as reference images,
  physical whiteboard with silver metal frame, blurred office background,
  bold colored marker text (blue for titles, black for body, red for emphasis),
  simple hand-drawn marker icons and diagrams, blue and red arrows and underlines,
  clean white board surface, ceiling lights visible, professional explainer whiteboard style
  ```

### 2️⃣ 龙虾插画风格
- **参考图**: `styles/lobster/ref.jpg`（傅盛开工仪式封面）
- **特征**: 龙虾吉祥物，蓝色单线条插图，活泼热闹
- **适合**: 内部分享、活动仪式、轻松场合

### 3️⃣ 极简文字风格
- **参考图**: 无
- **特征**: 大标题+要点列表，无复杂插图
- **适合**: 严肃商务、董事会汇报

---

## 完整工作流程

```
① 用户说"ppt-nano 做PPT"
② 询问主题、页数
③ 展示风格选项 → 用户选择
④ 逐页确认文案
⑤ AI生成预览图（含参考图）→ 发飞书
⑥ 用户审查 → 指定重做页面
⑦ 合成 .pptx 下载
```

---

## 核心生成命令

```python
import subprocess, json

SKILL_DIR = "/home/ubuntu/.openclaw/workspace/skills/ppt-nano"

STYLES = {
    "whiteboard": {
        "ref": f"{SKILL_DIR}/styles/whiteboard/combined_ref.jpg",
        "prompt": "realistic whiteboard marker style, silver frame whiteboard photo, bold blue marker title, black marker body text, red emphasis, hand-drawn icons, clean white board"
    },
    "lobster": {
        "ref": f"{SKILL_DIR}/styles/lobster/ref.jpg", 
        "prompt": "whiteboard single-line blue marker cartoon, lobster mascot, doodles, bold black title, red circles"
    },
    "minimal": {
        "ref": None,
        "prompt": "clean minimal whiteboard, large bold black marker title, neat bullet list, red underlines"
    }
}

def generate_page(style_key, page_prompt, ratio="16:9", size="1k"):
    style = STYLES[style_key]
    ref_part = f"@{style['ref']} " if style['ref'] else ""
    full_prompt = f"/nanobanana {ratio} {size} {ref_part}{style['prompt']}, {page_prompt}"
    result = subprocess.run(
        ["dvcode", "--output-format", "stream-json", "--yolo", full_prompt],
        capture_output=True, text=True, timeout=180
    )
    combined = result.stdout + result.stderr
    for line in combined.split('\n'):
        try:
            d = json.loads(line)
            if d.get('type') == 'nanobanana_completed':
                return d.get('image_urls', [None])[0]
        except: pass
    return None
```

---

## 文件结构

```
skills/ppt-nano/
├── README.md              # 本文件
├── styles/
│   ├── styles.json        # 风格配置
│   ├── whiteboard/
│   │   ├── ref1-5.jpg     # 5张原始参考图
│   │   └── combined_ref.jpg  # 拼合参考图（传给nanobanana）
│   └── lobster/
│       └── ref.jpg        # 龙虾风格参考图
└── ppt_nano.py            # 生成脚本（TODO）
```

---

## 注意事项

- nanobanana 只支持**单张参考图**，已用 PIL 将5张拼合
- 白板风格每页间隔 15 秒，避免 Vertex AI 限流
- 1K图片每张约消耗 50-54 积分
- python-pptx 合成时 16:9 = 10" × 5.625"

---

Version: 2.0 | 多风格支持 | 2026-02-26
