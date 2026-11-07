# Chrome 登录交接操作手册

## 读取与字段映射

在正确的源配置打开已确认的后台标签页。工具已提供受权 CDP 时，针对该标签页发送以下命令。用经确认的 HTTPS 后台 URL 替换示例。补充路径或子域前先确认其属于授权范围。

```json
{"method":"Network.getCookies","params":{"urls":["https://creator.example.com/dashboard"]}}
```

CDP 按 URL 返回可用 Cookie。按授权根域核对 `domain`，只接受根域或以点分隔的子域。排除带 `partitionKey`、`partitionKeyOpaque` 或已过期的记录。对 Chrome CDP 的常规域表示，带前导点表示 domain cookie，其余按 host-only 处理。保留 `name`、`value`、`domain`、`path`、`secure`、`httpOnly`，并按下表转换。浏览器 Cookie API 原生提供 `hostOnly`，使用该 API 时保留其返回值。

| CDP 字段 | 交接格式 |
| --- | --- |
| `sameSite: "None"` | `sameSite: "no_restriction"` |
| `sameSite: "Lax"` / `"Strict"` | `sameSite: "lax"` / `"strict"` |
| 缺少 `sameSite` | `sameSite: "unspecified"` |
| `session: true` | 省略 `expirationDate` |
| 持久 Cookie 的正数 `expires` | `expirationDate`，Unix 时间戳，单位为秒 |

在内存中处理工具返回和转换结果。工具若只能把返回值写进聊天或日志，切换到用户批准的本地扩展。 [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/tot/Network/#method-getCookies) · [Chrome Cookies API](https://developer.chrome.com/docs/extensions/reference/api/cookies)

## 生成和整理文件

[随附扩展](../assets/chrome-extension/manifest.json)预设 `douyin`、`xiaohongshu`、`zhihu`、`tiktok`。扩展使用 Chrome 的 Cookie API，按平台请求可选 HTTPS 域权限，在本机完成加解密。需要支持其他站点时，先审查并同步调整域名清单、站点选择项和 manifest 权限。 [Chrome Permissions API](https://developer.chrome.com/docs/extensions/reference/api/permissions)

- CDP 路径可从本地 [transfer.mjs](../assets/chrome-extension/transfer.mjs) 调用 `encrypt(site, passphrase, cookies)` 和 `decrypt(site, passphrase, bundle)`。可使用具备 Web Crypto 的运行时。扩展路径从工具栏打开扩展页面，选择平台，输入随机口令并点「导出加密包」。
- 优先用系统随机源生成 32 字节，再编码为口令。用独立密码管理器或系统凭据存储保管。例如 Windows 可用当前用户 DPAPI 留存本机副本，Mac 端使用密码管理器或 Keychain 接收。两端传递口令走独立的受控途径。
- 格式 `browser-session-handoff-v1` 使用 AES-256-GCM、PBKDF2-SHA256（600,000 次）、16 字节随机 salt、12 字节随机 IV，以及 UTF-8 的 `格式:站点` 作为认证数据。使用与加密文件格式匹配的导入器。
- 在同一个受控运行时从磁盘回读密文。解密后核对记录数和完整内容。日志只记录平台与检查结果。若仅完成扩展中的内存往返校验，状态仍为「磁盘回读待核验」。
- 将密文、导入器的四个源文件和一份简短接入说明放进一个 ZIP。检查归档实际文件列表后，用 Windows `Get-FileHash -Algorithm SHA256` 或 macOS `shasum -a 256` 算出归档哈希。通过受控途径发送 ZIP 和预期哈希。说明可以使用下面的清单。

```text
README.md                    # 已授权站点、文件映射、目标配置和验证步骤
encrypted/<site>.encrypted.json
importer/manifest.json
importer/open-transfer.js
importer/transfer.html
importer/transfer.mjs
```

## 目标设备

1. 核对 ZIP 哈希，解压到目标设备受控目录。打开 Agent 将实际使用的专用 Chrome 配置。
2. 在 Chrome 扩展管理页面通过「加载已解压的扩展程序」选择 `importer/`。打开工具栏扩展，选平台与对应文件，输入单独收到的口令。由用户确认 Chrome 的该站点权限。
3. 首次导入前保持该平台的 Cookie 存储为空。导入器检测到该平台已有 Cookie 会停止。若显示部分写入，在同一专用配置中只读检查后台。确需重试时使用一个新的空白专用配置，并让 Agent 指向该配置。
4. 在同一配置打开平台后台，核对预期账号和评论页。成功后移除临时扩展与交接副本，按约定保管源文件和口令。若遇到登录挑战、设备绑定或过期会话，由用户走平台正常登录流程。OAuth 接入继续走官方授权。

## 验收样例

- 已授权两个站点，要求只传一个 ZIP。归档包含两个密文和匹配的导入器，口令单独保管。清单列出逐站点回读和目标端验证状态。
- 站点选错、口令错误或密文被修改。解密失败，导入器在写入前停止。
- 用户拒绝 Chrome 权限或平台要求重新验证。记录该站点的实际状态，等待用户操作。
