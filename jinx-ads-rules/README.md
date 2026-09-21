<div align="center">

# 🛑 Jinx 去广告规则 · 转换版

### 让 iOS 拦得住的广告，在 mihomo / Surge 上也拦得住

*不是原创规则 —— 上游 Jinx 黑/白名单的语法翻译件，不增删一条规则内容。*

[![Source](https://img.shields.io/badge/Source-Jinx%203.1.9-8250df?style=flat-square)](https://github.com/VME98/jinx-rules)
[![mihomo](https://img.shields.io/badge/mihomo-OpenClash-1f6feb?style=flat-square)](https://github.com/RiverFlowsInUUU/jinx-ads-rules)
[![Surge](https://img.shields.io/badge/Surge-RULE--SET-orange?style=flat-square)](https://github.com/RiverFlowsInUUU/jinx-ads-rules)
[![Rules](https://img.shields.io/badge/Ads-3891%20%7C%203838-0969da?style=flat-square)](https://github.com/RiverFlowsInUUU/jinx-ads-rules)
[![License](https://img.shields.io/badge/License-未声明-critical?style=flat-square)](#-许可与免责)

[先读来源](#-先读来源与许可) · [快速开始](#-快速开始) · [文件结构](#-文件结构) · [该选哪个](#-该选哪个文件) · [mihomo](#-mihomo--openclash-配置) · [Surge](#-surge-配置) · [规则顺序](#-规则顺序) · [转换原理](#-转换原理) · [重新生成](#-重新生成) · [已知坑](#-已知坑) · [许可](#-许可与免责)

</div>

<table align="center">
  <tr>
    <td align="center" width="33%">
      🛑<br><b>语义保真</b><br><sub>黑名单按「域 + 全部子域」复刻<br>149 条中缀通配逐平台对译</sub>
    </td>
    <td align="center" width="33%">
      📦<br><b>两平台各三份</b><br><sub>完整版 / 差集版 / 白名单守卫<br>mihomo 与 Surge 内容一一对应</sub>
    </td>
    <td align="center" width="33%">
      🧪<br><b>脚本可复现</b><br><sub>6 个文件全部由脚本产出<br>重跑逐字节一致</sub>
    </td>
  </tr>
</table>

---

## ⚠️ 先读：来源与许可

| 项 | 说明 |
|:---|:-----|
| 上游 | [`VME98/jinx-rules`](https://github.com/VME98/jinx-rules) · 数据 `3.1.9` · `2026-09-15` |
| 上游许可 | **`license: null`** —— 未声明任何 License |
| 本仓库 | **同样不主张任何许可**。这是对公开数据的格式翻译，不是我的作品 |
| 下架承诺 | 上游作者若认为不妥，开 issue 或联系我，**立刻删除本仓库** |

> 📌 建议直接引用**上游原始地址**；本仓库只是替你省掉「转换」这一步。
>
> 🩹 **v2 修正（2026-09-19）**：v1 把普通域名错转成 `DOMAIN`（精确匹配），但 Jinx 实际是**后缀匹配** —— 列表里写 `bugly.qq.com`，它连 `ios.bugly.qq.com` 一起拦。改回 `DOMAIN-SUFFIX` 后，同一份日志 30 条被拦域名的覆盖率 **93% → 100%**。早期 `*-domain.list` / `*-domainset.txt` 变体已全部删除。

---

## 🚀 快速开始

```
1️⃣ 选文件   →   mihomo-ads.list（mihomo）/ surge-ads.list（Surge）
2️⃣ 接规则   →   白名单 → REJECT → 你原有的规则
3️⃣ 验顺序   →   面板看到 jinx-ads 命中 = 生效
```

| 客户端 | 黑名单 | 白名单 |
|:-------|:-------|:-------|
| mihomo / OpenClash / Stash | `mihomo-ads.list` | `mihomo-white-guard.list` |
| Surge | `surge-ads.list` | `surge-white-guard.list` |

> 💡 顺序是**生死线**。REJECT 排在 `GEOSITE,cn,DIRECT` 之后 = 白接，见 [§规则顺序](#-规则顺序)。

---

## 📁 文件结构

```
jinx-ads-rules/
├── mihomo-ads.list             # 黑名单 完整版 3891 条 ⭐
├── mihomo-ads-delta.list       # 黑名单 差集版 3838 条
├── mihomo-white-guard.list     # 白名单守卫 43 条 ⭐
├── surge-ads.list              # 黑名单 完整版 3891 条 ⭐
├── surge-ads-delta.list        # 黑名单 差集版 3838 条
├── surge-white-guard.list      # 白名单守卫 43 条 ⭐
├── custom-ads.list             # 自定义追加源（3 条）— 只供 --extra 合并
├── custom-direct.list          # 自定义直连源（1 条）— 只供 --extra-white 合并
└── skill/                      # 转换脚本 + 方法论
    ├── SKILL.md
    └── scripts/
        ├── convert_ruleset.py      # 6 个规则文件全部由它产出
        ├── upload_repo.py
        └── upload_to_github.py
```

**两个地址前缀，二选一**，拼上文件名即完整地址：

| 源 | 前缀 |
|:---|:-----|
| **jsDelivr（推荐）** | `https://cdn.jsdelivr.net/gh/RiverFlowsInUUU/jinx-ads-rules@main/` |
| GitHub raw（备选） | `https://raw.githubusercontent.com/RiverFlowsInUUU/jinx-ads-rules/main/` |

优先 jsDelivr —— `raw.githubusercontent.com` 在国内常不可达。急用可在 URL 后加 `?v=<日期>` 绕开 CDN 缓存。

---

## 🎯 该选哪个文件

判据只有一条：**你的客户端里有没有同时跑 `AWAvenue-Ads-Rule`？**

| 情况 | mihomo | Surge |
|:-----|:-------|:------|
| **没有 / 不确定** | **`mihomo-ads.list`** ⭐ | **`surge-ads.list`** ⭐ |
| 有 AWAvenue | `mihomo-ads-delta.list` | `surge-ads-delta.list` |

- 📉 差集只少 **53 条**（3838 vs 3891），体积差异可忽略。**除非确定 AWAvenue 在跑，否则直接用完整版** —— 省得为 53 条埋一个「以为有人管、其实没人管」的坑。
- 🛡️ **白名单（43 条）强烈建议加**。上游 325 条白名单里只有 42 条真会被这套黑名单误杀，其余是给别的规则集准备的（含 `github.com`、`jsdelivr.net`、`icloud.com`，放在 REJECT 前会强制直连，国内属负优化）。**只要这 42 条。**
- ⚠️ `custom-ads.list` / `custom-direct.list` 是**源文件不是规则集**，不要直接引用。

---

## 🔷 mihomo / OpenClash 配置

> **适用**：mihomo、OpenClash、Stash、FlClash

```yaml
rule-providers:
  jinx-ads:
    type: http
    behavior: classical          # ⚠️ 必须 classical，不要用 domain
    format: text
    url: "https://cdn.jsdelivr.net/gh/RiverFlowsInUUU/jinx-ads-rules@main/mihomo-ads.list"
    path: ./rule_provider/jinx-ads.list
    interval: 86400

  jinx-white-guard:
    type: http
    behavior: classical
    format: text
    url: "https://cdn.jsdelivr.net/gh/RiverFlowsInUUU/jinx-ads-rules@main/mihomo-white-guard.list"
    path: ./rule_provider/jinx-white-guard.list
    interval: 86400

rules:
  - RULE-SET,jinx-white-guard,DIRECT   # ① 白名单必须在 REJECT 之前
  - RULE-SET,jinx-ads,REJECT           # ② 广告拦截
  # - GEOSITE,cn,DIRECT ...            # ③ 你原有的规则接在后面
```

> `behavior: domain` 不要用：它对普通域名的匹配范围取决于实现，而 `classical` + 显式 `DOMAIN-SUFFIX` 语义明确、可控。
>
> 🚨 **OpenClash 用户先读下一节** —— 一个默认开关能让整套规则**静默失效**。

### 🚨 OpenClash：一个开关让规则「静默失效」

**症状**：规则接好了，日志里也看得到 `match RuleSet(jinx-ads) using REJECT`，但**部分广告照旧**；更诡异的是漏掉的那些域名，日志里**一条记录都没有**。

**根因：`绕过中国大陆 IP`（`china_ip_route`，默认常开）**。它在生成运行配置时静默把「中国大陆域名集」塞进 `fake-ip-filter`（`/usr/share/openclash/yml_change.sh`）：

```
域名命中 oc-cn-domain → DNS 返回真实 IP（不是 198.18.x.x）
      ↓
防火墙「目标 IP 属大陆 → return」→ 连接根本没进内核
      ↓
规则引擎没有机会执行 → 广告照常（且无日志）
```

**为什么中招的偏偏是广告**：大量国内 App 的广告 / 埋点 SDK 挂在国内大厂域名下（`*.volces.com`、`*.bytedns.com`），天然落进「中国大陆域名集」。

**两条判据（任一条成立即中招）**

| 判据 | 操作 | 判读 |
|:-----|:-----|:-----|
| ① 日志为空 | `grep '<域名>' /tmp/openclash.log` | 0 条 → 压根没进内核 |
| ② DNS 应答 | `tcpdump -i br-lan -n -vv 'udp port 53'` | 同设备既有真实 IP 又有 `198.18.x.x` → 石锤 |

**解法**

```bash
uci set openclash.config.china_ip_route='0'
uci commit openclash
/etc/init.d/openclash restart
```

关掉后所有域名都走 fake-ip、连接全部进内核 → 域名规则 100% 有机会执行。

- ✅ 保留项：`fake-ip-filter` 里 NTP / STUN / 局域网等硬编码条目不受影响
- ⚖️ 副作用：域名访问多一跳内核；**纯 IP 直连不受影响**
- ↩️ 回滚：`uci set openclash.config.china_ip_route='1'` + commit + restart

**验收三步**：① DNS 变了 —— 同一域名从真实 IP 变成 `198.18.x.x`；② 请求被拒 —— 直接请求该域名，连接 / TLS 握手失败；③ 日志有了 —— `/tmp/openclash.log` 出现 `match RuleSet(jinx-ads) … REJECT`。

---

## 🔶 Surge 配置

```
[Rule]
# ① 白名单（精确放行）
RULE-SET,https://cdn.jsdelivr.net/gh/RiverFlowsInUUU/jinx-ads-rules@main/surge-white-guard.list,DIRECT
# ② 广告拦截
RULE-SET,https://cdn.jsdelivr.net/gh/RiverFlowsInUUU/jinx-ads-rules@main/surge-ads.list,REJECT,pre-matching,extended-matching
# ③ 你自己的规则接在后面
```

| 参数 | 作用 |
|:-----|:-----|
| `pre-matching` | REJECT 提前到 DNS / 连接建立阶段生效，最接近 Jinx 的系统级拦截体验 |
| `extended-matching` | 额外按 TLS SNI / HTTP Host 匹配，专治「App 直连 IP 导致域名规则失效」 |

> ⚠️ `pre-matching` **只能跟 REJECT 系策略用**，`DIRECT` 加它无效（Surge 官方明确）—— 白名单那行不要写。

---

## 📋 规则顺序

规则引擎**自上而下、先匹配先赢**。你机器上 99% 的国内广告域名，同时也属于「中国大陆域名」。

```
❌ 顺序错                              ✅ 顺序对
GEOSITE,cn,DIRECT      ← 先命中放行    RULE-SET,jinx-white-guard,DIRECT
RULE-SET,jinx-ads,REJECT ← 轮不到      RULE-SET,jinx-ads,REJECT
                                       GEOSITE,cn,DIRECT
```

**铁律**：白名单（DIRECT）→ 黑名单（REJECT）→ 常规分流（`GEOSITE,cn` / `GEOIP,cn`）。

**土办法验证**：开一个本来有广告的 App，看面板的规则命中 —— 看到 `jinx-ads` 命中即顺序对；只看到 `cn` / `DIRECT` / `Final`，就把 REJECT 提到前面。

---

## 🔄 转换原理

上游 `rules/version.json`：

```json
{ "version": "3.1.9",
  "lastUpdate": "2026-09-15T14:35:01Z",
  "domainBlacklistCount": 3888,
  "domainWhitelistCount": 325,
  "urlBlacklistCount": 890,
  "urlWhitelistCount": 21,
  "mitmSkipDomainsCount": 33 }
```

语法映射：

| 上游写法 | 含义 | mihomo | Surge |
|:---------|:-----|:-------|:------|
| `bugly.qq.com` | 该域 + **全部子域** | `DOMAIN-SUFFIX,bugly.qq.com` | `DOMAIN-SUFFIX,bugly.qq.com` |
| `*.cupid.iqiyi.com` | 同上（等价） | `DOMAIN-SUFFIX,cupid.iqiyi.com` | `DOMAIN-SUFFIX,cupid.iqiyi.com` |
| `p*-ad.adkwai.com` | 中缀通配（单级） | `DOMAIN-REGEX,^p.*\-ad\.adkwai\.com$` | `DOMAIN-WILDCARD,p*-ad.adkwai.com` |
| 白名单 `qq.com` | **仅精确**，不继承子域 | `DOMAIN,qq.com` | `DOMAIN,qq.com` |

**两平台的唯一差异**：149 条中缀通配 —— mihomo 不支持星号内嵌，用 `DOMAIN-REGEX`；Surge 用 `DOMAIN-WILDCARD`。其余条目完全一致。

- 🔍 **后缀语义依据**：日志中 `sdkquic.e.qq.com` 被拦而列表只有 `e.qq.com`；`ios.bugly.qq.com` 被拦而列表只有 `bugly.qq.com`。
- 🔍 **白名单精确依据**：白名单含 `qq.com`，但 `sdk.e.qq.com`、`c3.gdt.qq.com`、`ios.bugly.qq.com` 均被正常拦截。
- 🚫 **未转换**：`url_blacklist*`、`url_whitelist*`、`mitm_skip_domains.txt`、`url_response_policies.json` 依赖 MITM 上下文，域名规则无法表达。

---

## 🛠️ 重新生成

规则不是手工维护的死快照 —— 产出它们的脚本与方法论一并放在 `skill/`：

| 路径 | 内容 |
|:-----|:-----|
| `skill/SKILL.md` | 完整方法论：匹配语义判定、三平台通配映射、差集逻辑、白名单瘦身、踩坑记录 |
| `skill/scripts/convert_ruleset.py` | 转换主脚本（6 个规则文件全部由它产出） |
| `skill/scripts/upload_to_github.py` | 批量上传辅助脚本（纯 GitHub API，无需 git / gh CLI） |

**① 取源文件**

```bash
mkdir -p jinx-rules && cd jinx-rules
for f in blacklist.txt blacklist_wildcard.txt whitelist.txt whitelist_wildcard.txt version.json; do
  curl -fsSLO "https://raw.githubusercontent.com/VME98/jinx-rules/master/rules/$f"
done
cd ..
```

**② 生成（三条命令产出全部 6 个文件）**

```bash
SK=skill/scripts/convert_ruleset.py

# 黑名单 完整版（suffix 语义）
python $SK --src ./jinx-rules --out ./out --fixed blacklist.txt --wild blacklist_wildcard.txt \
    --tag ads --mode suffix --naming repo --extra ./custom-ads.list

# 黑名单 差集版（剔除 AWAvenue 已深度覆盖的条目）
python $SK --src ./jinx-rules --out ./out --fixed blacklist.txt --wild blacklist_wildcard.txt \
    --tag ads-delta --mode suffix --naming repo --extra ./custom-ads.list \
    --delta-ref https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/Filters/AWAvenue-Ads-Rule-Clash-Classical.yaml

# 白名单 精简守卫（exact 语义）
python $SK --src ./jinx-rules --out ./out --fixed whitelist.txt --wild whitelist_wildcard.txt \
    --tag white-guard --mode exact --naming repo \
    --guard-against-fixed blacklist.txt --guard-against-wild blacklist_wildcard.txt \
    --extra-white ./custom-direct.list
```

> ✅ **已实测**：从上游 `3.1.9` 重跑，产出的 6 个文件与仓库现有文件**逐字节一致**（剔除注释后 `diff` 为空）。

### ✍️ 两个人工维护入口

`custom-ads.list`（3 条）与 `custom-direct.list`（1 条）是**唯一需要人手改的文件**，重跑时由脚本自动合并。

| 文件 | 参数 | 语义 | 合并时机 |
|:-----|:-----|:-----|:---------|
| `custom-ads.list` | `--extra` | `DOMAIN-SUFFIX` | 条目池之后、差集之前 → 与上游条目同等对待 |
| `custom-direct.list` | `--extra-white` | 强制 `DOMAIN-SUFFIX` | guard 过滤之后 → 不参与裁剪，永远存活 |

两者都追加在输出**末尾**、表头多一行 `# extra:`，便于 diff 核验。

- ⚠️ **不要手改 `mihomo-*.list` / `surge-*.list`** —— 它们是生成产物，重跑一次即被完全覆盖。

当前内容：

- 🎯 `msg.qy.net` —— 爱奇艺视频广告素材出口（CNAME → `msg.video.dns.iqiyi.com`）；收录于 anti-AD、1Hosts Lite
- 🎯 `rmonitor.qq.com` —— 腾讯广告监控上报；收录于 anti-AD、1Hosts Lite
- 🎯 `rdelivery.qq.com` —— 腾讯广告配置拉取（响应头 `trpc.rdelivery.config_pull_server`）；收录于 1Hosts Lite
- 🟢 `*.tange365.com` —— 相机 App「小鲸看看」自身业务域（账户 / 设备 / 云存储），必须直连

> 📌 前三条来自一次真实漏拦定位：该 App 冷启动时 `t7z.cupid.iqiyi.com`（爱奇艺广告 SDK）被拦，**75 ms 后** `msg.qy.net` 放行 —— 广告位能渲染，素材必然来自某个没被拦的域名。

---

## ⚠️ 已知坑

- 🥇 **顺序** —— 白名单 → REJECT → `GEOSITE,cn`。「规则看着配了、广告还在」的头号原因
- 🪃 **OpenClash 前置开关** —— 开着「绕过中国大陆 IP」时规则对相当一部分域名完全不生效，且日志看不出异常
- 🌐 **超广通配** —— 源里有 `ad.*`、`ads-*`、`pangolin*` 这类一条覆盖几百条的规则，某 App 出问题先怀疑它们
- ✳️ **中缀星号** —— 只存在于 `classical` / `RULE-SET` 格式，这也是本仓库只提供这两种格式的原因
- 🕐 **jsDelivr 缓存** —— 更新后几分钟到几小时延迟，急用加 `?v=<日期>`
- 🔗 **地址二选一** —— 优先 jsDelivr；只在拉不动或需「改动立刻生效」时才换 raw
- 🧱 **只做域名级拦截** —— 同域内嵌广告（广告与内容同一域名）需 MITM / URL 级规则，本仓库做不到
- 🎯 **`DOMAIN-SUFFIX` 覆盖面大** —— 为复刻 Jinx 行为；误杀就用白名单加回，别把语义改回精确

---

## 📄 许可与免责

- 规则数据版权归上游 `VME98/jinx-rules` 及其原始来源。本仓库**不主张任何权利**、不声明 License。
- 🔧 **数据与工具分开看**：`skill/` 下的脚本与方法论是本仓库自带工具，**不含任何上游数据**，可自由取用、修改、再分发；「不主张许可」只针对根目录的规则数据。
- `DOMAIN-SUFFIX` 会拦截整个子域树，请自行评估对自有服务的影响，必要时用白名单放行。
- 本仓库仅提供格式转换结果，**不对拦截效果与误杀后果作任何保证**。
- 若上游作者或任何权利人要求，本仓库将立即删除。

---

<div align="center">

🛑 数据来自 VME98/jinx-rules · 本仓库不主张任何许可 · [回到顶部](#-jinx-去广告规则--转换版)

</div>
