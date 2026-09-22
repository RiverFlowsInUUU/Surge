<div align="center">

# 🛡️ Surge 配置模板

**🪶 懒人版 · 🧭 分流版**

*不绑节点，不绑订阅 · 让 DNS 无处可漏*

[![Surge](https://img.shields.io/badge/Surge-iOS%20%7C%20macOS-1f6feb?style=flat-square)](https://github.com/RiverFlowsInUUU/surge)
[![Profiles](https://img.shields.io/badge/Profiles-lazy%20%7C%20routing-0969da?style=flat-square)](https://github.com/RiverFlowsInUUU/surge)
[![Rules](https://img.shields.io/badge/Rules-13%20%7C%2026-8250df?style=flat-square)](https://github.com/RiverFlowsInUUU/surge)
[![DNS](https://img.shields.io/badge/DNS-Zero%20Leak-2ea043?style=flat-square)](https://github.com/RiverFlowsInUUU/surge)
[![License](https://img.shields.io/badge/License-MIT-dfb317?style=flat-square)](docs/10-图标与许可.md)

</div>

## 📥 两份配置

🪶 **懒人版** · 一个出口

```
https://raw.githubusercontent.com/RiverFlowsInUUU/surge/main/profiles/lazy.min.conf
```

🧭 **分流版** · 按应用 + 按地区

```
https://raw.githubusercontent.com/RiverFlowsInUUU/surge/main/profiles/routing.min.conf
```

选中一条，点右上角复制 → Surge **配置 → 从 URL 下载** → 粘贴。

---

## 🪶 懒人版

`profiles/lazy.conf` · `profiles/lazy.min.conf`

3 组 / 13 条规则。全部流量走一个出口。

| | |
|:--|:--|
| ✈️ 节点 | `Node-A` ~ `Node-D`，4 条占位 |
| 🧭 `Proxy` | 主出口，按首字节延迟 + 重传评分选点 |
| 🤖 `AI` | AI 流量独立出口 |
| 🛑 `AD` | 手动开关（`REJECT` / `DIRECT`） |

---

## 🧭 分流版

`profiles/routing.conf` · `profiles/routing.min.conf`

26 组 / 26 条规则。先按应用分，再按地区分。组序与 egern v2.5 对齐。

| 层 | 组 | 选路 |
|:---|:---|:---|
| 🎯 总入口 | `Proxy` · `Smart` | `Proxy` 手动（首项 `MAX`）· `Smart` 自动 |
| 🧩 应用 | 12 组（见下） | 手动，默认走 `Proxy` 全部节点 |
| 📡 订阅 | `Airport` | 订阅槽位（隐藏） |
| 🛑 开关 | `WeChat` · `AD` | 手动 |
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

## 📋 规则顺序

自上而下匹配，第一条命中即决定去向。

| # | 规则 | 🪶 懒人版 | 🧭 分流版 |
|:-:|:-----|:----------|:----------|
| 🛡️ | 白名单守卫 | `surge-white-guard.list` → `DIRECT` | 同左 |
| 🚫 | 广告拦截 | `surge-ads.list` → `REJECT` | 同左 |
| 🤖 | 按应用 | `AI.list` → `AI` | 13 条，见下 |
| 🎮 | 游戏机主机名 | `nintendo.net` · `playstation.net` · `xboxlive.com` → `Proxy` | 同左 |
| 🍎 | Apple 服务 | `SYSTEM` + `Apple_All_No_Resolve.list` → `DIRECT` | 同左 |
| 🏠 | 内网 | `LAN` · `private.txt` → `DIRECT` | 同左 |
| 🇨🇳 | 国内域名 | `direct.txt` → `DIRECT` | 同左 |
| 🌏 | 国内 IP | `GEOIP,CN` → `DIRECT` | 同左 |
| 🌐 | 兜底 | `Proxy` | `Final` |

**分流版的应用规则**

| 规则集 | 去向 |
|:-------|:-----|
| `OpenAI.list` | `ChatGPT` |
| `Gemini.list` | `Gemini` |
| `Anthropic.list` · `Claude.list` | `Claude` |
| `AI.list` | `AI` |
| `Spotify.list` | `Spotify` |
| `YouTubeMusic.list` | `YouTubeMusic` |
| `YouTube.list` | `YouTube` |
| `Telegram.list` | `Telegram` |
| `Twitter.list` | `Twitter` |
| `GitHub.list` | `GitHub` |
| `Google.list` | `Google` |
| `Microsoft.list` | `Microsoft` |
| `WeChat.list` | `WeChat` |

**三条排序约束**

1. 厂商专属规则排在 `AI.list` 之前，否则 AI 域名先被 `AI.list` 接走。
2. `GitHub.list` 排在 `direct.txt` 之前 —— `github.com` 同时在国内直连清单里。
3. IP 类规则（`GEOIP,CN`）排最后，全部带 `no-resolve`。

---

## 🌐 防泄露原理

明文 `UDP:53` 只有三条出口。

| 出口 | 机制 | 堵法 |
|:----:|:-----|:-----|
| 🚪 引导解析 | DNS 端点写成主机名时，必须先明文解析一次 | 端点写 IP 字面量 |
| 🚪 旁路设备 | 忽略 Surge DNS 的设备直接发明文 `:53` | `hijack-dns` 接管 |
| 🚪 规则触发解析 | 不带 `no-resolve` 的 IP 规则会主动发起解析 | IP 类规则一律带 `no-resolve` |

---

## 📁 文件结构

```
surge/
├── 📁 profiles/        # 4 份配置：懒人版 / 分流版 × 带注释 / 纯配置
├── 🖼️ icons/           # 策略组图标
├── 📚 docs/            # 11 篇专题
├── 📘 DetailsReadme/   # 完整技术文档
├── 🗓️ CHANGELOG.md
└── 🧪 skill/           # 审计脚本 + 回归测试
```

---

## 📚 规则来源

- 🛑 [jinx-ads-rules](https://github.com/RiverFlowsInUUU/jinx-ads-rules) —— 广告拦截 · 白名单守卫
- 🧩 [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) —— 应用规则集
- 🤖 [ACL4SSR/ACL4SSR](https://github.com/ACL4SSR/ACL4SSR) —— `AI.list`
- 🇨🇳 [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules) —— `direct.txt` · `private.txt`
- 🗺️ [adysec/IP_database](https://github.com/adysec/IP_database) —— `GeoLite2-Country.mmdb`

---

## 📖 更多文档

- 📘 [`DetailsReadme/`](DetailsReadme/) —— 逐段详解 · 原理推导 · 已知取舍 · FAQ
- 🧭 [`docs/11`](docs/11-分流版设计.md) —— 分流版设计
- ⚠️ [`docs/09`](docs/09-注意事项.md) —— 注意事项
- 🎨 [`docs/10`](docs/10-图标与许可.md) —— 图标与许可
- 📂 [`docs/`](docs/) —— 全部 11 篇
- 🗓️ [`CHANGELOG.md`](CHANGELOG.md)

---

<div align="center">

MIT License · [图标与许可](docs/10-图标与许可.md)

</div>
