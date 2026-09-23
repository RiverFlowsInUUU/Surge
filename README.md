<div align="center">

# 🛡️ Surge 配置模板

*让 DNS 无处可漏*

[![Surge](https://img.shields.io/badge/Surge-iOS%20%7C%20macOS-1f6feb?style=flat-square)](https://github.com/RiverFlowsInUUU/Surge)
[![Profiles](https://img.shields.io/badge/Profiles-lazy%20%7C%20routing-0969da?style=flat-square)](https://github.com/RiverFlowsInUUU/Surge)
[![Rules](https://img.shields.io/badge/Rules-11%20%7C%2024-8250df?style=flat-square)](https://github.com/RiverFlowsInUUU/Surge)
[![DNS](https://img.shields.io/badge/DNS-Zero%20Leak-2ea043?style=flat-square)](https://github.com/RiverFlowsInUUU/Surge)
[![License](https://img.shields.io/badge/License-MIT-dfb317?style=flat-square)](docs/10-图标与许可.md)

</div>

## 📥 两全其美，皆合心意

🪶 **懒人版** · 至简 · 省心

```
https://raw.githubusercontent.com/RiverFlowsInUUU/Surge/main/profiles/lazy.min.conf
```

🧭 **分流版** · 可控 · 随心

```
https://raw.githubusercontent.com/RiverFlowsInUUU/Surge/main/profiles/routing_v3.min.conf
```

---

## 🧭 井然有序

两版的分组，自上而下：第一列为分流版的组（每项配图标），第二列懒人版有则 ✅、无则 `-`，第三列分流版全覆盖 ✅。

| 组 | 🪶 懒人版 | 🧭 分流版 |
|:---|:---:|:---:|
| 🚀 `Proxy` | ✅ | ✅ |
| ⚡ `Smart` | - | ✅ |
| 🤖 `ChatGPT` · `Gemini` · `Claude` · `AI` | ✅ | ✅ |
| 🎵 `Spotify` · 🎶 `YouTubeMusic` · ▶️ `YouTube` | - | ✅ |
| 🐙 `GitHub` · 🔎 `Google` · 🪟 `Microsoft` | - | ✅ |
| ✈️ `Telegram` · 🐦 `Twitter` · 💚 `WeChat` | - | ✅ |
| 🛑 `AD` | ✅ | ✅ |
| 🇭🇰 `Hong Kong` · 🇺🇸 `USA` · 🇯🇵 `Japan` · 🇨🇳 `Taiwan`<br>🇸🇬 `Singapore` · 🇰🇷 `Korea` · 🇦🇶 `Other Regions` | - | ✅ |
| 💧 `MAX` | - | ✅ |
| 🌐 `Final` | ✅ | ✅ |

> 🔍 选路、地区筛法与规则顺序见 [`docs/11`](docs/11-分流版设计.md)；带注释的原始文件见 [`profiles/`](profiles/)。

---

## 🌐 隐私至上 · 无 DNS 泄露

| | |
|:--|:--|
| 🚫 盲区设备 | 不识 DNS 的设备也被 `hijack-dns` 接管，明文 `:53` 无处可逃 |
| 🔐 加密通道 | 解析全程加密 DNS，不落入运营商 DHCP |
| 🧭 规则克制 | IP 规则一律 `no-resolve`，只为匹配、不额外发问 |
| 🔒 闭环连接 | `DoH` 直连、不跟代理链，启动不成环 |
| ✂️ 远端解析 | 代理域名交节点解析，本地不留答案 |
| 📋 自检读数 | 审计 **0 高危 / 0 中危**，路由 **33/33** |

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
