#!/usr/bin/env python3
"""
Quick start a new WeChat article with template
"""
import argparse
from pathlib import Path
from datetime import datetime


def create_article(title: str, topic: str = ""):
    """Create new article file from template"""
    drafts_dir = Path(__file__).parent.parent / "drafts"
    drafts_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{title.replace(' ', '_')}.md"
    
    template = f"""# {title}

## 写作计划

**主题：** {topic or "待定"}

**目标读者：** 

**核心观点：** 

**关键数据/案例：**
- 

---

## 文章正文

### 开头 (100-150字)

*用故事、数据或问题勾起兴趣。直白说明文章解决什么问题。*

---

### 主体观点

#### 观点 1

*观点 + 案例 + 解释*

---

#### 观点 2

*观点 + 案例 + 解释*

---

#### 观点 3

*观点 + 案例 + 解释*

---

### 结尾 (100-150字)

*总结核心观点,留下思考或行动建议*

---

## 发布前检查清单

- [ ] 标题是否能引起好奇心或共鸣?
- [ ] 开头 30 秒能抓住读者吗?
- [ ] 有具体故事或数据吗?
- [ ] 避免了大白话或学术语言吗?
- [ ] 段落长度合适吗?
- [ ] 有清晰的结尾吗?
- [ ] 检查了错别字和语病吗?

## 提示

**傅盛写作风格:**
- ✅ 口语化,像跟朋友聊天
- ✅ 用故事代替说教
- ✅ 有态度和观点
- ✅ 简化复杂的东西
- ✅ 短句 + 多换行

**避免:**
- ❌ AI 八股文
- ❌ 模棱两可
- ❌ 数据堆砌
- ❌ 长句子
- ❌ 空洞的词汇
"""
    
    file_path = drafts_dir / filename
    file_path.write_text(template, encoding='utf-8')
    
    print(f"✅ Article created: {file_path}")
    print(f"\n💡 Next steps:")
    print(f"   1. Edit the article: {file_path}")
    print(f"   2. Polish the text: python3 scripts/polish_text.py {file_path}")
    print(f"   3. Generate cover: python3 scripts/generate_cover.py --title \"{title}\" --style modern")
    
    return str(file_path)


def main():
    parser = argparse.ArgumentParser(description="Create new WeChat article")
    parser.add_argument("title", help="Article title")
    parser.add_argument("--topic", default="", help="Article topic (optional)")
    
    args = parser.parse_args()
    create_article(args.title, args.topic)


if __name__ == "__main__":
    main()
