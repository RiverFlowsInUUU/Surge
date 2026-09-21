# Surge 防 DNS 泄露 · 完整技术文档

> 面向想彻底弄明白「为什么这么写」的读者。
> 只想赶紧用起来 → 看 [`README`](../README.md) 的 [🚀 快速开始](../README.md#-快速开始)。
>
> 目录
> [1 · 文件结构与两份形态](#1--文件结构与两份形态) ·
> [2 · 防泄露原理：从机制到推导](#2--防泄露原理从机制到推导) ·
> [3 · `[General]` 逐键](#3--general-逐键) ·
> [4 · `[Proxy]` 与占位符](#4--proxy-与占位符) ·
> [5 · 占位符与脱敏规则](#5--占位符与脱敏规则) ·
> [6 · `smart` / `select` 组的差别](#6--smart--select-组的差别) ·
> [7 · `underlying-proxy` 中转链](#7--underlying-proxy-中转链) ·
> [8 · `pre-matching` 与 `extended-matching`](#8--pre-matching-与-extended-matching) ·
> [9 · `always-real-ip` 与 Fake-IP](#9--always-real-ip-与-fake-ip) ·
> [10 · `hijack-dns` 的边界](#10--hijack-dns-的边界) ·
> [11 · 规则集与刷新](#11--规则集与刷新) ·
> [12 · `no-resolve` 的双刃](#12--no-resolve-的双刃) ·
> [13 · `[Proxy Group]`：三个组与两个「不能用组」的地方](#13--proxy-group三个组与两个不能用组的地方) ·
> [14 · `[Rule]`：12 条逐条](#14--rule12-条逐条) ·
> [15 · 审计体系](#15--审计体系) ·
> [16 · 已知取舍](#16--已知取舍) ·
> [17 · FAQ](#17--faq) ·
> [18 · 维护者须知](#18--维护者须知)

---

## 1 · 文件结构与两份形态

```
surge-anti-dns-leak/
├── profiles/
│   ├── v1.conf          # 完整版（带注释）—— 推荐
│   ├── v1.min.conf      # 完整版（纯配置，注释剥掉）
│   ├── v0.conf          # 极简版（带注释）
│   └── v0.min.conf      # 极简版（纯配置）
├── icons/               # 26 个策略组图标（本地，不跨项目引用）
├── docs/                # 01–10 专题
├── DetailsReadme/       # 本文件
├── CHANGELOG.md
├── LICENSE
└── skill/
    ├── SKILL.md                  # 方法论
    ├── README.md                 # 脚本用法
    ├── reference/                # 逐条判据
    ├── scripts/                  # 3 个审计脚本 + 1 个共享模块
    └── tests/                    # 5 阶段回归 + 3 个 fixture + 链接检查
```

### 1.1 为什么每份配置有两份形态

| 形态 | 给谁 | 特点 |
|:-----|:-----|:-----|
| `.conf` | 想读懂的人 | 每个键上方有理由；结构分段带标题 |
| `.min.conf` | 只想导进去的人 / 机器处理 | 同内容，无注释，行数少一半 |

两者**内容必须一致，只差注释**。这条由 `skill/tests/architecture.sh` 的一致性断言兜底
（比对 16 个 DNS 相关键的逐字相等）。

> ⚠️ `.min.conf` 里仍保留 `# audit-waive:` 那行 —— 它是**有语义的注释**，不是说明文字。
> 删掉它，审计读数就从「2 waived」变成「2 high」。

---

## 2 · 防泄露原理：从机制到推导

### 2.1 先定义「泄露」

本文所说的 DNS 泄露，**不是**「DNS 请求被加密了没有」，也不是「权威服务器知道你是谁」。
定义收紧到一条：

> **设备发出的、能被链路上的第三方（运营商 / Wi-Fi 提供者 / 旁路设备）直接读到的
> 明文 DNS 查询，存在任何一条「必然会被走到」的通路。**

「必然会被走到」是关键。一个只在极端条件下才会发生的明文查询，和每 5 分钟发生一次的
明文查询，风险量级完全不同 —— 但配置语法上它们看起来一样。

### 2.2 明文查询从哪来：三条出口

#### 出口 ①：引导解析（bootstrap）

DoH / DoT 端点写成一个**主机名**时，会出现一个循环：

```
要用 DoH 查 dns.google 的 IP
  → 但得先知道 dns.google 的 IP 才能建 DoH 连接
    → 于是先用明文 DNS 查一次 dns.google 的 IP
      → 这一步就是泄露
```

这不是实现缺陷，是协议固有的先有鸡先有蛋。**唯一彻底的解法是端点写 IP 字面量**，
让循环不存在。

`dns-server` 同理：它承担引导解析职责，如果写成 `system`，等于把这一步交给
运营商 DHCP 下发的那台解析器 —— 那正是要消除的对象。

**配置里的对策**

```
dns-server = 223.5.5.5, 119.29.29.29, 1.1.1.1, 8.8.8.8     # 裸 IP，不是 system
encrypted-dns-server = https://1.1.1.1/dns-query, …        # 至少一个 IP 字面量
```

`encrypted-dns-server` 里保留了 `https://dns.google/dns-query` 与
`https://dns.alidns.com/dns-query` 两个主机名端点 —— 这是**刻意的取舍**（见 §16），
已在 profile 内用 `# audit-waive: 1` 声明。

#### 出口 ②：旁路设备

HomePod、Apple TV、Chromecast、智能音箱、部分 IoT 设备**不使用** Surge 的 DNS
（它们有自己的硬编码解析器，通常是 `8.8.8.8`），发出的就是明文 `UDP:53`。

这些查询会穿过 Surge 的 TUN 接口。**默认情况下 Surge 不管它们** —— 它们直接到
硬编码的那台境外解析器。这既是泄露，也常常是「设备能用但很慢」的原因
（境外解析器在国内链路上时通时不通）。

**配置里的对策**

```
hijack-dns = 8.8.8.8:53, 8.8.4.4:53, 1.1.1.1:53, 1.0.0.1:53, 9.9.9.9:53, 208.67.222.222:53
```

把这些地址的 `:53` 查询接管回来，走 Surge 的加密 DNS。
想一网打尽可以写 `hijack-dns = *`（Surge 官方示例值），代价是所有 `:53`
查询都进 Surge 处理，极少数依赖原生 `:53` 行为的应用可能受影响。

#### 出口 ③：规则触发解析

这是最隐蔽的一条。**不带 `no-resolve` 的 IP 类规则会主动发起 DNS 解析**：

```
GEOIP,CN,DIRECT          ← 没有 no-resolve
```

Surge 求值到这条规则时，如果请求只是一个域名（还没有 IP），它会**先做一次 DNS 查询**
拿到 IP，再拿这个 IP 去查 GeoIP 库。

关键在于：**这次解析走的是 Surge 的 DNS 客户端**，所以它本身是加密的、不泄露。
但它的存在会带来两个后果：

1. 每个走到这条规则的域名都要等一次解析 —— 表现为「首个请求卡一下」；
2. 在启动早期（加密 DNS 还没就绪）或加密 DNS 不可达时，这次解析会**回退明文**。

**配置里的对策**

```
GEOIP,CN,DIRECT,no-resolve
RULE-SET,LAN,DIRECT,no-resolve
RULE-SET,…,private.txt,DIRECT,no-resolve
RULE-SET,…,direct.txt,DIRECT,no-resolve
RULE-SET,…,AI.list,…,no-resolve
```

⚠️ 但 `no-resolve` 有代价，见 §12 —— 这是本模板最需要注意的一处。

### 2.3 三处收口之后

| 出口 | 收口手段 |
|:----:|:---------|
| ① 引导 | 端点写 IP 字面量；`dns-server` 写裸 IP |
| ② 旁路 | `hijack-dns` 接管 |
| ③ 规则 | 所有 IP 类规则带 `no-resolve` |

三者叠加，明文 `UDP:53` 没有任何一条通路是「必然会被走到」的。
注意措辞：是「没有必然通路」，不是「绝对零明文」——
一个从没访问过的域名、一次极端网络切换，仍可能产生零星明文。**任何声称
"绝对零泄露"的配置都在夸大**。

---

## 3 · `[General]` 逐键

### 3.1 DNS 段（防泄露本体）

| 键 | 值 | 为什么 |
|:---|:---|:-------|
| `dns-server` | `223.5.5.5, 119.29.29.29, 1.1.1.1, 8.8.8.8` | 引导与连通性测试。**绝不用 `system`**。前两个是国内（快、稳），后两个境外（用于验证加密 DNS 前的连通性） |
| `encrypted-dns-server` | `1.1.1.1` + `dns.google` + `dns.alidns.com` | 三个不同机构，任一故障有退路。1 个 IP 字面量保证冷启动可用 |
| `encrypted-dns-follow-outbound-mode` | `false` | 见下 |
| `hijack-dns` | 6 个境外解析器的 `:53` | 出口 ② |
| `allow-dns-svcb` | `false` | 不向应用下发 HTTPS/SVCB 记录。开启会让应用绕过 Surge 的部分解析路径 |
| `exclude-simple-hostnames` | `true` | 单标签主机名（`nas`、`router`）直接交给系统解析，不产生查询 |
| `read-etc-hosts` | `true` | 尊重本机 hosts |
| `use-local-host-item-for-proxy` | `false` | 见下 |

**`encrypted-dns-follow-outbound-mode` 为什么必须 `false`**

设成 `true` 时，DoH 连接自己也要遵循代理规则。若代理规则里这个解析器域名指向代理，
就形成「要解析它 → 需要它 → 要解析它」的环。Surge 会检测并回退明文，等于泄露。

**`use-local-host-item-for-proxy` 为什么必须 `false`**

`[Host]` 段与 `read-etc-hosts` 提供的本地映射只服务 DIRECT 路径。
一旦开启，本地 DNS 结果会变成**硬性的代理目标** —— 走代理的域名应该由节点侧
根据地理位置解析（CDN 就近），本地给它一个答案反而会把它钉在错误的 IP 上。

### 3.2 IPv6

| 键 | 值 | 为什么 |
|:---|:---|:-------|
| `ipv6 = true` | 真实 IPv6 可直连 | 关掉会让纯 IPv6 站点不可达 |
| `ipv6-vif = auto` | 仅在本地网络确实有可用 IPv6 前缀时才让 VIF 承载 | 若写死 `true`，在纯 IPv4 的 Wi-Fi 上会留一条死掉的 AAAA 路径 —— 表现为连接超时 + 额外耗电 |

### 3.3 GeoIP

| 键 | 值 |
|:---|:---|
| `geoip-maxmind-url` | `adysec/IP_database` 的手工构造 `GeoLite2-Country.mmdb` |
| `disable-geoip-db-auto-update` | `false`（保持自动更新） |

手动构造的 mmdb 不一定带 MaxMind 官方签名，Surge 可能报警。当前配置保持更新开启；
若日志出现更新报错，把它改成 `true` 即可（代价是库会变旧）。

### 3.4 测试端点

| 键 | 值 | 为什么 |
|:---|:---|:-------|
| `test-timeout` | `5` | 5 秒足够区分「慢」和「坏」 |
| `internet-test-url` | `connect.rom.miui.com/generate_204` | 国内 204，低方差 |
| `proxy-test-url` | `connect.rom.miui.com/generate_204` | **本模板相对源配置唯一一处实质改动** —— 见 §16.1 |
| `proxy-test-udp` | `apple.com@1.1.1.1` | `smart` 组的 UDP 评分要用；`1.1.1.1` 是 IP 字面量，不产生解析 |

### 3.5 流量处理

| 键 | 值 | 为什么 |
|:---|:---|:-------|
| `udp-policy-not-supported-behaviour` | `reject` | `https` 类型节点不支持 UDP 中继（见 §4.3）。落到这类节点上的 UDP 直接拒绝，语义清晰 |
| `udp-priority` | `true` | 系统繁忙时优先处理 UDP（游戏、视频通话受益） |
| `block-quic` | `per-policy` | 默认阻止 QUIC，只在策略明确支持时放行。QUIC 走 UDP，绕过 TCP 类规则会导致分流失效 |

### 3.6 局域网与安全

| 键 | 值 | 为什么 |
|:---|:---|:-------|
| `allow-wifi-access` / `allow-hotspot-access` | `true` | 允许同网段设备用本机做代理 |
| `proxy-restricted-to-lan` / `gateway-restricted-to-lan` | `true` | **安全项**：即使上级网络 DMZ / 端口转发配得潦草，监听端口也不会暴露到当前子网之外 |

### 3.7 Wi-Fi / 蜂窝

| 键 | 值 | 为什么 |
|:---|:---|:-------|
| `all-hybrid` | `false` | `true` 会让**每条 TCP 连接和每次 DNS 查询**同时走 Wi-Fi + 蜂窝 —— 明确的耗电与流量代价 |
| `wifi-assist` | `false` | Wi-Fi 弱时自动切蜂窝，会打断代理连接 |

### 3.8 `always-real-ip`

```
always-real-ip = *.lan, *.local, *.localdomain, *.home.arpa,
                 *.srv.nintendo.net, *.stun.playstation.net, *.xboxlive.com,
                 stun.*, time.*.com, ntp.*.com, *.pool.ntp.org, *.market.xiaomi.com
```

两类：

- **本地类**（`*.lan` / `*.local` / `*.home.arpa`）—— 局域网设备必须拿真实地址
- **功能类**（游戏机 / STUN / NTP）—— NAT 类型检测与时间同步需要真实可路由地址

⚠️ `always-real-ip` **只改变返回真实 IP 还是 Fake-IP，不改变流量的目的地**。
它不参与分流 —— 想让游戏机流量走代理，还得靠 `[Rule]` 里的 `DOMAIN-SUFFIX` 规则。

---

## 4 · `[Proxy]` 与占位符

### 4.1 四条占位节点

```
Node-A = hysteria2, 203.0.113.10, 52341, password=REPLACE_WITH_YOUR_PASSWORD, sni=REPLACE_WITH_YOUR_SNI
Node-B = hysteria2, 203.0.113.11, 52341, password=REPLACE_WITH_YOUR_PASSWORD, sni=REPLACE_WITH_YOUR_SNI
Node-C = https, cdn-relay.example.com, 443, username="REPLACE_WITH_USERNAME", password="REPLACE_WITH_PASSWORD", underlying-proxy="Node-B", sni=cdn-relay.example.com
Node-D = https, 203.0.113.20, 443, underlying-proxy="Node-A", skip-cert-verify=true, sni=203.0.113.20
```

| 节点 | 类型 | 角色 |
|:-----|:-----|:-----|
| `Node-A` | `hysteria2` | 落地节点（IP 字面量） |
| `Node-B` | `hysteria2` | 落地节点 ②，同时是 `Node-C` 的 `underlying-proxy` |
| `Node-C` | `https` | 中转链：经 `Node-B` 出去连 CDN 中转域名 |
| `Node-D` | `https` | 经 `Node-A` 中转 |

### 4.2 为什么 `download-bandwidth` 不写

`hysteria2` 的 `download-bandwidth` 是**服务端**拥塞控制提示。填一个偏大的值会让
服务端猛发、链路 buffering 撑爆（bufferbloat），填偏小则浪费带宽。除非服务商
明确公布数字，否则交给服务端自适应。

### 4.3 `https` 类型不支持 UDP 中继

这是 Surge 的代理类型限制，不是配置问题。后果：

- 落到 `Node-C` / `Node-D` 上的 UDP 请求会被拒绝（由
  `udp-policy-not-supported-behaviour = reject` 决定）；
- 所以它们**只放在 `AI` 组**，不做默认出口 —— AI 流量以稳定长连接为主，不靠 UDP；
- 反过来，需要 UDP 的场景（游戏、部分 QUIC 应用）必须走 `hysteria2`。

### 4.4 节点用 IP 还是域名

- `Node-A` / `Node-B` / `Node-D` 用 **IP 字面量** —— 不产生「解析节点域名」这一次查询。
  这是本配置里唯一**必定发生**的本地解析，能省则省。
- `Node-C` 用域名（`cdn-relay.example.com`）—— 中转链按域名走 CDN 就近解析是它的意义所在。

### 4.5 为什么 `Node-E = vless, …` 被注释掉

`vless` / `XTLS Reality` **不是 Surge 的原生代理类型**。写了会被跳过并告警，
只增加解析噪音。保留一行注释是给从 Clash 迁过来的读者看的。

---

## 5 · 占位符与脱敏规则

本仓库是公开模板，**所有节点信息都是占位符**。脱敏规则：

| 字段 | 占位形式 |
|:-----|:---------|
| 节点 IP | RFC 5737 文档地址段：`192.0.2.0/24`、`198.51.100.0/24`、`203.0.113.0/24` |
| 中转域名 | `cdn-relay.example.com`（`example.com` 是 RFC 2606 保留域） |
| 密码 / 用户名 | `REPLACE_WITH_YOUR_PASSWORD` / `REPLACE_WITH_USERNAME` |
| SNI | `REPLACE_WITH_YOUR_SNI` 或与 server 相同的 IP / 域名 |

这三类都是**国际标准保留给文档用的**，不会指向任何真实主机，也不会误导使用者。

检验由 `skill/tests/architecture.sh` 的第 ① 组断言自动完成：
非文档段 IPv4、非 `REPLACE_WITH_*` 凭据、不在允许清单的节点主机名、以及若干
禁止出现的敏感子串，任一命中即失败。

> 🔐 `docs/09-注意事项.md` 里明确写着：**不要把真实节点提交回来**。
> 改完本地用可以，`git push` 前跑一次 `architecture.sh`。

---

## 6 · `smart` / `select` 组的差别

### 6.1 `smart` 怎么打分

三个信号：

| 维度 | 说明 |
|:-----|:-----|
| 真实连接首字节延迟 | 主项，比 ping 更贴近实际体验 |
| TCP 重传率 | 每 1% 约折算 50 ms —— 丢包按时延折算才能进同一套评分 |
| UDP 响应延迟 | 单列。`https` 类型不支持 UDP，UDP 表现必须单独看 |

- 重测间隔固定 **5 分钟**
- **按站点记住最优策略** —— 所以「同一节点，A 站快 B 站慢」能自适应
- 成员越少选得越快

### 6.2 什么时候不该用 `smart`

`smart` 会**静默换节点**。如果你：

- 需要出口 IP 稳定（某些服务按 IP 做风控）
- 想知道「我现在到底走哪个节点」

那 `select` 更合适。`v0` 用的就是 `select` —— 它的用户诉求是「我看见什么就是什么」，
静默换节点是**意外行为**。代价是节点挂了要手动切。

### 6.3 本模板的分工

| 组 | 类型 | 理由 |
|:---|:-----|:-----|
| `Proxy` | `smart` | 日常流量，自动选最快 |
| `AI` | `smart` | 但成员是 `Node-C` / `Node-D` —— 出口与日常流量**物理隔离**，组内自动选 |
| `AD` | `select` | 手动开关，不由规则引用 |

---

## 7 · `underlying-proxy` 中转链

### 7.1 机制

```
Node-C = https, cdn-relay.example.com, 443, …, underlying-proxy="Node-B", …
                        │                                    │
                        │                                    └─ 先连它，再由它去连 cdn-relay
                        └─ 实际目标
```

`underlying-proxy` 指向的节点先建连，再由它去访问本节点。等价于一层手写链式代理。

### 7.2 两条硬约束

1. **被指向的名字必须存在**（在 `[Proxy]` 或 `[Proxy Group]` 里）。
   否则 Surge 会以「无法解析 `underlying-proxy`」**拒绝加载整份配置**。
   本文件里 `Node-C → Node-B`、`Node-D → Node-A`，都在同一个 `[Proxy]` 段里。
2. **不能形成环**。`A → B` 且 `B → A` 会让 Surge 拒绝加载。

### 7.3 改动顺序

改了节点名之后，**先确认 `underlying-proxy` 引用的新名字存在，再保存**。
这是本文件里唯一需要「按顺序改」的地方 —— 顺序错了会直接导致配置无法加载。

---

## 8 · `pre-matching` 与 `extended-matching`

### 8.1 `pre-matching`

让 REJECT 在 **DNS 查询阶段 / TCP-SYN 阶段**就被求值。
被拦的请求得到一个「No Record」或 TCP RST 就结束了，**连接层完全不会启动**。

这是全模板最大的一笔 CPU 与耗电优化。省的不只是带宽，是「解析 → 建连 →
等首字节 → 丢弃」这一整串唤醒。移动端省电的关键从来不是省流量，是少唤醒。

### 8.2 硬约束：策略必须是字面量

`pre-matching` 的规则，策略必须是 **REJECT 族的字面量策略名**。

**不能是策略组** —— 哪怕那个组只有 `REJECT` 一个成员。原因：策略组在运行时
可以解析成 `DIRECT`（例如组被切走、或组成员动态变化），Surge 无法据此保证
「一定拦得住」，于是**直接拒绝加载整份配置**。

⇒ 这是 `AD` 组「不由任何规则引用」的根因。规则里写字面量 `REJECT`，`AD` 组
留给面板上手动切 —— 但要让读者知道：**把 `AD` 切成 `DIRECT` 并不会关闭广告拦截**，
因为规则根本不经过它。想真正关掉，改规则那一行的策略或注释掉整行。

### 8.3 `extended-matching`

额外按 **TLS SNI / HTTP Host** 匹配。专治「App 直连 IP，域名规则失效」——
很多 App 会先解析出 IP 再直连，此时纯域名规则不再命中；`extended-matching`
从 TLS 握手里读 SNI 补上这一步。

⚠️ 本项目**没有**在 `AI.list` 那条规则上加它 —— 那条是分流不是拦截，
加 `extended-matching` 会让它按 SNI 匹配，与「域名规则集」的语义不符。
`check_surge_dns.py` 的 `check_10` 只对带 `pre-matching` 的规则提示缺
`extended-matching`，不给非拦截规则报负。

---

## 9 · `always-real-ip` 与 Fake-IP

### 9.1 两种模式

| 模式 | 对应用返回什么 | 后果 |
|:-----|:---------------|:-----|
| Fake-IP | 一个假地址（如 `198.18.x.x`），Surge 靠它反查域名 | 分流准确，但拿不到真实 IP |
| Real-IP | 真实地址 | 应用能拿到真实 IP，但分流会变弱（只能靠 IP） |

Surge 默认对走代理的域名用 Fake-IP，对 DIRECT 的域名用 Real-IP。

### 9.2 `always-real-ip` 强制某些主机名走 Real-IP

NAT 类型检测（STUN）、时间同步（NTP）、游戏机配对，都需要真实可路由地址 ——
给它们 Fake-IP 会直接坏掉。

⚠️ 再次强调：`always-real-ip` **不改变流量的目的地**。它只是让应用拿到真实 IP。

### 9.3 与规则顺序的关系

`always-real-ip` 里的主机名，如果在 `[Rule]` 里没有被域名规则接住，
就会走到后面的 IP 类规则 —— 而 IP 类规则带 `no-resolve`，对未解析的主机名**跳过**。

于是它们最终落 `FINAL → Proxy`，其解析必须由节点远端完成 —— 这本身没问题
（远端解析更准）。但**本地若需要它的地址**（NAT 检测要真实 IP），就会出问题。

⇒ 所以 `v1` 里有这三条：

```
DOMAIN-SUFFIX,nintendo.net,Proxy
DOMAIN-SUFFIX,playstation.net,Proxy
DOMAIN-SUFFIX,xboxlive.com,Proxy
```

用 `DOMAIN` 类规则（**无需 DNS**）先接住它们，让后面那些 IP 规则不必为了判它们而解析。

---

## 10 · `hijack-dns` 的边界

### 10.1 能拦什么

- 硬编码了知名公共解析器 IP（`8.8.8.8` 等）的设备
- 显式发往这些地址的 `:53` 查询

### 10.2 拦不住什么

- **DoH / DoT 客户端**：`https://dns.google/dns-query` 走 443，不是 `:53`。
  `hijack-dns` 管不到。唯一办法是让那个 App 走代理，或承认它（多数情况下 DoH 本身
  是加密的，不算「明文泄露」）。
- **自建解析器**：企业内网 DNS、某些路由器的 `192.168.x.1:53`。要覆盖得显式列。
- **`:53` 之外的端口**：非标准端口上的 DNS。
- **不经过 Surge 的流量**：例如另一个 VPN、或 Surge 未接管时。

### 10.3 要不要写 `hijack-dns = *`

| | 列具体地址（本模板） | 写 `*` |
|:--|:---------------------|:-------|
| 覆盖面 | 6 个最常见 | 全部 `:53` |
| 风险 | 少量自建解析器 / 冷门公共解析器漏掉 | 极少数依赖原生 `:53` 行为的应用可能异常 |
| 审计读数 | LOW（「未覆盖 N 个知名解析器」） | OK |

本模板选列具体地址，因为「覆盖面足够 + 行为可预测」比「一网打尽 + 边界情况未知」更稳。
想换就改一行。

> ⚠️ 审计器**不会**因为「列得少」判负 —— 第一版按条数判负是错的（`:53` 的地址空间
> 是无限的，列举永远不可能「列全」）。现在的判据是「还有多少**已知的**知名境外
> 解析器没被覆盖」，且只报 LOW。

---

## 11 · 规则集与刷新

### 11.1 引用清单

| 规则集 | 条数 | 类型 | 上游 |
|:-------|:----:|:-----|:-----|
| `surge-white-guard.list` | 43 | 纯域名 | jinx-ads-rules |
| `surge-ads.list` | 3891 | 纯域名 | jinx-ads-rules |
| `AI.list` | 49 | 纯域名 | ACL4SSR（**钉 commit**） |
| `private.txt` | 130 | 域名 + 可能含 IP | Loyalsoldier |
| `direct.txt` | 111169 | 纯域名 | Loyalsoldier |
| `SYSTEM` / `LAN` | — | 内置 | Surge |

### 11.2 `update-interval=86400`

远程 `RULE-SET` 都带按天刷新。这是**必须**的 —— 上游新收录的广告域名否则会一直命不中。

⚠️ 同一个键只应该写在一处。源配置里 `update-interval=3600` 曾写在 `[Proxy Group]`
的 `smart` 组上 —— 那只对订阅型组有意义，写在那里是空转。本模板已移除。

### 11.3 为什么 `AI.list` 钉了 commit

```
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/75f01010…/Clash/Ruleset/AI.list,AI,…
                                                      ^^^^^^^^ 40 位 commit hash
```

`AI` 组的出口隔离是有意设计的，如果 `AI.list` 的内容随上游分支漂移，
「哪些域名走 AI 组」就会悄悄改变。钉 commit 让这个集合**可复现**。

代价：上游更新了不会自动跟进。要更新得手动换 hash。

### 11.4 为什么 `direct.txt` 是主承重墙

见 §12。

---

## 12 · `no-resolve` 的双刃

这是全项目最需要注意的一处，也是 [`docs/05`](../docs/05-分流与no_resolve必须成对交付.md)
整篇复盘的由来。

### 12.1 刀刃一：不带 `no-resolve` → 触发解析

```
GEOIP,CN,DIRECT       # 每个走到这里的域名都要被解析一次
```

### 12.2 刀刃二：带上 `no-resolve` → 不再匹配域名

```
GEOIP,CN,DIRECT,no-resolve    # 对未解析的主机名直接跳过
```

于是「**解析出来发现是国内 IP 就直连**」这条路**也一起没了**。
国内域名不再被 `GEOIP,CN` 接住。

### 12.3 后果

如果没有别的规则接住国内域名，它们会全部落到 `FINAL → Proxy` ——
**国内网站整片走代理**。

而更糟的是：两个审计脚本当时**双双通过**，因为
- `check_surge_dns.py` 审的是**结构**（顺序、`no-resolve`、策略可解析）；
- `audit_ruleset_content.py` 数的是**规则集条目类型**。

两者都不会问「一个国内域名走完这份规则，最后去哪」。

### 12.4 修法：两条判据必须成对交付

> **A** —— 所有 IP 类规则带 `no-resolve`
> **B** —— `FINAL` 之前有一个**域名体量足够**的国内直连规则集

只交 A 会漏分流，只交 B 会漏 DNS。**必须一起。**

本模板的 B 是 `direct.txt`（11 万条**域名**条目）。
`skill/tests/architecture.sh` 把这两条都写成了断言。

### 12.5 一个配套的假通过陷阱

审计国内直连时，**只测 `.cn` 域名会假通过** ——
这种配置靠的是 `DOMAIN-SUFFIX,cn` 这条兜底，不是真的接住了国内域名。

`audit_routing_coverage.py` 的 17 个国内探针里**刻意混入非 `.cn`** 的：
`qq.com` / `taobao.com` / `miui.com` / `bilibili.com` / `jd.com` …
（见脚本里的注释：「只有 `.cn` 后缀能直连的配置是**假通过**」）。

---

## 13 · `[Proxy Group]`：三个组与两个「不能用组」的地方

### 13.1 三个组

```
Proxy = smart, "Node-A", "Node-B", icon-url=…/Proxy.png
AI    = smart, "Node-C", "Node-D", icon-url=…/openai.png
AD    = select, REJECT, DIRECT, icon-url=…/AdBlock.png
```

| 组 | 类型 | 承载 | 被谁引用 |
|:---|:-----|:-----|:---------|
| `Proxy` | `smart` | `Node-A` / `Node-B` | `FINAL` + 3 条游戏机域名 |
| `AI` | `smart` | `Node-C` / `Node-D` | `AI.list` |
| `AD` | `select` | `REJECT` / `DIRECT` | **没有任何规则引用** |

### 13.2 不能用组的地方 ①：`pre-matching`

见 §8.2。`pre-matching` 的规则策略**必须是字面量 REJECT 族**，写成组会加载失败。
所以广告拦截写的是 `REJECT` 而不是 `AD`。

### 13.3 不能用组的地方 ②：`AD` 组的定位陷阱

`AD` 组看起来像「广告开关」，但：

- 规则里的广告拦截写的是字面量 `REJECT`，**不经过 `AD` 组**；
- 所以在面板上把 `AD` 切成 `DIRECT`，**不会**关闭广告拦截。

`AD` 组的真实用途是「临时放行全部广告时不用改规则文件」—— 但当前配置下它做不到这件事。

> 📌 这是本模板**已知的语义冗余**。保留它是因为：① 面板上有个开关看着直观；
> ② 想真正用起来，把 `[Rule]` 里那条 `RULE-SET,…,surge-ads.list` 的策略从
> `REJECT` 改成 `AD` 即可 —— 但要注意**改完那行就不能带 `pre-matching` 了**
> （见 §8.2），也就是会失去最大那笔耗电优化。**这是个明确的取舍，不是笔误。**

### 13.4 为什么 `AI` 组要独立

不是「更细」，是**出口隔离**：

- AI 服务的风控对出口 IP 的稳定性敏感；
- `Proxy` 是 `smart`，会按站点静默换节点 —— 出口 IP 飘忽反而有害；
- 独立组可以把 AI 出口钉在专门的节点上（示例里是 `Node-C` / `Node-D`）。

### 13.5 组名与成员名的大小写

Surge 的组名 / 节点名引用**不区分大小写地可解析**，但 `check_surge_dns.py`
的 `check_7` 会同时按原名与全小写匹配，避免把 `Proxy` 与 `proxy` 判成两个东西。

---

## 14 · `[Rule]`：12 条逐条

`[Rule]` 是**有序的** —— 自上而下匹配，**第一条命中即决定去向**。

| # | 规则 | 策略 | 选项 | 为什么排这里 |
|:-:|:-----|:----:|:-----|:-------------|
| 1 | `RULE-SET,…,surge-white-guard.list` | `DIRECT` | — | **必须**在 REJECT 之前，否则形同虚设 |
| 2 | `RULE-SET,…,surge-ads.list` | `REJECT` | `pre-matching,extended-matching` | 黑名单。必须在 `direct.txt` / `GEOIP,CN` **之前** —— 否则国内广告域名被 `direct.txt` 接走 |
| 3 | `RULE-SET,…,AI.list` | `AI` | `update-interval=86400,no-resolve` | 纯域名集，显式 `no-resolve` |
| 4 | `DOMAIN-SUFFIX,nintendo.net` | `Proxy` | — | 见 §9.3 |
| 5 | `DOMAIN-SUFFIX,playstation.net` | `Proxy` | — | 同上 |
| 6 | `DOMAIN-SUFFIX,xboxlive.com` | `Proxy` | — | 同上 |
| 7 | `RULE-SET,SYSTEM` | `DIRECT` | — | Apple 激活 / 推送 / 定位 / 配对，内置权威集合 |
| 8 | `RULE-SET,LAN` | `DIRECT` | `no-resolve` | 含 IP-CIDR，**必须** `no-resolve` |
| 9 | `RULE-SET,…,private.txt` | `DIRECT` | `no-resolve` | 内网域名 |
| 10 | `RULE-SET,…,direct.txt` | `DIRECT` | `no-resolve` | **主承重墙**，11 万条域名。见 §12 |
| 11 | `GEOIP,CN,DIRECT` | `DIRECT` | `no-resolve` | IP 类规则，放最后 |
| 12 | `FINAL,Proxy,dns-failed` | `Proxy` | `dns-failed` | 兜底 |

### 14.1 铁律

**白名单(DIRECT) → 黑名单(REJECT) → 常规分流（`direct.txt` / `GEOIP,CN`）**

REJECT 绝不能排在 `direct.txt` / `GEOIP,CN` 之后 —— 那等于白加，
因为国内广告域名会先被 `direct.txt` 接走。

### 14.2 为什么 IP 类规则必须放最后

IP 类规则需要有已解析的地址。放在所有域名规则之后，使走代理 / 被广告拦截 /
国内直连的流量都**不必做本地 DNS 查询**。

### 14.3 `FINAL` 的 `dns-failed`

万一规则求值因 DNS 失败而中断，用代理策略而不是让请求直接失败。
走代理的域名由节点远端解析 —— 所以这一条既修好了失败，也**避免了一次明文本地查询**。

---

## 15 · 审计体系

### 15.1 三个脚本

| 脚本 | 审什么 | 需要联网 |
|:-----|:-------|:--------:|
| `check_surge_dns.py` | 文件内部的**结构**（12 项检查） | ❌ |
| `audit_ruleset_content.py` | **远程规则集的内容**（缺 no-resolve 的 IP 条目 / 直连集合的域名体量） | ✅ |
| `audit_routing_coverage.py` | 拿**真实域名走一遍** `[Rule]`，看最终去哪 | ✅ |
| `skill/tests/architecture.sh` | 三条项目不变量（占位符纪律 / DNS 段一致性 / 规则顺序铁律） | ❌ |
| `skill/tests/check_links.py` | markdown 相对链接与锚点（改标题后**静默失效**的那一类问题） | ❌ |

### 15.2 为什么需要三个而不是一个

它们回答的是**不同层次**的问题：

- `check_surge_dns.py`：「这份文件自洽吗？」
- `audit_ruleset_content.py`：「它引用的东西里有雷吗？」（profile 里看不见）
- `audit_routing_coverage.py`：「一个真实请求进来，实际去哪？」（结构全绿也可能错）

第三个是 Egern 项目的教训换来的：**两个审计脚本双双通过，分流却整片是坏的。**

### 15.3 豁免机制

`# audit-waive: <检查号> <理由>` 写在 **profile 里**，不写在审计器里。

| | 写在审计器 | 写在 profile |
|:--|:-----------|:-------------|
| 影响面 | 判据被**永久**削弱，别的 profile 也失去保护 | 只豁免这一份 |
| 可追溯 | 要去读代码 | 在**被豁免的对象旁边**，可 grep |
| 改配置的人 | 看不到 | 一定看到 |

豁免把 finding 降级为 `WAIVED:` 并**照常逐条打印** —— 不改判定语义的前提是它仍然可见。

### 15.4 共享模块 `_surge_common.py`

所有脚本从这里 import 判据。背景是 Egern 项目里两个脚本各自实现了一份
「端点主机名解析」逻辑 —— **判据本体同步了、喂给判据的 helper 没同步**，
同一份配置给出相反结论。

⇒ 教训：**靠注释提醒同步两份拷贝是不可靠的。** 从结构上消灭拷贝。

### 15.5 `policy_index()` —— 最容易写错的一处

```python
# 有匹配值：DOMAIN-SUFFIX,x.com,POLICY / GEOIP,CN,DIRECT / RULE-SET,SET,POLICY
#          → 策略恒为 index 2
# 无匹配值：FINAL,POLICY → 策略为 index 1
```

**`GEOIP` 属于「有匹配值」**（匹配值是 `CN`）。第一版把它归错了组，
于是把 `CN` 当成策略名，报出「规则引用了未定义的策略 `CN`」这个**假 HIGH**。
同一处还漏掉了 `RULE-SET` 的 index 1 是规则集标识而不是策略。

> 判据写错方向比漏报更危险 —— 它会让使用者去改一条**本来正确的**规则。

### 15.6 全绿 ≠ 可用

审计脚本只覆盖**静态可判定**的部分。拦截效果、误杀、节点可用性必须实测。
这是 Egern 项目连续 5 次「脚本全绿、实测仍有问题」换来的结论。

---

## 16 · 已知取舍

### 16.1 `proxy-test-url` 用国内端点

源配置是 `http://www.gstatic.com/generate_204`（境外）。本模板改成
`http://connect.rom.miui.com/generate_204`。

理由：`proxy-test-url` **每 5 分钟被每个组各跑一遍**，是持续性动作。
用境外端点等于制造一个必然发生的境外域名解析面。改成国内后：

- 解析被 `direct.txt` 接住，走直连，不进代理链；
- 国内 204 的 RTT 方差小，测出的分数更能反映节点本身。

⚠️ 注意区分：`proxy-test-url` 决定测速用什么，`proxy-test-udp` 决定 UDP 测速用什么。

### 16.2 保留 2 个主机名形式的加密 DNS 端点

`dns.google` / `dns.alidns.com` 会被引导解析一次。换成纯 IP 字面量能消掉，
但会失去两项收益：

1. **按域名走 CDN 就近解析**；
2. **ECS 合规**（不把公网 IP 交给非 CDN 的解析器）。

已在 profile 内用 `# audit-waive: 1` 声明（详见 §15.3）。
想彻底消掉就把它们换成 IP 字面量，同时删掉那行 waive。

### 16.3 `hijack-dns` 不穷举

见 §10.3。

### 16.4 `AD` 组的语义冗余

见 §13.3。

### 16.5 `v0` 的三点代价

移除白名单守卫 / AI 合流 / `Proxy` 是 `select`。
详细写在 [`profiles/v0.conf`](../profiles/v0.conf) 末尾 —— 刻意放在**改动发生的地方**，
因为改的人不会去看 `docs/`。

### 16.6 兜底指 `Proxy` 而非国内组

本模板不做「分流兜底的境内 / 境外切分」—— 兜底一律 `Proxy`。
国内直连靠 `direct.txt` + `GEOIP,CN` 正面覆盖，不靠兜底。

---

## 17 · FAQ

**Q：我照抄了，但国内网站慢 / 打不开。**

先跑 `python skill/scripts/audit_routing_coverage.py profiles/v1.conf`。
若国内探针没命中 `DIRECT`，检查两条：① 有没有删掉 `direct.txt` 那条规则；
② 有没有把 `GEOIP,CN` 挪到域名规则前面。

**Q：`GEOIP,CN` 加了 `no-resolve` 之后国内 IP 还判得准吗？**

判得准，但**前提是它前面有域名类规则接住国内域名**。`no-resolve` 只是
「对未解析的主机名跳过」，已经解析出 IP 的请求照常判。见 §12。

**Q：为什么广告拦截不指向 `AD` 组？**

见 §8.2 / §13.3。`pre-matching` 要求字面量策略；且 `AD` 可被切成 `DIRECT`，
Surge 无法保证「一定拦得住」。

**Q：`smart` 组一直换节点，我想固定。**

把 `Proxy = smart, …` 改成 `select`。或把 `AI` 的成员单独钉一个节点。

**Q：我删了 `# audit-waive:` 那行，为什么突然报 HIGH？**

那是有语义的注释，不是说明文字。见 §15.3。

**Q：能不能只保留 `encrypted-dns-server`，去掉 `dns-server`？**

不建议。`dns-server` 承担引导与连通性测试职责。去掉后 Surge 会用系统 DNS
（运营商 DHCP 下发的那台）—— 正是出口 ①。

**Q：iOS 上怎么用？**

Surge iOS 版不支持本地文件配置，需要把 profile 内容托管到一个可访问的地址
（Gist / 自己仓库），再用 URL 导入。`icons/` 里的图标地址已是绝对 URL，
不依赖本地路径。

---

## 18 · 维护者须知

### 18.1 改动前必须知道的三条

1. **DNS 段不许只改一个版本。** `v0` / `v1` 的 16 个 DNS 键由测试逐字比对。
   要改就两个一起改。
2. **规则顺序铁律不许破。** 白名单 → REJECT → 域名类直连 → IP 类 → `FINAL`。
3. **节点不许提交真实值。** `architecture.sh` 会拦。

### 18.2 加第三个版本

见 [`docs/07`](../docs/07-文件版本沿革.md) §6 的 6 条清单 —— 那 6 条就是
`architecture.sh` 的全部断言。**能过测试的版本才叫一个新版本。**

### 18.3 全部验证都在本地

```bash
bash skill/tests/run.sh              # 5 阶段，13 个断言
SKIP_NET=1 bash skill/tests/run.sh   # 跳过联网阶段
```

⚠️ **本仓库刻意不挂 CI / 任何自动化**。理由与替代做法见
[`skill/README.md`](../skill/README.md)。

### 18.4 退出码约定

| 码 | 含义 |
|:--:|:-----|
| 0 | 通过 |
| 1 | 有发现（审计器）/ 有断言失败（测试） |
| 2 | **环境故障**（解释器坏、文件缺失、用法错误） |

⚠️ 退出码 2 是必须的：`run.sh` 的 `bad_*` fixture **期望退出码 1**。
如果解释器坏掉，脚本也返回 1 —— 会被误判成「判负通过」。**审计器的故障
绝不能被计成一次成功的判负。**
