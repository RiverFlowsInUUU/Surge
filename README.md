<div align="center">

# 🛡️ Surge 防 DNS 泄露配置模板

### 让 DNS 无处可漏

*不绑定节点，不绑定订阅。只做一件事：消除 DNS 泄露面。*

[![Surge](https://img.shields.io/badge/Surge-iOS%20%7C%20macOS-1f6feb?style=flat-square)](https://github.com/RiverFlowsInUUU/surge-anti-dns-leak)
[![DNS](https://img.shields.io/badge/DNS-Zero%20Leak-2ea043?style=flat-square)](https://github.com/RiverFlowsInUUU/surge-anti-dns-leak)
[![Profiles](https://img.shields.io/badge/Profiles-lazy%20%7C%20routing-0969da?style=flat-square)](https://github.com/RiverFlowsInUUU/surge-anti-dns-leak)
[![Rules](https://img.shields.io/badge/Rules-12%20%7C%2015-8250df?style=flat-square)](https://github.com/RiverFlowsInUUU/surge-anti-dns-leak)
[![License](https://img.shields.io/badge/License-MIT-dfb317?style=flat-square)](docs/10-图标与许可.md)

[快速开始](#-快速开始) · [两份配置](#-两份配置) · [文件结构](#-文件结构) · [防泄露原理](#-防泄露原理) · [策略组结构](#-策略组结构) · [规则顺序](#-规则顺序) · [规则来源](#-规则来源) · [更多文档](#-更多文档)

</div>

<table align="center">
  <tr>
    <td align="center" width="33%">
      🔒<br><b>零明文 DNS</b><br><sub>引导 / 端点 / 劫持<br>三处收口，明文 :53 不出网</sub>
    </td>
    <td align="center" width="33%">
      🧩<br><b>不绑节点与订阅</b><br><sub>节点全为占位符<br>换节点不用改一行结构</sub>
    </td>
    <td align="center" width="33%">
      🧪<br><b>脚本可复跑</b><br><sub>12 项审计 + 分流覆盖<br>回归测试 15 条断言</sub>
    </td>
  </tr>
</table>

---

## 🚀 快速开始

```
1️⃣ 拿配置   →   profiles/lazy.conf
2️⃣ 填节点   →   [Proxy] 段的占位节点
3️⃣ 填充值   →   如有的话，改成你自己的
4️⃣ 导入     →   Surge
```

| 位置 | 现在是什么 | 填什么 | 必填 |
|:-----|:-----------|:-------|:----:|
| `[Proxy]` 的 4 条节点 | `203.0.113.x` + `REPLACE_WITH_*` | 你的节点信息 | ✅ |
| `[Proxy Group]` 的组成员 | `"Node-A"` … | 你的节点名 / 订阅组名 | ✅ |
| 测试端点（可选） | `internet-test-url` 国内 / `proxy-test-url` 境外 | 按你的取向换 | ⬜ 可选 |

填完节点即可导入，无需其他改动。

📄 **两份形态**：`lazy.conf`（带注释）与 `lazy.min.conf`（纯配置），内容一致，只差注释，取用其一即可。

---

## 🧭 两份配置

**不是版本关系，是分工关系。选一份用，不要叠加。**

| | 🪶 `lazy.conf` | 🧭 `routing.conf` |
|:--|:---------------|:------------------|
| 定位 | 懒人版 | 分流版 |
| 策略组 | 3 个 | 16 个 |
| 规则 | 12 条 | 15 条 |
| 出口粒度 | `Proxy` / `AI` / `AD`，全量一个出口 | 按**应用**分（ChatGPT / Claude / AI），组内再按**地区**分 |
| 适合 | 只想通、不想调 | 想让 ChatGPT 走美国、Claude 走台湾 |
| 导入 | `profiles/lazy.conf` | `profiles/routing.conf` |

两份都带：**防 DNS 泄露结构** + **广告拦截（含白名单守卫）** + **局域网共享**。
且 `[General]` 的 16 个 DNS 相关键**逐字相同** —— 防泄露标准不因分流粒度而变（由测试断言）。

```
1️⃣ 拿配置   →   profiles/lazy.conf  或  profiles/routing.conf
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

以 `lazy.conf` 为例：3 个组 / 12 条规则（`routing.conf` 是 16 组 / 15 条，见[两份配置](#-两份配置)）。组与组可以互相引用，最终都收敛到 `Proxy` 或 `DIRECT`。

**✈️ 节点** —— 4 条占位节点

- 🅰️ `Node-A` · `hysteria2` —— 落地节点（IP 字面量）
- 🅱️ `Node-B` · `hysteria2` —— 落地节点 ②，同时是中转链的 `underlying-proxy`
- 🅲 `Node-C` · `https` —— 中转链：经 `Node-B` 出去连 CDN 中转域名
- 🅳 `Node-D` · `https` —— 经 `Node-A` 中转

**🎛️ 三个策略组**

- 🧭 `Proxy` · `smart` —— 主入口，承载 `Node-A` / `Node-B`，按真实首字节延迟 + 重传 + UDP 响应评分
- 🤖 `AI` · `smart` —— AI 流量独立出口，承载 `Node-C` / `Node-D`，承接 `AI.list`
- 🛑 `AD` · `select` —— 独立手动开关（`REJECT` / `DIRECT`），不牵动规则引擎

> 📌 拦截动作走**字面量 `REJECT`**（为了拿到 `pre-matching` 的 DNS 阶段拦截能力），
> `AD` 组则作为**独立的手动干预入口**保留 —— 这是刻意的分层。说明见 [`DetailsReadme` §13.3](DetailsReadme/DetailsReadme.md#133-ad-组的定位独立的手动开关)。

---

## 📋 规则顺序

`[Rule]` 是**有序的** —— 自上而下匹配，**第一条命中即决定去向**，后面的不再看。

| 分类 | 规则 / 规则集 | 去向 |
|:-----|:--------------|:----:|
| 🛡️ ① 白名单守卫 | `jinx surge-white-guard.list`（43 条） | 直连 |
| 🚫 ② 广告拦截 | `jinx surge-ads.list`（3891 条）`pre-matching` | 拒绝 |
| 🤖 ③ AI 分流 | `AI.list`（49 条） | `AI` 组 |
| 🎮 ④ real-ip 主机名 | `nintendo.net` / `playstation.net` / `xboxlive.com` | 代理 |
| 🍎 ⑤ Apple 系统 | `SYSTEM`（内置） | 直连 |
| 🏠 ⑥ 内网直连 | `LAN` / `private.txt` | 直连 |
| 🇨🇳 ⑦ 国内直连 | `direct.txt`（11 万条域名） | 直连 |
| 🌏 ⑧ GeoIP CN | 中国 IP | 直连 |
| 🌐 ⑨ 兜底 | `default` | `Proxy` |

**铁律**：**白名单(DIRECT) → 黑名单(REJECT) → 常规分流（`direct.txt` / `GEOIP,CN`）**。REJECT 绝不能排在 `direct.txt` / `GEOIP,CN` 之后 —— 那等于白加。

> 📌 完整的 12 条逐条清单与「为什么 IP 类规则必须放最后」见 [`DetailsReadme` §1.4](DetailsReadme/DetailsReadme.md#14--rule12-条逐条)。

---

## 📚 规则来源

- 🛑 [RiverFlowsInUUU/jinx-ads-rules](https://github.com/RiverFlowsInUUU/jinx-ads-rules) —— 广告拦截 + 白名单守卫
- 🤖 [ACL4SSR/ACL4SSR](https://github.com/ACL4SSR/ACL4SSR) —— `AI.list`
- 🇨🇳 [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules) —— `direct.txt` / `private.txt`
- 🗺️ [adysec/IP_database](https://github.com/adysec/IP_database) —— `GeoLite2-Country.mmdb`

---

## 📖 更多文档

- ⚠️ [`docs/09-注意事项.md`](docs/09-注意事项.md) —— 使用前必看：规则集刷新 · 刻意不挂 CI
- 🎨 [`docs/10-图标与许可.md`](docs/10-图标与许可.md) —— 图标来源 · MIT 许可 · 第三方版权
- 🗓️ [`CHANGELOG.md`](CHANGELOG.md) —— 更新日志（按时间倒序，遵循 Keep a Changelog）
- 📘 [`DetailsReadme/`](DetailsReadme/) —— 逐段详解 · 原理推导 · 已知取舍 · FAQ
- 🧭 [`docs/11-分流版设计.md`](docs/11-分流版设计.md) —— 分流版：`flatten` 的对应写法 · Smart 组不能嵌套组 · 地区关键词双份
- 📂 [`docs/`](docs/) —— 其余 8 篇专题：DNS 怎么工作 / 为什么泄露 / 加固清单 / 逐段讲解 / 审计读数 …
- 🧪 [`skill/`](skill/) —— 3 个审计脚本、回归测试与方法论

---

<div align="center">

🛡️ 让 DNS 无处可漏 · MIT License · [图标与许可](docs/10-图标与许可.md)

</div>
