# 部署与恢复

## 核对官方来源和版本

使用 [Xray 官方安装仓库](https://github.com/XTLS/Xray-install) 和 [官方发布](https://github.com/XTLS/Xray-core/releases)。先下载并检查脚本及版本参数，再执行。记录来源、版本和可取得的校验信息，不执行未经检查的视频短链接脚本。

同时查 [Xray 传输配置](https://xtls.github.io/en/config/transport.html)、[XHTTP 说明](https://github.com/XTLS/Xray-core/discussions/4113) 和 [mihomo VLESS](https://wiki.metacubex.one/en/config/proxies/vless/)。文档可能晚于已安装版本，以选定版本的配置检查和真实握手为准。不要只升级服务端而不测客户端。

## 保留管理入口

保存核心配置、systemd 单元和覆盖文件、防火墙规则、SSH 配置及版本。记录权限、SHA256 和恢复命令，检查备份可读。

固定 SSH 主机密钥。能从供应商控制台核对指纹时先核对；仅首次信任时如实记录。主机密钥变化不得自动放行。

创建专用 SSH 密钥并验证新会话成功后才关闭密码登录。检查 sshd 配置语法和实际生效设置，保留供应商恢复入口。修改 SSH 或防火墙前安排服务器端限时自动回滚，独立会话验证通过后再取消。当前 SSH 未断开不是成功证据。

沿用现有防火墙管理器，保留业务端口、回环、已建立连接和必要 ICMP/ICMPv6。新机通常只需 SSH 与代理 TCP 443。不要清空已有规则或自动停止占用 443 的业务。443 被占用时选择经用户授权且确认可用的 listenPort，将该端口同步到防火墙、服务端、YAML、URI 和测试。另查供应商安全组；不能沿用其他端口的测试结果。

## 配置基线

以下是参数约束，不是完整可执行配置。根据选定版本生成 JSON 并运行核心配置检查。

| 项目 | 基线 |
| --- | --- |
| 入站 | VLESS，TCP listenPort，默认 443，两个独立 UUID，decryption 为 none |
| 传输 | XHTTP，服务端 mode 为 auto |
| 路径 | 新部署随机生成，以 / 开头，两端一致 |
| 填充 | xPaddingBytes 为 100-1000，核对版本支持 |
| 安全层 | REALITY，show 为 false，xver 为 0 |
| 目标 | 实测域名加 443，serverNames 包含客户端 SNI |
| 密钥 | 新生成 X25519 密钥对，私钥仅服务端 |
| short ID | 两个不同随机 8 字节值，编码为 16 位十六进制 |
| 客户端 | Chrome 指纹、ALPN h2、XHTTP stream-one、TLS 和 REALITY |
| flow | XHTTP 基线不设置 xtls-rprx-vision |

使用所选版本的 xray uuid、xray x25519 或等效安全随机库。核对密钥工具实际输出中的公钥字段。不能复用教程 UUID、路径或密钥。维护时仅修改目标入站。

## 服务权限与回滚

使用专用低权限账户。配置通常由 root 管理、服务组可读，权限 0640。备份仅管理员可读。低端口通常仅需 CAP_NET_BIND_SERVICE。systemd 列表可能叠加，需要先清空继承项：

```ini
[Service]
User=xray
Group=xray
NoNewPrivileges=true
ProtectHome=true
PrivateTmp=true
CapabilityBoundingSet=
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=
AmbientCapabilities=CAP_NET_BIND_SERVICE
```

确认账户和目录权限后应用。用 systemctl show 检查最终能力集合，再实际重启。已有功能需要额外能力时按实际需求调整。

按业务决定是否禁止代理访问私网和 SMTP 25，不阻断用户明确需要的服务。不要附加与协议无关的全机调优。

先运行 `xray run -test -config <配置路径>`，再原子替换并重启。失败时恢复文件与权限，验证服务和代理恢复。新部署检查开机启动；整机重启仅在已获授权且不影响其他业务时执行。

## 安排服务器端回滚

先确定实际 SSH 服务名、防火墙管理器和文件位置。把备份及 restore.sh 放在 root 独占目录。恢复脚本使用绝对路径，按以下顺序恢复：

1. 恢复防火墙的已知可用规则，保留 SSH 管理端口。
2. 恢复 SSH 配置和权限，通过 sshd -t 后重新加载实际 SSH 服务。
3. 恢复 Xray 配置和权限，通过配置检查后重启服务。
4. 将执行状态及恢复哈希写入仅 root 可读的日志。任一步失败都记录，并继续尝试恢复其他独立组件。

仅筛选目标时，恢复脚本只恢复 Xray，不触碰 SSH 或防火墙。先对脚本做语法检查并核对其使用的是修改前备份。为本次任务选择唯一 unit 名称，执行：

```sh
systemd-run --unit=<唯一任务名>-rollback --on-active=10m /bin/sh /root/<私密备份目录>/restore.sh
systemctl status <唯一任务名>-rollback.timer
systemctl list-timers <唯一任务名>-rollback.timer
```

这些命令中的占位符必须替换为已确认的路径和名称。检查 timer 存在且触发时间正确，再开始变更。预计操作超时则先重新安排足够时间，不让正常测试与恢复并发。

取消前检查恢复任务没有运行中；若已触发，先读取日志并确认最终状态。独立会话和代理验证通过后停止对应 timer，并确认 timer 不活跃。保留 restore.sh 和备份作为手动恢复入口。没有 systemd 时使用目标系统可验证的等效调度器；不能安排恢复时不执行可能断开唯一管理入口的变更。
