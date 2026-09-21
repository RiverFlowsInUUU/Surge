<div align="center">

# 🛡️ Surge 防 DNS 泄露配置模板

### 让 DNS 无处可漏

*不绑定节点，不绑定订阅。只做一件事：消除 DNS 泄露面。*

[![Surge](https://img.shields.io/badge/Surge-iOS%20%7C%20macOS-1f6feb?style=flat-square)](https://github.com/RiverFlowsInUUU/surge-anti-dns-leak)
[![DNS](https://img.shields.io/badge/DNS-Zero%20Leak-2ea043?style=flat-square)](https://github.com/RiverFlowsInUUU/surge-anti-dns-leak)
[![Profiles](https://img.shields.io/badge/Profiles-lazy%20%7C%20routing-0969da?style=flat-square)](https://github.com/RiverFlowsInUUU/surge-anti-dns-leak)
[![Rules](https://img.shields.io/badge/Rules-13%20%7C%2026-8250df?style=flat-square)](https://github.com/RiverFlowsInUUU/surge-anti-dns-leak)
[![License](https://img.shields.io/badge/License-MIT-dfb317?style=flat-square)](docs/10-图标与许可.md)

[快速开始](#-快速开始) · [两份配置](#-两份配置) · [文件结构](#-文件结构) · [防泄露原理](#-防泄露原理) · [策略组结构](#-策略组结构) · [规则顺序](#-规则顺序) · [规则来源](#-规则来源) · [更多文档](#-更多文档)

</div>

## 📥 复制链接

🪶 **懒人版** —— 一个出口，不想调

```
https://raw.githubusercontent.com/RiverFlowsInUUU/surge-anti-dns-leak/main/profiles/lazy.min.conf
```

🧭 **分流版** —— 按应用 + 按地区

```
https://raw.githubusercontent.com/RiverFlowsInUUU/surge-anti-dns-leak/main/profiles/routing.min.conf
```

**怎么用**：鼠标移到上面灰框的右上角，点 **复制图标** → Surge 里
**配置 → 从 URL 下载** → 粘贴 → 导入。两个版本**选一个用，不要叠加**。

> 💡 这两条是**纯配置版**，导入即用。想读带注释的版本（同样内容 + 大段注释）：
> [🐈 `lazy.conf`](profiles/lazy.conf) · [🐈 `routing.conf`](profiles/routing.conf)
> ⚠️ 链接都指向 `main` 分支，我会持续更新 —— 想锁定某天的版本请自行 fork。

---

## 🚀 快速开始

先选一份配置（两版的区别见[两份配置](#-两份配置)）：

```
🪶 懒人版                           🧭 分流版
1️⃣ 拿配置  上面复制链接的第 1 条     1️⃣ 拿配置  上面复制链接的第 2 条
2️⃣ 填节点  [Proxy] 的 4 条占位       2️⃣ 填节点  [Proxy] 的 7 条占位
3️⃣ 填充值  如有的话                  3️⃣ 填订阅  Airport 组的 policy-path
4️⃣ 导入    Surge                    4️⃣ 填充值  如有的话
                                    5️⃣ 导入    Surge
```

**要填什么**

| 位置 | 🪶 懒人版 | 🧭 分流版 | 必填 |
|:-----|:----------|:----------|:----:|
| `[Proxy]` 节点 | 4 条（`203.0.113.x` + `REPLACE_WITH_*`） | 7 条，**节点名带地区关键词** | ✅ |
| `[Proxy Group]` 组成员 | `"Node-A"` … | 自动从节点名筛出，通常不用改 | ✅ |
| 订阅槽位 | — | `Airport` 组 `policy-path` 的 `REPLACE_WITH_YOUR_TOKEN` | ⬜ 可选 |
| 测试端点（可选） | `internet-test-url` 国内 / `proxy-test-url` 境外 | 同左 | ⬜ 可选 |

> ⚠️ 分流版的节点名**要带地区关键词**（`HK` / `US` / `JP` / `SG` …），
> 因为地区组是用正则按**节点名**筛的。改名规则见 [`docs/11` §4](docs/11-分流版设计.md)。
> 不填订阅槽位也能用 —— 那份组会自动留空，只跑你自己手写的节点。

**从 URL 导入时，节点要自己填**（下载到的文件里是占位符）。
想先在本地改好再导入？用带注释的 [`lazy.conf`](profiles/lazy.conf) / [`routing.conf`](profiles/routing.conf)，
两者与上面的 `.min.conf` **内容完全一致**，只多注释。

📄 **两份形态**：每份配置都有 `.conf`（带注释）与 `.min.conf`（纯配置），内容一致，只差注释，取用其一即可。

---

## 🧭 两份配置

**不是版本关系，是分工关系。选一份用，不要叠加。**

| | 🪶 懒人版 | 🧭 分流版 |
|:--|:----------|:----------|
| 文件 | `lazy.conf` / `lazy.min.conf` | `routing.conf` / `routing.min.conf` |
| 策略组 | 3 个 | 26 个 |
| 规则 | 13 条 | 26 条 |
| 出口粒度 | `Proxy` / `AI` / `AD`，全量一个出口 | 按**应用**分（ChatGPT / Google / GitHub … 共 14 组），组内再按**地区**分 |
| 适合 | 只想通、不想调 | 想让 ChatGPT 走美国、Claude 走台湾 |

两份都带：**防 DNS 泄露结构** + **广告拦截（含白名单守卫）** + **局域网共享**。
且 `[General]` 的 16 个 DNS 相关键**逐字相同** —— 防泄露标准不因分流粒度而变（由测试断言）。

```
1️⃣ 拿配置   →   复制链接的第 1 条（懒人）或 第 2 条（分流）
2️⃣ 填节点   →   [Proxy] 段的占位节点
3️⃣ 填订阅   →   仅分流版需要：Airport 组的 policy-path
4️⃣ 导入     →   Surge
```

> 📌 分流版专有的三处设计约束（`flatten` 的对应写法 / Smart 组不能嵌套组 / 地区关键词双份）
> 见 [`docs/11-分流版设计.md`](docs/11-分流版设计.md)。

---

## 📁 文件结构

```
surge-anti-dns-leak/
├── 📁 profiles/            # 4 份配置 = 2 种分工 × 2 种形态（带注释 / 纯配置）
├── 🖼️ icons/               # 策略组图标（已内置，不跨项目引用）
├── 📚 docs/                # 11 篇专题（原理 / 清单 / 逐段讲解 / 分流版设计 / 审计读数 等）
├── 📘 DetailsReadme/       # 完整技术文档
├── 🗓️ CHANGELOG.md         # 更新日志（按时间倒序）
└── 🧪 skill/               # 方法论（SKILL.md + reference/）+ 4 个审计脚本 + 回归测试
```

---

## 🌐 防泄露原理

Surge 的 DNS 泄露只有三条出口，配置把三条都堵上。

| 出口 | 机制 | 本模板怎么堵 |
|:----:|:-----|:-------------|
| 🚪 **引导解析** | `encrypted-dns-server` / `dns-server` 里若是主机名，必须先明文解析一次 | 端点写 IP 字面量；`dns-server` 写裸 IP，**绝不用 `system`** |
| 🚪 **旁路设备** | 忽略 Surge DNS 的设备（HomePod / Apple TV / 智能音箱）直接发明文 `:53` | `hijack-dns` 把这些查询接管回来 |
| 🚪 **规则触发解析** | 不带 `no-resolve` 的 IP 类规则会**主动**发起解析 | 所有 IP 类规则一律带 `no-resolve`（含第三方规则集，见 §审计） |

三者叠加后，明文 `UDP:53` 没有任何一条通路是"必然被走到"的。

> 🔍 完整推导（含"为什么 `pre-matching` 是最大的一笔耗电优化"）见 [`DetailsReadme` §2](DetailsReadme/DetailsReadme.md#2--防泄露原理从机制到推导) 与 [`docs/02`](docs/02-DNS为什么会泄露.md)。

---

## 🎯 策略组结构

两版差异很大：`lazy.conf` 是 **3 个组 / 13 条规则**，`routing.conf` 是 **26 个组 / 26 条规则**。

### 🪶 `lazy.conf` —— 3 个组

**✈️ 节点** —— 4 条占位节点

- 🅰️ `Node-A` · `hysteria2` —— 落地节点（IP 字面量）
- 🅱️ `Node-B` · `hysteria2` —— 落地节点 ②，同时是中转链的 `underlying-proxy`
- 🅲 `Node-C` · `https` —— 中转链：经 `Node-B` 出去连 CDN 中转域名
- 🅳 `Node-D` · `https` —— 经 `Node-A` 中转

**🎛️ 三个策略组**

- 🧭 `Proxy` · `smart` —— 主入口，承载 `Node-A` / `Node-B`，按真实首字节延迟 + 重传 + UDP 响应评分
- 🤖 `AI` · `smart` —— AI 流量独立出口，承载 `Node-C` / `Node-D`，承接 `AI.list`
- 🛑 `AD` · `select` —— 独立手动开关（`REJECT` / `DIRECT`），不牵动规则引擎

### 🧭 `routing.conf` —— 26 个组

**✈️ 节点** —— 7 条占位节点，**节点名里带地区关键词**，供下面的正则筛选：
`Node-HK-01` / `Node-HK-02` / `Node-US-01` / `Node-JP-01` / `Node-SG-01` / `Node-Relay-01` / `Node-Relay-02`

**🎛️ 五层结构**

| 层 | 组 | 类型 | 作用 |
|:---|:---|:----:|:-----|
| 🎯 总入口 | `Proxy` / `Smart` | `smart` | 全部节点参与打分，自动选最快 |
| 📡 订阅 | `Airport` | `select` | `policy-path` 订阅槽位，`hidden=true` |
| 🌏 地区 | `Hong Kong` / `USA` / `Japan` / `Taiwan` / `Singapore` / `Korea` / `Other Regions` | `smart` | 用 `policy-regex-filter` **按节点名正则筛**出同地区节点 |
| 💎 精选 | `MAX` | `smart` | 只筛**倍率为 `0.x`** 的节点（`policy-regex-filter` 用负向断言匹配倍率） |
| 🧩 应用 | `ChatGPT` / `Gemini` / `Claude` / `AI` / `Google` / `Spotify` / `YouTubeMusic` / `YouTube` / `Telegram` / `Twitter` / `GitHub` / `Microsoft` / `WeChat` / `Final` | `select` | **把地区组当子节点列进去**，需要时可手动切地区 |
| 🛑 开关 | `AD` | `select` | 同 lazy，独立手动开关 |

**🧩 应用组各自的默认取向**（与 egern v2.5 对齐；括号内是首项）：

| 应用 | 默认 | 说明 |
|:-----|:----:|:-----|
| ChatGPT · Gemini · Claude | 代理 | Claude 例外：默认走 **台湾** 组 |
| Google | 代理 | 首项是 **`Gemini` 组** —— 即「Google 走 Gemini → Proxy」，多一层可切 |
| Spotify · YouTubeMusic · YouTube | 代理 | 媒体类，默认总出口，可切地区 |
| Telegram · Twitter | 代理 | 社交类，默认总出口，可切地区 |
| GitHub | 代理 | 开发者服务，默认总出口，可切地区 |
| Microsoft | **DIRECT** | 微软国内可直连，走代理反而慢；需要时面板切 Proxy |
| WeChat | **DIRECT** | 微信直连，**存在的意义是把它从兜底里摘出来**，别被 `Final` 送进代理 |

> 📌 拦截动作走**字面量 `REJECT`**（为了拿到 `pre-matching` 的 DNS 阶段拦截能力），
> `AD` 组则作为**独立的手动干预入口**保留 —— 这是刻意的分层。说明见 [`DetailsReadme` §13.3](DetailsReadme/DetailsReadme.md#133-ad-组的定位独立的手动开关)。
>
> 📌 地区组为什么能"按节点名筛"、`MAX` 的倍率正则怎么写、以及
> **Smart 组为什么不能把其他组当子策略**，见 [`docs/11-分流版设计.md`](docs/11-分流版设计.md) §3–§4。

---

## 📋 规则顺序

`[Rule]` 是**有序的** —— 自上而下匹配，**第一条命中即决定去向**，后面的不再看。

两版**共用同一条骨架**，只在「按应用分流」和「兜底」两段不同：

| 分类 | 🪶 `lazy.conf`（13 条） | 🧭 `routing.conf`（26 条） |
|:-----|:------------------------|:---------------------------|
| 🛡️ ① 白名单守卫 | `surge-white-guard.list`（43 条） | 同左 |
| 🚫 ② 广告拦截 | `surge-ads.list`（3891 条） | 同左 |
| 🤖 ③ 按应用分流 | `AI.list`（49 条） → `AI` | **拆成 13 条**，按厂商 / 应用分家（见下） |
| 🎮 ④ real-ip 主机名 | `nintendo.net` / `playstation.net` / `xboxlive.com` | 同左 |
| 🍎 ⑤ Apple 服务 | `SYSTEM` + `Apple_All_No_Resolve.list` | 同左 |
| 🏠 ⑥ 内网直连 | `LAN` / `private.txt` | 同左 |
| 🇨🇳 ⑦ 国内直连 | `direct.txt`（11 万条域名） | 同左 |
| 🌏 ⑧ GeoIP CN | 中国 IP | 同左 |
| 🌐 ⑨ 兜底 | `default` → `Proxy` | **`Final` 组**（可手动改道） |

**③ 按应用分流：一版够用，一版可挑**

- 🪶 `lazy.conf` —— 只有 `AI.list` 一条，全部 AI 流量走 `AI` 组，**不用挑**。
- 🧭 `routing.conf` —— 拆成 13 条，按厂商 / 应用分家，**可以给不同厂商挑不同地区**：

  | 段 | 规则集 | 去向 |
  |:---|:-------|:-----|
  | 🤖 AI 厂商 | `OpenAI.list` | `ChatGPT` |
  | | `Gemini.list` | `Gemini` |
  | | `Anthropic.list` + `Claude.list` | `Claude` |
  | | `AI.list`（49 条） | `AI` |
  | 🎬 媒体社交 | `Spotify.list` | `Spotify` |
  | | `YouTubeMusic.list` | `YouTubeMusic` |
  | | `YouTube.list` | `YouTube` |
  | | `Telegram.list` | `Telegram` |
  | | `Twitter.list` | `Twitter` |
  | 🪟 开发系统 | `GitHub.list` | `GitHub` |
  | | `Google.list` | `Google` |
  | | `Microsoft.list` | `Microsoft` |
  | 💬 即时通讯 | `WeChat.list` | `WeChat` |

  **两处顺序是刻意的**：

  1. **厂商专属规则必须排在通用 `AI.list` 之前** —— 否则 AI 域名先被 `AI.list` 接走，
     `ChatGPT` / `Gemini` / `Claude` 组永远轮不到。
  2. **`GitHub.list` 必须排在 `direct.txt` 之前** —— `github.com` 同时被国家直连清单收录，
     靠后的规则接不到它，应用的代理取向就失效了。
     （白名单守卫那条 `DIRECT` 排在更前面，两者不冲突：它只管「别被广告规则误杀」。）

  之所以 `Anthropic.list` 和 `Claude.list` 并列同一去向，是因为两个上游集覆盖面不同，**取并集更稳**。

**⑨ 兜底：一版硬指，一版可改道**

- 🪶 `lazy.conf` —— `FINAL` 直接指向 `Proxy`，没有可改的余地。
- 🧭 `routing.conf` —— `FINAL,Final,dns-failed`，兜底指向 `Final` **选择组**，
  平时跟 `Proxy` 行为一致，需要时可在面板上手动改道。

**两版都遵守的铁律**

1. **白名单(DIRECT) → 黑名单(REJECT) → 常规分流（`direct.txt` / `GEOIP,CN`）**。
   REJECT 绝不能排在 `direct.txt` / `GEOIP,CN` 之后 —— 那等于白加。
2. **IP 类规则（`LAN` / `private.txt` / `direct.txt` / `GEOIP,CN`）必须带 `no-resolve`，
   且必须排在 `FINAL` 之前。** 这两件事是一体的：补了 `no-resolve` 就关掉了「解析后判 IP 归属」这条直连路径，
   所以**域名体量足够的国内直连集必须一起交付**，否则国内域名整片落进兜底组。
3. **`pre-matching` 的策略必须是字面量 `REJECT`**，不能是策略组 —— 组在运行时可能解析成 `DIRECT`，
   Surge 会**直接拒绝加载整份配置**。

> 📌 逐条清单（lazy 13 条 / routing 26 条）与「为什么 IP 类规则必须放最后」见
> [`DetailsReadme` §14](DetailsReadme/DetailsReadme.md#14--rule两版规则顺序) 与 [`docs/11` §5](docs/11-分流版设计.md)。

---

## 📚 规则来源

- 🛑 [RiverFlowsInUUU/jinx-ads-rules](https://github.com/RiverFlowsInUUU/jinx-ads-rules) —— 广告拦截 + 白名单守卫
- 🤖 [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) —— 各应用规则集（OpenAI / Gemini / Spotify / YouTube / GitHub / Google / Microsoft / WeChat …）
- 🤖 [ACL4SSR/ACL4SSR](https://github.com/ACL4SSR/ACL4SSR) —— `AI.list`
- 🇨🇳 [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules) —— `direct.txt` / `private.txt`
- 🗺️ [adysec/IP_database](https://github.com/adysec/IP_database) —— `GeoLite2-Country.mmdb`
- 🧭 [RiverFlowsInUUU/egern-anti-dns-leak](https://github.com/RiverFlowsInUUU/egern-anti-dns-leak) —— 分流版的应用分组与地区取向参考

---

## 📖 更多文档

- ⚠️ [`docs/09-注意事项.md`](docs/09-注意事项.md) —— 使用前必看：规则集刷新 · 刻意不挂 CI
- 🎨 [`docs/10-图标与许可.md`](docs/10-图标与许可.md) —— 图标来源 · MIT 许可 · 第三方版权
- 🗓️ [`CHANGELOG.md`](CHANGELOG.md) —— 更新日志（按时间倒序，遵循 Keep a Changelog）
- 📘 [`DetailsReadme/`](DetailsReadme/) —— 逐段详解 · 原理推导 · 已知取舍 · FAQ
- 🧭 [`docs/11-分流版设计.md`](docs/11-分流版设计.md) —— 分流版：`flatten` 的对应写法 · Smart 组不能嵌套组 · 地区关键词双份
- 📂 [`docs/`](docs/) —— 其余 9 篇专题：DNS 怎么工作 / 为什么泄露 / 加固清单 / 逐段讲解 / 审计读数 …
- 🧪 [`skill/`](skill/) —— 4 个审计脚本、回归测试与方法论

---

<div align="center">

🛡️ 让 DNS 无处可漏 · MIT License · [图标与许可](docs/10-图标与许可.md)

</div>
