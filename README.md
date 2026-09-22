<div align="center">

# 🛡️ Surge 配置模板

**🪶 懒人版 · 🧭 分流版**

*不绑节点，不绑订阅 · 让 DNS 无处可漏*

[![Surge](https://img.shields.io/badge/Surge-iOS%20%7C%20macOS-1f6feb?style=flat-square)](https://github.com/RiverFlowsInUUU/Surge)
[![Profiles](https://img.shields.io/badge/Profiles-lazy%20%7C%20routing-0969da?style=flat-square)](https://github.com/RiverFlowsInUUU/Surge)
[![Rules](https://img.shields.io/badge/Rules-13%20%7C%2026-8250df?style=flat-square)](https://github.com/RiverFlowsInUUU/Surge)
[![DNS](https://img.shields.io/badge/DNS-Zero%20Leak-2ea043?style=flat-square)](https://github.com/RiverFlowsInUUU/Surge)
[![License](https://img.shields.io/badge/License-MIT-dfb317?style=flat-square)](docs/10-图标与许可.md)

</div>

## 📥 两份配置

🪶 **懒人版** · 一个出口

```
https://raw.githubusercontent.com/RiverFlowsInUUU/Surge/main/profiles/lazy.min.conf
```

🧭 **分流版** · 按应用 + 按地区

```
https://raw.githubusercontent.com/RiverFlowsInUUU/Surge/main/profiles/routing.min.conf
```

选中一条，点右上角复制 → Surge **配置 → 从 URL 下载** → 粘贴。

---

## 🪶 懒人版

`profiles/lazy.conf` · `profiles/lazy.min.conf`

3 组 / 14 条规则。全部流量走一个出口。

| | |
|:--|:--|
| ✈️ 节点 | `Node-A` ~ `Node-D`，4 条占位 |
| 🧭 `Proxy` | 主出口，按首字节延迟 + 重传评分选点 |
| 🤖 `AI` | AI 流量独立出口 |
| 🛑 `AD` | 手动开关（`REJECT` / `DIRECT`） |

---

## 🧭 分流版

`profiles/routing.conf` · `profiles/routing.min.conf`

26 组 / 27 条规则。先按应用分，再按地区分。

| 层 | 组 | 选路 |
|:---|:---|:---|
| 🎯 总入口 | `Proxy` · `Smart` | `Proxy` 手动（首项 `MAX`）· `Smart` 自动 |
| 🧩 应用 | 13 组（见下） | 手动；多数默认走 `Proxy`，`Microsoft` · `WeChat` 首项 `DIRECT` |
| 📡 订阅 | `Airport` | 订阅槽位（隐藏） |
| 🛑 开关 | `AD` | 手动，独立于规则链路 |
| 🌏 地区 | `Hong Kong` · `USA` · `Japan` · `Taiwan` · `Singapore` · `Korea` · `Other Regions` | 自动，按节点名正则筛 |
| 💎 精选 | `MAX` | 自动，低倍率节点 |
| 🌐 兜底 | `Final` | 手动（默认 `Proxy`） |

**应用组的默认出口**

每组都是 `select, include-other-group="Proxy"` —— 默认走 `Proxy` 的全部节点，面板上可随时改道。

| 应用 | 默认 | 备注 |
|:-----|:-----|:-----|
| 🤖 `ChatGPT` · `Gemini` · `AI` | `Proxy` | |
| 🎭 `Claude` | 中国台湾 | 首项 `Taiwan` |
| 🔎 `Google` | `Gemini` → `Proxy` | 首项 `Gemini` |
| 🎵 `Spotify` · 🎶 `YouTubeMusic` · ▶️ `YouTube` | `Proxy` | |
| ✈️ `Telegram` · 🐦 `Twitter` | `Proxy` | |
| 🐙 `GitHub` | `Proxy` | |
| 🪟 `Microsoft` | `DIRECT` | 首项 `DIRECT` |
| 💚 `WeChat` | `DIRECT` | 首项 `DIRECT`，把微信从兜底里摘出来 |
| 🌐 `Final` | `Proxy` | 兜底，可改道 |

---

## 📋 分流顺序

自上而下匹配，第一条命中即决定去向。

| # | 匹配什么 | 🪶 懒人版 | 🧭 分流版 |
|:-:|:-----|:----------|:----------|
| 🛡️ | 白名单域名 | 直连 | 同左 |
| 🚫 | 广告域名 | 拦截 | 同左 |
| 🤖 | 按应用 | AI 服务 → `AI` | 13 类应用各自成组 |
| 🎮 | 游戏机主机名 | `Proxy` | 同左 |
| 🍎 | Apple 服务 | 直连 | 同左 |
| 🏠 | 内网 | 直连 | 同左 |
| 🇨🇳 | 国内域名 | 直连 | 同左 |
| 🌏 | 国内 IP | 直连 | 同左 |
| 🌐 | 其余全部 | `Proxy` | `Final` |

> 🚫 **广告拦截由两条并列清单承担**，同策略、同参数。
> ⚠️ **白名单必须排在这两条之前**，顺序不可调整。

---

## 🌐 DNS 防泄漏

| | |
|:--|:--|
| 🚫 设备硬编码的明文 `:53` | `hijack-dns` 接管 —— HomePod / Apple TV / 智能音箱这类无视 DNS 设置的设备 |
| 🔐 解析通道 | 加密 DNS 全程接管；引导解析器显式写死，不落到运营商 DHCP |
| 🧭 规则匹配 | IP 类规则全部 `no-resolve`，不为匹配额外发起解析 |
| 🔒 DoH 连接 | 固定直连、不跟随代理链，启动期不成环 |
| ✂️ 远端解析 | 走代理的域名由节点侧解析，本地不留答案 |
| 📋 审计读数 | 自带审计脚本 **0 high / 0 medium** · 路由覆盖 **33/33** |

---

## 📁 文件结构

| | 路径 | 内容 |
|:--:|:-----|:-----|
| 📁 | [`profiles/`](profiles/) | 4 份配置：懒人版 / 分流版 × 带注释 / 纯配置 |
| 🖼️ | [`icons/`](icons/) | 策略组图标 |
| 📚 | [`docs/`](docs/) | 12 篇专题 |
| 📘 | [`DetailsReadme/`](DetailsReadme/DetailsReadme.md) | 完整技术文档 |
| 🗓️ | [`CHANGELOG.md`](CHANGELOG.md) | 版本记录 |
| 🧪 | [`skill/`](skill/) | 审计脚本 + 回归测试 |

---

## 📖 更多文档

- 📘 [`DetailsReadme/`](DetailsReadme/) —— 逐段详解 · 原理推导 · 已知取舍 · FAQ
- 🧭 [`docs/11`](docs/11-分流版设计.md) —— 分流版设计
- 📚 [`docs/12`](docs/12-规则集与来源.md) —— 规则集与来源
- ⚠️ [`docs/09`](docs/09-注意事项.md) —— 注意事项
- 🎨 [`docs/10`](docs/10-图标与许可.md) —— 图标与许可
- 📂 [`docs/`](docs/) —— 全部 12 篇
- 🗓️ [`CHANGELOG.md`](CHANGELOG.md)

---

<div align="center">

MIT License · [图标与许可](docs/10-图标与许可.md)

</div>
