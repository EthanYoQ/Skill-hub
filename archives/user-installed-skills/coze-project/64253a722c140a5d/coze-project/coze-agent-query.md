# coze-agent-query: 群信息查询参考

**这是 coze-project skill 的群信息查询参考。** 触发条件 / 协作流程 / 跨技能衔接见同目录 [`SKILL.md`](./SKILL.md); 群文件 CRUD 操作见 [`coze-agent-files.md`](./coze-agent-files.md)。本文件讲**项目元数据 / 群成员 / 群消息历史查询的详细语法**。

需要敲 `coze agent info` / `member` / `message` 时 Read 本文件。

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
out=$(coze agent info --org-id "$account_id" --project-id "$group_id" --json 2>"$err") \
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

## 子命令一览

| 子命令 | 用途 | 用户提问示例 |
|---|---|---|
| `agent info` | 项目元数据 | "这个项目是啥", "项目设置" |
| `agent member list` | 群成员 | "谁在群里", "有谁的权限" |
| `agent message list` | 群聊历史 | "上次说啥", "之前讨论过的结论" |

下文 `$account_id` / `$group_id` 都指你从 `<coze-context>` 抄来的值。

## `agent info` — 项目元数据

```bash
coze agent info --org-id "$account_id" --project-id "$group_id" --json
```

返回项目完整记录在 `.data` 下:
- `name`: 项目 / 群名
- `description`: 项目描述
- `owner_id` / `owner_name`: 所有者
- `created_at` / `updated_at`: 时间戳
- 其他设置字段

**典型用法**:

```bash
# 拿项目名
name=$(coze agent info --org-id "$account_id" --project-id "$group_id" --json \
       | jq -r '.data.name')

# 整个元数据展示给用户
coze agent info --org-id "$account_id" --project-id "$group_id" --json | jq '.data'
```

## `agent member list` — 群成员

```bash
coze agent member list --org-id "$account_id" --project-id "$group_id" --json
```

返回成员列表在 `.data` 下, 每项含:
- `user_id`: 用户 ID
- `name` / `username`: 名字
- `role`: 权限角色 (owner / admin / member 等)
- 加入时间等

**典型用法**:

```bash
# 列出所有成员名 + 角色
coze agent member list --org-id "$account_id" --project-id "$group_id" --json \
  | jq -r '.data[] | "\(.role): \(.name)"'

# 找 owner
coze agent member list --org-id "$account_id" --project-id "$group_id" --json \
  | jq -r '.data[] | select(.role == "owner") | .name'
```

## `agent message list` — 群聊历史

```bash
# 最近 5 条
coze agent message list --org-id "$account_id" --project-id "$group_id" --size 5 --json

# 最旧的在前, 包含被引用的消息
coze agent message list --org-id "$account_id" --project-id "$group_id" \
  --asc-mode --need-reference --json

# 下一页
coze agent message list --org-id "$account_id" --project-id "$group_id" \
  --cursor "$next_cursor" --json
```

参数:
- `--size`: 每次最大 **10** (硬上限, 多了 CLI 拒绝)。要拿超过 10 条**必须**用 `--cursor` 翻页
- `--asc-mode`: 翻为最旧在前 (默认最新在前)
- `--need-reference`: 内联包含被引用 / 被回复的消息
- `--conversation-id`: 项目里有多个会话时过滤到单个

返回 `.data` 含消息数组 + 翻页游标, 但**具体字段名 (e.g. `messages` / `items` / `list`, `next_cursor` / `cursor` / `nextToken`) 以 CLI 实际返回为准**——不要凭印象猜。

**翻页累积 pattern** (用户要"最近 30 条"):

```bash
# === 第一步必做: 探字段名 (不要跳过这步直接用下面的模板) ===
first=$(coze agent message list --org-id "$account_id" --project-id "$group_id" \
        --size 1 --json)
echo "$first" | jq '.data | keys'
# 看输出, 找出消息数组字段名和游标字段名,
# 在下面把 <MSG_FIELD> 和 <CURSOR_FIELD> 替换成实际字段名

# === 第二步: 翻页累积 (替换 <MSG_FIELD> / <CURSOR_FIELD> 后再运行) ===
A="$account_id"; P="$group_id"
all_msgs="[]"
cursor=""
remaining=30

while [ "$remaining" -gt 0 ]; do
  size=$([ "$remaining" -gt 10 ] && echo 10 || echo "$remaining")
  if [ -z "$cursor" ]; then
    page=$(coze agent message list --org-id "$A" --project-id "$P" --size "$size" --json)
  else
    page=$(coze agent message list --org-id "$A" --project-id "$P" --size "$size" --cursor "$cursor" --json)
  fi
  # 信封校验 (见顶部"CLI 调用约束")
  [ "$(echo "$page" | jq -r '.code')" = "0" ] || break

  # ↓↓↓ 这两行的 <MSG_FIELD> / <CURSOR_FIELD> 必须替换, 否则 jq 报 syntax error ↓↓↓
  all_msgs=$(echo "$all_msgs $page" | jq -s '.[0] + .[1].data.<MSG_FIELD>')
  cursor=$(echo "$page" | jq -r '.data.<CURSOR_FIELD> // ""')
  [ -z "$cursor" ] || [ "$cursor" = "null" ] && break

  remaining=$((remaining - size))
done

echo "$all_msgs" | jq '.'
```

> 占位符 `<MSG_FIELD>` / `<CURSOR_FIELD>` 是**故意**写成非法语法的——jq 会立刻报错, 强迫你先跑第一步探字段名再来填。不要照抄 `data.messages` / `data.next_cursor`, 那只是常见命名, 不一定是这个 CLI 的实际字段。

> ⚠️ **不要假装 10 条上限不存在**。用户要"最近 30 条"就老老实实翻 3 页。直接传 `--size 30` 会被 CLI 拒绝。

**追溯讨论结论的常见姿势** (用户问"上次怎么决定的"):

1. `--asc-mode` 从最旧拉, 保留时间顺序
2. `--need-reference` 让"A 引用 B 然后说 ..."的上下文不断链
3. 翻页累积到一个合理深度 (e.g. 30-50 条)
4. 把关键节点 (决策、结论、行动项) 摘要给用户, 别原样倒出所有消息

## 不要做的事 (查询层面)

- ❌ 不要省 `--json` 或忽略信封 `.code` 校验 (见顶部"CLI 调用约束")
- ❌ 不要传 `--size > 10` — CLI 直接拒绝, 老实翻页
- ❌ 不要不带 `--need-reference` 就追溯有引用链的讨论 — 引用断了上下文丢, 误导用户
- ❌ 不要首次调用就假定游标字段名 — 先看一次 `.data` 实际形状, 字段名以 CLI 实际返回为准
- ❌ 不要把所有消息原样倒给用户 — 摘要 + 关键节点引用更有用
- ❌ 不要无差别拉全部消息再筛 — 项目消息量大时浪费 API, 先想清楚需要什么时间范围 / 关键词
