# AACT 连接配置 · 详细部署

> 主 SKILL.md 第 3 节的展开。skill 启动时自动检测优先级：**本地 dump (B) → 云端 (A) → 报错指引**。

## 方式 A · 云端公共 PostgreSQL（零部署）

| 字段 | 值 |
|------|----|
| Host | `aact-db.ctti-clinicaltrials.org` |
| Port | `5432` |
| Database | `aact` |
| User/Pass | 注册免费账号: https://aact.ctti-clinicaltrials.org/users/sign_up |
| SSL | `sslmode=require`（部分网络环境强制） |

**适合**：偶发查询、无本地 PostgreSQL、可接受网络延迟（典型 200ms-2s/查询）。
**不适合**：百万级 JOIN、整库扫描、密集批量挖掘（建议改本地）。

## 方式 B · 本地 dump 还原（高性能 · 离线）

下载每日 dump（约 2.27 GB pg_dump custom format）：
https://aact.ctti-clinicaltrials.org/downloads

**前置要求**：本地 PostgreSQL 16+。

### 还原命令（跨平台）

**macOS / Linux**:
```bash
createdb aact
pg_restore -d aact -j 4 --no-owner --no-privileges /path/to/postgres_data.dmp
```

**Windows (PowerShell)**:
```powershell
& "C:\Program Files\PostgreSQL\16\bin\createdb.exe" aact
& "C:\Program Files\PostgreSQL\16\bin\pg_restore.exe" -d aact -j 4 --no-owner --no-privileges "D:\dumps\postgres_data.dmp"
```

**适合**：批量挖掘、跨年度聚合、设计相似性匹配、整库扫描；典型查询 < 5s。

## 配置文件 `~/.config/aact.local.yaml`

```yaml
# 优先模式：local 或 cloud；auto 表示自动检测（默认）
mode: auto

local:
  host: localhost
  port: 5432
  database: aact
  user: postgres
  password: ${AACT_LOCAL_PASSWORD}  # 从环境变量读取

cloud:
  host: aact-db.ctti-clinicaltrials.org
  port: 5432
  database: aact
  user: ${AACT_CLOUD_USER}
  password: ${AACT_CLOUD_PASSWORD}
  sslmode: require

defaults:
  query_limit: 1000          # 防爆默认 LIMIT
  cursor_threshold: 50000    # 超过该行数自动切 server-side cursor
  statement_timeout: 120000  # 毫秒
  read_only: true            # 强制只读会话（防 DROP/DELETE 误操作）
```

## 密钥管理铁律

- **永不**把 password 明文写进 yaml；用 `${VAR}` 占位符 + 环境变量
- yaml 文件加入 `.gitignore`
- 启动时校验所有 `${VAR}` 占位符已被解析；缺失则立即报错并指引设置环境变量
- 云端凭据轮换：通过 https://aact.ctti-clinicaltrials.org/users/edit 重置

## Read-Only 强制（防误操作）

每次连接后立即执行：
```sql
SET default_transaction_read_only = ON;
SET statement_timeout = 120000;
```

这样即便恶意 prompt 注入 `DROP TABLE`，也会被 PostgreSQL 拒绝。

## 服务管理速查

| 平台 | 启动 PostgreSQL |
|------|-----------------|
| macOS (Homebrew) | `brew services start postgresql@16` |
| Linux (systemd) | `sudo systemctl start postgresql` |
| Windows | `Start-Service postgresql-x64-16` |
| Docker | `docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=xxx postgres:16` |

## Schema 年度变更处理

AACT 每年 schema 微调 1-2 次（列改名、新增 results 子表）。订阅：
- https://aact.ctti-clinicaltrials.org/release_notes

skill 应在 meta 中输出 `aact_snapshot_date`，并在出现 `relation "xxx" does not exist` 时自动指向 release_notes 校准。
