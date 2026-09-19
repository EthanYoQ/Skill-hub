# coze-agent-files: 群文件操作参考

**这是 coze-project skill 的群文件操作参考。** 触发条件 / 协作流程 / 跨技能衔接见同目录 [`SKILL.md`](./SKILL.md); 群信息查询 (info / member / message) 见 [`coze-agent-query.md`](./coze-agent-query.md)。本文件讲**群文件 CRUD 的详细语法 + shell 引用细节**。

需要敲 `coze agent file ...` 时 Read 本文件。

## CLI 调用约束 (所有 `coze agent` 命令通用)

**前提**:
- `coze` 在 PATH (平台保证), 已登录, 不要配 auth
- 每个命令必带 `--json` (省略 → `E1000 INVALID_ARGUMENT`)
- 每个命令必带 `--org-id "$account_id" --project-id "$group_id"` (从 `<coze-context>` 抄, 见 SKILL.md)

**输出信封** (stdout 成功):
```json
{ "code": 0, "msg": "...", "data": { ... } }
```

**校验两层才用结果**: shell 退出码 == 0 **且** `.code == 0` (可能 0 退出但软失败)。

`jq` 模板 (注意 stderr 必须捕到文件, 否则失败时错误原因丢失):
```bash
err=$(mktemp)
out=$(coze agent file read --org-id "$account_id" --project-id "$group_id" \
        --file-path "$path" --json 2>"$err") \
  || { cat "$err" >&2; rm -f "$err"; exit 1; }
rm -f "$err"
[ "$(echo "$out" | jq -r '.code')" = "0" ] \
  || { echo "API error: $out" >&2; exit 1; }
echo "$out" | jq '.data'
```

> ⚠️ **`$(...)` 只捕 stdout**——CLI 错误 JSON 走 stderr, 不重定向 (`2>"$err"`) 的话失败时 `$out` 是空的, 你完全看不到原因。这个 pattern 必须用, 不能省。

**错误码** (JSON 错误写 stderr, 非零退出):

| 代码 | 含义 | 怎么办 |
|---|---|---|
| `E1000` | 参数错 (缺 `--json` / 缺 ID / `--size`/`--limit` 非法) | 修命令重试 |
| `E5002` | 后端 / 服务端错 (`.code != 0`) | 把消息转给用户; **不要盲目重试** |

## 群文件路径语义 (⚠️ 必读)

**所有 `--file-path` 参数都是相对路径**, 相对的是**群文件目录根** (`.` 即群文件根)。**绝对不要传 `/` 开头的路径**, 后端会找不到。

- 列群文件根: `--file-path .` 或者不传 `--file-path`
- 根下的文件: `example.md` (✅) / `example.md` (❌)
- 子目录: `notes` (✅) / `/notes` (❌)
- 子目录下的文件: `notesexample.md` (✅) / `/notesexample.md` (❌)

`file list` 返回的 `file_path` 字段也是相对路径——后续 read / write / edit **直接拿来用**, 不要自己拼 `/`。

## 子命令一览

| 子命令 | 用途 |
|---|---|
| `agent file list` | 列群文件 / 目录树 |
| `agent file read` | 读群文件内容 |
| `agent file write` | 创建 / 整文件覆盖 |
| `agent file edit` | 外科手术式修改 (replace / append) |

下文 `$account_id` / `$group_id` 都指你从 `<coze-context>` 抄来的值。

## `agent file list` — 群文件目录列表

```bash
# 群文件工作区根目录
coze agent file list --org-id "$account_id" --project-id "$group_id" --json

# 特定子目录, 递归 10 层
coze agent file list \
  --org-id "$account_id" --project-id "$group_id" \
  --file-path "notes" \
  --depth 10 --json
```

参数:
- `--file-path`: 起始目录 (相对群文件根, e.g. `notes`; 不带或传 `.` 都是列群文件根)
- `--depth`: 递归深度 (不带则浅列表, 只列直接子项)

返回 `.data.files`, 每项含:
- `name`: 文件名 / 目录名
- `file_path`: 相对路径 (相对群文件根)
- `is_dir`: `true` 为目录, `false` 为文件

> **路径规范化坑**: 后端有时返回看着被规范化过的路径 (加了额外前缀 / 多了层级 / 跟你输入的形状不同)。**后续读 / 写继续用你最初的用户面向路径**, 不要替换成后端规范化版本——否则后续 read / edit 会找不到文件。

## `agent file read` — 读群文件

```bash
# 整文件
coze agent file read \
  --org-id "$account_id" --project-id "$group_id" \
  --file-path "example.md" --json

# 仅第 1–20 行
coze agent file read \
  --org-id "$account_id" --project-id "$group_id" \
  --file-path "example.md" \
  --offset 1 --limit 20 --json
```

参数:
- `--file-path`: **必填**, 群文件**相对路径** (相对群文件根)
- `--offset`: 起始行号 (从 1 开始)
- `--limit`: 读多少行

