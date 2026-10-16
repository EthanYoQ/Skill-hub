# 生成客户端与私密交付

## 单一参数记录

记录 host、port、target、path、privateKey、publicKey、节点列表中的 name/uuid/shortId，以及 SSH 信息和版本。记录只放权限受限的交付目录。Windows 限制 ACL 到当前用户及必要系统账户；Linux 目录 0700、私密文件 0600。普通 MD 不是加密文件。

使用本地 JSON/YAML 库、URL 编码器和二维码库生成。缺少库时只在获准的执行环境安装到临时目录；用户禁止操作电脑时不要在其电脑安装。生成逻辑读取私密文件，不把秘密放入命令行、日志、剪贴板或聊天。服务端私钥不得进入客户端配置。

## Clash Verge

核对 [mihomo VLESS](https://wiki.metacubex.one/en/config/proxies/vless/)、[传输配置](https://wiki.metacubex.one/en/config/proxies/transport/) 和 [TUN](https://wiki.metacubex.one/en/config/inbound/tun/) 的目标版本语法。生成两个条目：

- type 为 vless，server/port/uuid 来自记录。
- network 为 xhttp，tls 为 true，servername 为所选目标，client-fingerprint 为 chrome。
- reality-opts 使用 public-key 和 short-id。
- xhttp-opts 使用匹配的 path 和 mode stream-one；ALPN 为 h2，不设置 flow。

代理组包含两个节点，不加静默 DIRECT 兜底。保留用户路由策略；新配置默认公网经该组，明确需要的本地网段才直连。不要覆盖现有客户端配置。

新建 IPv4 出口、阻断 IPv6 的配置可采用以下策略，先验证内核支持：

- 全局 ipv6 为 true，让 TUN 接管 IPv6；DNS ipv6 为 false。
- TUN 启用 auto-route、auto-detect-interface、strict-route，并配置双栈接管。
- dns-hijack 同时覆盖 `any:53` 和 `tcp://any:53`。
- TUN IPv6 地址使用不冲突的 ULA，route-address 覆盖 IPv4 和 IPv6 默认路由。
- 首条规则 `IP-CIDR6,::/0,REJECT,no-resolve` 阻断 IPv6 出口。不要全局关闭 IPv6 却声称接管了系统 IPv6。
- DNS 使用 fake-ip，respect-rules 为 true，公共解析使用经代理组的加密 DNS。
- DNS 仅监听回环。代理入口和 DoH 引导解析避免循环依赖，固定 IP 节点可减少引导依赖。

按官方语法指定 DoH 使用代理组，检查日志中的实际选择。fake-ip 本身不证明无 DNS 泄漏。设置 allow-lan false，使用未占用的本地端口。双栈代理需求需另行设计，不机械加入 IPv6 拒绝规则。

## Shadowrocket

为每个节点生成 VLESS URI。authority 包含 UUID、host 和端口，IPv6 地址加方括号。查询参数如下：

| 参数 | 值 |
| --- | --- |
| encryption | none |
| security | reality |
| sni | 所选目标 |
| fp | chrome |
| pbk | REALITY 公钥 |
| sid | 该节点 short ID |
| type | xhttp |
| path | 两端相同，进行 URL 编码 |
| mode | stream-one |
| alpn | h2 |

节点名放在编码后的 fragment。用本地二维码库输出 PNG，再用独立解码器读取，核对 URI 完全一致。不得用图片生成模型绘制二维码。

核对目标 Shadowrocket 版本支持 XHTTP/REALITY 和 URI 字段，优先读官方应用内说明。没有设备实测时标记待用户导入验证。二维码仅承载节点参数，不包含 Clash 的全局 DNS、路由和 IPv6 策略。另给出与实际应用版本匹配的设置说明，未核实的菜单和语法不要编造。

## 交付文件

交付 YAML、两个 PNG、两个 URI 的文本文件和私密 MD。MD 写明连接方法、SSH 密钥位置及恢复所需材料、节点参数、备份、恢复命令、版本、筛选结果、导入说明、实际测试和未测范围。用户要求集中留存密钥时可写入私密 MD，并说明含凭据。

保留更新前的交付文件和服务器配置，分目录避免误导入。生成 SHA256 清单。重新导出时核对 UUID、short ID、密钥和路径未意外轮换。公开报告仅留脱敏信息，不上传私密 MD、二维码或服务端配置。
