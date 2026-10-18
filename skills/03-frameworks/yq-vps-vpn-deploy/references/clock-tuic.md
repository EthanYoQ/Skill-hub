# 时钟、TUIC 与证书续期

新增 TUIC UDP 备用、排查间歇认证失败或维护短期证书时读取。以下版本来自已验证的部署基线：sing-box 1.14.3、mihomo 1.19.32、Certbot 5.8.0。它们不是永久推荐版本；更换版本后重验对应行为。

## 先检查实际系统时钟

已遇到 NTP 源可用，但 `chronyc tracking` 的 `System time` 仍偏差数分钟的情况。NTP 服务 active、源已选中和系统时钟已校正是不同事实。时钟异常期间的日志时间不能直接用于判断故障先后。

保存 chrony 配置及当前状态，比较 `date -u`、`chronyc tracking`、`chronyc sources -v` 和多个独立时间源。记录偏差、来源和可信的观测时间。不要仅凭本机日志时间断言故障持续时长，也不要未经验证归因为虚拟机时钟故障。

确认源一致、校时属于当前授权范围后，可用 `chronyc makestep` 立即纠偏，再用有界的 `chronyc waitsync` 检查收敛。例如 `chronyc waitsync 60 0.01` 最多检查 60 次，要求剩余校正量小于 0.01 秒。之后复查 tracking、实际 UTC 和 `timedatectl show -p NTPSynchronized`；该属性可能稍后才变为 yes，不能只读一次。

`makestep 1.0 3` 只允许 chronyd 启动后的前三次更新进行超过 1 秒的步进，不负责运行数小时后的再次大偏差。参见 [chrony 配置](https://chrony-project.org/doc/4.6/chrony.conf.html) 和 [chronyc 命令](https://chrony-project.org/doc/4.6/chronyc.html)。若偏差重复出现，先查来源、服务重启和宿主时间同步。持续允许步进的策略，例如负数 limit，只在已评估影响的代理专用主机上考虑；它会改变系统墙上时间，不能推广到所有服务器。备份并写明恢复原校时配置的方法。

## 独立部署 TUIC v5

保留已工作的 Xray VLESS TCP 服务。新增 sing-box 独立服务、账户与配置，使用低权限用户和低端口所需的 `CAP_NET_BIND_SERVICE`。TCP 443 与 UDP 443 可以同时监听；单独验证 UDP 防火墙和安全组。

按 [sing-box TUIC](https://sing-box.sagernet.org/configuration/inbound/tuic/) 配置 v5 的 UUID 和随机密码、TLS 及 ALPN `h3`。运行配置检查后再启动；实际 UDP/QUIC 握手才证明入口可达。保持 `zero_rtt_handshake: false`，客户端关闭 0-RTT，不为减少一次握手启用重放风险。TLS 文件权限与重载字段查 [sing-box TLS](https://sing-box.sagernet.org/configuration/shared/tls/)。

## 没有域名时使用可信 IP 证书

Let’s Encrypt 已提供 IP 地址证书，要求 `shortlived`，有效期 160 小时。无需购买域名，但必须控制申请的公网 IP，并可靠自动续期。参见 [IP 证书开放说明](https://letsencrypt.org/2026/01/15/6day-and-ip-general-availability) 和 [Certbot IP 申请流程](https://letsencrypt.org/2026/03/11/shorter-certs-certbot)。

使用已验证版本或核实当前 Certbot 支持 `--ip-address` 和 `--preferred-profile shortlived`。先用 staging 验证 HTTP-01，再申请生产证书；staging 链不受公网客户端信任。HTTP-01 使用公网 TCP 80，续期也需要该路径可达。已有 Web 服务优先采用适用的 webroot；不为 standalone 自动停业务。

生产验收检查证书链、IP SAN、有效期和实际 QUIC 端点，客户端保持证书验证。不能用跳过验证掩盖签发、时钟或名称错误。

配置自动续期及 deploy hook，让服务读取最新证书；按 [Certbot 续期说明](https://eff-certbot.readthedocs.io/en/stable/using.html#renewing-certificates) 检查实际调度、权限、失败记录和到期告警。区分续期 dry-run、钩子执行和真实端点换证：文件变化或命令返回成功都不等于 QUIC 已使用新证书。比较换证前后的证书序列号，并通过新的真实 QUIC 连接读回；若只能验证磁盘证书，端点换证仍标未测。

在已验证的文件监听部署中，同一密钥续期可避免证书和密钥分别替换时短暂不匹配；若采用 Certbot `--reuse-key`，写明密钥轮换另行执行，不能把它当作永久不轮换的要求。deploy hook 应检查链、SAN、有效期和公私钥匹配，按服务权限部署后验证新握手。

验收无中断换证时，同时保持现有流并建立新连接，核对新证书和旧流。需要重启才能加载时，如实记录重连。未实测前不宣称热重载、续期无中断或长期可用；测试只做必要次数，不反复强制生产签发。

## mihomo 的证书验证陷阱

[mihomo 1.19.32 源码](https://github.com/MetaCubeX/mihomo/blob/v1.19.32/adapter/outbound/tuic.go) 中，`disable-sni: true` 会设置 `InsecureSkipVerify = true`，即使另写 `skip-cert-verify: false` 也不能据此声称验证证书。

IP 证书使用 `sni: <证书中的IP>`、`disable-sni: false`、`skip-cert-verify: false`。该名称用于 IP SAN 校验，不要求在线路上发送 IP SNI 扩展。另设 `alpn: [h3]`、`reduce-rtt: false`。参见 [mihomo TUIC 字段](https://wiki.metacubex.one/en/config/proxies/tuic/)，用错误名称负向测试证明没有绕过验证。

## 稳定性结论的边界

按 [验收](verification.md) 分别验证三进程、同凭据并发、双协议混用、至少 900 秒真实长流、UDP/DNS、认证拒绝和换证。几次 GET 只证明短请求可用，不能代表持续流。设备实测、隔夜运行、中国运营商路径分别记录，不能保证全国防封或隔夜稳定。