返回 `.data`:
- `.content`: 文件正文 (字符串)
- `.start_line` / `.end_line`: 实际拿到的行范围
- `.size`: 文件总大小 (字节)

> 大文件探索时**先读窗口** (`--offset` / `--limit`), 不要一次读整文件——既费 token 又可能撑爆。

## `agent file write` — 创建或整文件覆盖

```bash
coze agent file write \
  --org-id "$account_id" --project-id "$group_id" \
  --file-path "example.md" \
  --content "# title" --json
```

参数:
- `--file-path`: **必填**, 群文件**相对路径** (相对群文件根); 不存在的中间目录后端会**自动创建**
- `--content`: **必填**, 整文件内容 (字符串, 不是 diff)

⚠️ `file write` **覆盖整个文件**, 没有 merge。**只改一部分用 `file edit`**, 既不会误截断, 又避开 shell 引用长内容的问题。

适用场景:
- 新建文件 (e.g. 第一次沉淀本周周报)
- 文件结构整体重写 (确认要全覆盖)

## `agent file edit` — 外科手术式修改

任务是"编辑"或"更新"群文件时, 通常这个比 write 合适。按意图选模式:

| 模式 | 用途 | 必需参数 |
|---|---|---|
| `replace_one` | 替换唯一字符串第一次出现。先读文件、有明确锚点的外科手术编辑首选。 | `--old-string`, `--new-string` |
| `replace_all` | 全局重命名 / 全局替换。 | `--old-string`, `--new-string` |
| `append` | 文件末尾追加, 无前导换行。 | `--append-content` |
| `append_newline` | 文件末尾新起一行追加。**"追加新条目"几乎都该选这个**, 不是 `append`。 | `--append-content` |

```bash
# 全局重命名 config
coze agent file edit \
  --org-id "$account_id" --project-id "$group_id" \
  --file-path "config.md" \
  --mode replace_all \
  --old-string "model: gpt-4" --new-string "model: claude-sonnet-4-5" --json

# 追加新 todo 条目
coze agent file edit \
  --org-id "$account_id" --project-id "$group_id" \
  --file-path "todo.md" \
  --mode append_newline \
  --append-content "- review PR #42" --json
```

**`replace_one` 用法关键点**:
- **先 `file read` 看一下**, 找出在文件里明显唯一的 `--old-string` 锚点
- 锚点太短或重复出现, 会改错位置或失败
- 把锚点选得比要替换的核心多带一两行上下文是常见做法

**`append` vs `append_newline`**:
- 想在已有最后一行尾巴继续接 → `append`
- 想起新一行 (新 todo、新章节) → `append_newline` (默认偏好这个)

## Shell 引用提示 (主要踩坑点在 file write/edit)

`--content` / `--old-string` / `--new-string` / `--append-content` 都是普通 shell 参数, 引用要小心:

- **纯 ASCII 无引号无 `$`**: 双引号即可 — `--content "hello world"`
- **含双引号或 shell 元字符 (`$`、` ` `、`!`)**: 单引号整段, 或用 `$'...'` C 风格字面量
- **多行内容**: heredoc 灌变量最稳:
  ```bash
  content=$(cat <<'EOF'
  line 1
  line 2 with "quotes" and $vars not expanded
  EOF
  )
  coze agent file write --org-id "$account_id" --project-id "$group_id" \
    --file-path a.md --content "$content" --json
  ```
  (注意 `<<'EOF'` 加引号——防止变量在 heredoc 里被展开)
- **超长内容 (几百 KB 起)**: 命令行参数长度可能爆 (`E2BIG`)。先 `file write` 写个骨架, 后续 `file edit append_newline` 增量补
- **内容里有反引号 / `$(...)`**: 一定走单引号或 heredoc, 否则 shell 会执行命令替换

## 不要做的事 (文件操作层面)

- ❌ 不要省 `--json` 或忽略信封 `.code` 校验 (见顶部"CLI 调用约束")
- ❌ 不要用 `file write` 做小编辑 — 用 `file edit replace_one`, 既安全又不烦引用
- ❌ 不要 `replace_one` 不先 `read` — 锚点可能不唯一, 改错位置
- ❌ 不要 `replace_all` 用模糊锚点 — 全局替换出错就遍布全文
- ❌ 不要把后端规范化路径替换回去 — 后续调用继续用用户面向路径
- ❌ 不要把超大内容直接喂 `--content` — `E2BIG`; 先骨架后追加
- ❌ 不要 `append` 当 `append_newline` 用 — `append` 不加换行, 新条目会粘到上一行尾巴
- ❌ 不要相信 "`file write` 也能 merge" — 它就是整覆盖, 没有 merge 语义
- ❌ 不要忽略 heredoc 引号 — `<<EOF` 会展开 `$var`, `<<'EOF'` 才是字面量
