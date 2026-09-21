# 核对器 · 命令与判据

> **何时读**：跑审计脚本前（环境要求 / 命令）、或**要改判据时**（判据演进史）。
>
> 逐条事故复盘见 [`pitfalls.md`](pitfalls.md)。

---

## 1 · 环境要求

| 项 | 要求 |
|:---|:-----|
| Python | 3.8+，**仅标准库** |
| 网络 | `check_surge_dns.py` / `architecture.sh` **不需要**；另两个脚本需要 |
| 操作系统 | Windows（Git Bash）/ macOS / Linux 均可 |
| 磁盘 | 规则集缓存约 10 MB（`direct.txt` 一份 11 万条） |

⚠️ **Windows / Git Bash 的路径坑**：`pwd` 返回 `/c/Users/...`，
Windows 版 Python 打不开（报 `can't open file 'C:\c\Users\...'`）。
两个 `.sh` 脚本里都做了处理：

```bash
if command -v cygpath >/dev/null 2>&1; then
  PROFILES_W="$(cygpath -w "$PROFILES")"
else
  PROFILES_W="$PROFILES"
fi
```

⚠️ 拼接路径**一律用 `/`**，不要用 `\\` —— `cygpath -w` 给的是 `C:\Users\...`（反斜杠），
再拼 `\\check.py` 在 Linux 上会把反斜杠变成文件名的一部分 ⇒ file not found。

---

## 2 · 命令

```bash
S=./skill/scripts

# ── 不联网 ──────────────────────────────────────────────────────────
python "$S/check_surge_dns.py"  profiles/v1.conf              # 期望 exit 0
python "$S/check_surge_dns.py"  profiles/v1.conf --strict      # medium 也算失败
python "$S/check_surge_dns.py"  profiles/v1.conf --quiet       # 只打印计数
bash   ./skill/tests/architecture.sh                           # 期望 exit 0

# ── 需要联网 ────────────────────────────────────────────────────────
python "$S/audit_ruleset_content.py"  profiles/v1.conf         # 期望 exit 0
python "$S/audit_ruleset_content.py"  profiles/v1.conf --show-domestic --force
python "$S/audit_routing_coverage.py" profiles/v1.conf         # 期望 33/33
python "$S/audit_routing_coverage.py" profiles/v1.conf --show-all

# ── 回归测试（5 阶段，13 断言）─────────────────────────────────────
bash ./skill/tests/run.sh
SKIP_NET=1 bash ./skill/tests/run.sh
PY=/path/to/python bash ./skill/tests/run.sh
```

规则集缓存目录：

- Windows：`%TEMP%\surge-ruleset-cache`
- macOS / Linux：`/tmp/surge-ruleset-cache`

用 `--cache-dir` 指定别处；用 `--force` 忽略缓存重下。

---

## 3 · 退出码约定

| 码 | 含义 |
|:--:|:-----|
| 0 | 通过 |
| 1 | 有发现（审计器）/ 有断言失败（测试） |
| 2 | **环境故障**：解释器不可用 / 文件缺失 / 用法错误 |

⭐ **退出码 2 是必须的。**

`run.sh` 的 `bad_*` fixture **期望退出码 1**。如果解释器坏掉，脚本也返回 1
—— 会被误判成"判负通过"。前置检查把这个歧义消掉：

```bash
if ! "$PY" -c "import sys" >/dev/null 2>&1; then
  printf '\n❌ 前置检查失败：解释器不可用。PY=%s\n' "$PY" >&2
  exit 2
fi
```

> **铁律：审计器的故障绝不能被计成一次成功的判负。**

---

## 4 · 12 项判据（`check_surge_dns.py`）

| # | 检查 | 判负级别 | 判据细节 |
|:-:|:-----|:--------:|:---------|
| 1 | 加密 DNS 端点是 IP 字面量 | **HIGH** / MEDIUM / OK | 每个端点过 `ip_literal()`；非字面量的逐个列出。另有 MEDIUM：端点在国外（国内线路通常不可达，属取舍） |
| 2 | `dns-server` | **HIGH** / MEDIUM / OK | 缺失 → HIGH；含 `system` → **HIGH**；含主机名 → **HIGH**；国内解析器 < 2 → MEDIUM；否则 OK |
| 3 | `hijack-dns` | LOW / OK | 缺失 → **HIGH**。写 `*` 或 `0.0.0.0:53` → OK。否则算「**已知的**知名境外解析器里还有几个没覆盖」→ LOW（⚠️ **不是按条数判负**，见坑 6） |
| 4 | `encrypted-dns-follow-outbound-mode` | **HIGH** / OK | `true` → HIGH（会成环 / 回退明文）；未设置或 `false` → OK |
| 5 | `always-real-ip` / `use-local-host-item-for-proxy` | **HIGH** / LOW / OK | 缺 `always-real-ip` → LOW；`use-local-host-item-for-proxy = true` → **HIGH** |
| 6 | 测试端点域名归属（**提示性**） | LOW / OK | 逐个看 `internet-test-url` / `proxy-test-url` / `proxy-test-udp`：IP 字面量 → OK；国内域名 → OK；境外域名 → **LOW 提示**（性能取向取舍，见坑 14）；缺失 → LOW。⚠️ **不计入风险等级** |
| 7 | 策略组成员可解析 | **HIGH** / MEDIUM / OK | 空组 → HIGH；未知组类型 → MEDIUM；成员既不在 `[Proxy]` 也不是已知组 / 内置策略 → **HIGH**（Surge 会拒绝加载） |
| 8 | 规则策略可解析 | **HIGH** / MEDIUM / OK | 用 `policy_index()` 定位策略字段；类型未识别或字段不足 → MEDIUM（跳过策略校验）；策略不在已知集合 → **HIGH** |
| 9 | 规则顺序 | **HIGH** / MEDIUM / OK | 无 `FINAL` → HIGH；`FINAL` 不在最后 → MEDIUM；IP 类排在域名类之前 → **HIGH** |
| 10 | `pre-matching` 的策略是字面量 | **HIGH** / LOW / OK | 无 `pre-matching` 规则 → LOW；有 `pre-matching` 但策略不是 `reject*` → **HIGH**；缺 `extended-matching` → LOW |
| 11 | `always-real-ip` 被前置域名规则接住 | MEDIUM / LOW / OK | 本地类主机名（`*.lan` 等）不计数。未接住：若文件里有 `RULE-SET` → LOW（远程内容无法静态判定）；否则 → MEDIUM |
| 12 | IP 类规则的 `no-resolve` | MEDIUM / LOW / OK | 无 IP 类规则 → OK；任一带缺 → **MEDIUM**（⚠️ 不是泄露补丁：走代理时解析在代理端；缺它只是多一次冗余解析。真正风险是连带——补它必须同时有域名类国内直连集）；`FINAL` 缺 `dns-failed` → LOW |

### 4.1 `policy_index()` —— 最容易写错的一处

```python
_RULE_TYPES_WITH_VALUE = {
    "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "DOMAIN-WILDCARD",
    "DOMAIN-SET", "URL-REGEX", "USER-AGENT", "PROCESS-NAME",
    "IP-CIDR", "IP-CIDR6", "IP-ASN", "SRC-IP", "DEST-PORT", "SRC-PORT", "PROTOCOL",
    "GEOIP", "IP-GEOIP", "ASN",
}
_RULE_TYPES_NO_VALUE = {"FINAL"}
```

| 形态 | 策略下标 | 例子 |
|:-----|:--------:|:-----|
| 有匹配值 | **2** | `DOMAIN-SUFFIX,x.com,POLICY` / `GEOIP,CN,DIRECT` / `RULE-SET,SET,POLICY` |
| 无匹配值 | **1** | `FINAL,POLICY` |

⚠️ `RULE-SET` 的 index 1 是**规则集标识**（URL / 内置集合名），不是策略。
⚠️ `GEOIP` 属于"有匹配值"（匹配值是 `CN`）。

**这两处各制造过一批假 HIGH**，合计 24 条。详见 [`pitfalls.md`](pitfalls.md) 坑 4 / 坑 5。

### 4.2 豁免机制

```
# audit-waive: <检查号> <理由>
```

写在 **profile 里**，被 `load_waivers()` 用正则抓出：

```python
r"#\s*audit-waive:\s*(\d+)\s+(.*)"
```

命中的 finding 降级为 `WAIVED:<原级别>`，**照常逐条打印**在报告末尾的
「⚪ 已豁免」区。它不改判定语义的前提是**它仍然可见**。

⚠️ 这意味着 **`.min.conf` 里也要保留这行** —— 它是**有语义的注释**，不是说明文字。

### 4.3 报告格式

```
🔴 HIGH · N 条
   [ 1] 消息
        ↳ 细节
🟠 MEDIUM · N 条
...
🟡 LOW · N 条
...
✅ OK · N 条
...
⚪ 已豁免 · N 条（不改判定，但照样列出来）
   [ 1] 消息
        ↳ ⚠️ 已豁免（profile 内声明）：<理由>

──────────────────────────────────────────────────────────────
result: 0 high, 0 medium, 2 low, 12 ok, 2 waived
✅ 通过
```

`--quiet` 只打印最后两行。

---

## 5 · 规则集内容判据（`audit_ruleset_content.py`）

对每条远程 `RULE-SET`：

### A. 缺 `no-resolve` 的 IP 条目

```python
opts = [p.lower() for p in parts[2:]]
if "no-resolve" not in opts:
    stats["ip_without_no_resolve"].append((i, s))
```

- 命中任一条 → **HIGH**，并打印前 5 条原文 + 剩余条数
- 有一条启用的 `RULE-SET` 里只要有**一条**这种条目，
  **每个走到该规则的域名都会被强制本地解析一次**

### B. 直连集合的域名条目总量

把策略判给 `DIRECT` 的所有集合的**域名条目数**加总：

| 总量 | 判定 |
|:-----|:-----|
| < 1000 | **HIGH** —— 「足以接住国内域名的量级」不够 |
| ≥ 1000 | ✅ |

⚠️ **判据是「数域名条目」，不是看规则集名字，也不是看 README 标题。**
见 [`pitfalls.md`](pitfalls.md) 坑 1 的 `ChinaMax.list` 反例。

### C. 内置集合跳过

```python
BUILTIN_SETS = {"system", "lan", "direct", "proxy", "final", "reject",
                "domestic", "foreign", "cellular", "wifi"}
```

识别方式：标识里没有 `/`、没有 `\`、没有 `.`。

### D. 下载失败

`URLError` / `HTTPError` / `OSError` → 计 `medium`（"结论未知"），**不判 HIGH**。
理由：网络抖动不该被报成一个配置缺陷。

---

## 6 · 分流覆盖判据（`audit_routing_coverage.py`）

| 组 | 探针数 | 期望 |
|:--:|:------:|:-----|
| A · 国内 | 17 | 全部命中 `DIRECT` |
| B · 境外 | 8 | 命中 `PROXY` 或 `AI`，**不能落 `DIRECT`** |
| C · 误杀 | 8 | **绝不能命中 `REJECT`** |

### A 的探针刻意混入非 `.cn`

```
www.baidu.com    www.qq.com       www.taobao.com    www.jd.com
www.bilibili.com www.163.com      www.zhihu.com     www.miui.com
connect.rom.miui.com               www.aliyun.com    www.huawei.com
www.iqiyi.com    www.douyin.com   www.meituan.com   www.12306.cn
www.gov.cn       www.people.com.cn
```

17 个里 12 个非 `.cn`。**只测 `.cn` 会假通过** —— 见 [`pitfalls.md`](pitfalls.md) 坑 2。

### B 的 `allow` 集合

```python
FOREIGN_PROBES = {
    "chat.openai.com":    {"AI", "PROXY"},
    "api.anthropic.com":  {"AI", "PROXY"},
    "gemini.google.com":  {"AI", "PROXY"},
    "github.com":         {"PROXY"},
    "www.google.com":     {"PROXY"},
    "www.youtube.com":    {"PROXY"},
    "t.me":               {"PROXY"},
    "x.com":              {"PROXY"},
}
```

⚠️ AI 类域名允许落 `AI` 或 `PROXY` —— 因为 `v0` 没有 `AI` 组
（AI 流量合流进 `Proxy`）。判据必须对两个版本都成立。

### C 的意义

`github.com` / `jsdelivr.net` / `icloud.com` 这类高频域几乎必然出现在
广告黑名单的误杀面里。**提前发现误杀比等用户报障好。**

### 匹配器实现的边界

`Matcher` 只能按**域名**判定。以下类型**跳过**（无法用域名判定）：

- IP 类（`IP-CIDR` / `GEOIP` / `IP-ASN`）
- `URL-REGEX` / `USER-AGENT` / `PROCESS-NAME` / `PROTOCOL` / 端口类
- `FINAL` —— 命中即返回，作为兜底
- **内置集合**（`SYSTEM` / `LAN`）—— 内容不可得，**视作不命中**

⚠️ 最后一条是个已知的保守近似：探针恰好落在 `SYSTEM` 集合里时会走 `FINAL`，
判据仍会通过（因为 `FINAL → Proxy` 对境外探针是正确的）。
若将来有探针因此误判，应改成显式枚举内置集合的已知内容。

---

## 7 · 架构不变量（`architecture.sh`）

### ① 占位符纪律

| 判据 | 细节 |
|:-----|:-----|
| 禁止子串 | `couldflare-cdn.com` / `tange365.com` / `wangxinyu` —— **注释里也不许出现** |
| IPv4 白名单 | 必须是 `192.0.2.` / `198.51.100.` / `203.0.113.` 开头，或在 `KNOWN_DNS` 集合里 |
| 凭据 | `password` / `username` / `auth` 的值必须以 `REPLACE_WITH_` 开头 |
| SNI | 必须 `REPLACE_WITH_*` / 文档段 IP / `example.com` 结尾 |
| 节点主机名 | `[Proxy]` 段里非 IPv4 的 `server` 必须在 `ALLOWED_DOMAINS` 里 |

⚠️ IPv4 判据只扫**有效行**（`strip_c()` 剥掉整行注释与行尾注释）——
注释里出现私有网段是说明性文字，不是泄露。见 [`pitfalls.md`](pitfalls.md) 坑 8。

### ② DNS 段一致性

16 个键逐字比对 `v0.conf` 与 `v1.conf`：

```python
DNS_KEYS = [
    "dns-server", "encrypted-dns-server", "encrypted-dns-follow-outbound-mode",
    "hijack-dns", "allow-dns-svcb", "exclude-simple-hostnames", "read-etc-hosts",
    "use-local-host-item-for-proxy", "ipv6", "ipv6-vif",
    "geoip-maxmind-url", "disable-geoip-db-auto-update",
    "internet-test-url", "proxy-test-url", "proxy-test-udp",
    "always-real-ip",
]
```

任一键只在一边存在、或值不同 → 失败。

**理由**：`v0` 的定位是「裁剪功能」，不是「裁剪防泄露」。DNS 段被改动即是缺陷。

### ③ 规则顺序铁律

| 断言 | 判据 |
|:-----|:-----|
| ③-a | `FINAL` 必须是最后一条 |
| ③-b (i) | 白名单 DIRECT 在第一条 REJECT 之前；且**只能有一条**（`v0` 豁免） |
| ③-b (ii) | 第一条 REJECT 之后**必须有** DIRECT 规则（否则国内流量整片走代理） |
| ③-c | 所有 IP 类规则在所有域名类规则之后 |
| ③-d | 所有 IP 类规则带 `no-resolve` |

⚠️ ③-b 的两条是**独立的约束**，不是「DIRECT 在 REJECT 之前」一条。
见 [`pitfalls.md`](pitfalls.md) 坑 9。
⚠️ `v0` 刻意无白名单守卫，豁免并打印说明行。见坑 10。

---

## 8 · 判据演进史

| 版本 | 改动 | 原因 |
|:----:|:-----|:-----|
| v1 | `check_3` 按 `hijack-dns` **条数**判负 | 初版 |
| v2 | `check_3` 改为「未覆盖的**已知**知名解析器数」 | 判据**不可能被满足**，见坑 6 |
| v1 | `check_6` 只认 `.cn` / `.com.cn` | 初版 |
| v2 | `check_6` 加 `DOMESTIC_TEST_SUFFIXES` 显式清单 | `miui.com` 被误判为境外，见坑 7 |
| v3 | `check_6` 境外端点从 MEDIUM 降为 **LOW 提示** | 它是性能探针不是泄露通道，见坑 14 |
| v1 | `check_8` 策略取 `parts[1]` | 初版 |
| v2 | 引入 `policy_index()` | `GEOIP` 把 `CN` 当策略 → 12 个假 HIGH，见坑 4 |
| v3 | `policy_index()` 处理 `RULE-SET` | 索引 1 是规则集标识 → 又 12 个假 HIGH，见坑 5 |
| v4 | `policy_index()` 移入 `_surge_common.py` | 两处拷贝，见坑 11 |
| v1 | `check_11` 把本地类主机名也计入"未覆盖" | 初版 |
| v2 | 排除 `*.lan` / `*.local` 等；有 `RULE-SET` 时降级为 LOW | 误报，见坑 8 的同型问题 |
| v1 | 架构检查扫全文找 IPv4 | 初版 |
| v2 | 加 `strip_c()`，只扫有效行 | 注释里的 `10.0.0.0/8` 被误报，见坑 8 |
| v1 | 架构检查断言「DIRECT 不在 REJECT 之前」 | 初版 |
| v2 | 拆成 ③-b (i)(ii) 两条独立约束 | 不变量本身写错了，见坑 9 |
| v1 | ③-b 对 `v0` 也生效 | 初版 |
| v2 | `v0*` 豁免 + 打印说明行 | 要求 v0 改名成 v1，见坑 10 |
| — | 无豁免机制 | 初版：豁免只能写死在审计器里 |
| — | 引入 `# audit-waive:` | 判据可以退让，但退让必须留痕，见坑 15 |
| v1 | `audit_ruleset_content` 遍历原始行 | 初版 |
| v2 | 先 `strip_comment()` | 注释行被当成引用，见坑 12 |
| v1 | `run.sh` 只有"退出码非 0 即失败" | 初版 |
| v2 | 加前置检查，环境故障用退出码 2 | 解释器坏了被算成"判负通过"，见坑 13 |

### 一条贯穿的规律

> 每一轮修订，都不是「发现漏了某个检查」，
> 而是**原来那条判据的方向写错了**（假 HIGH / 不可能满足 / 覆盖了不该覆盖的）。

⇒ **假 HIGH 比漏报危害更大**：漏报只是少发现一个问题；
假 HIGH 会让使用者去改一条**本来正确的**规则，然后把配置改坏。

⇒ 因此本项目对每一条判据都要求：**能说清"怎么做才算过"**，
且**不能说清的就是判据没写好**。

---

## 9 · 全绿 ≠ 可用

审计脚本覆盖的是**静态可判定**的部分。以下必须实测：

| 维度 | 为什么脚本做不到 | 怎么做 |
|:-----|:-----------------|:-------|
| 冷启动有无明文 `:53` | 需要抓包 | Charles / Stream / Wireshark |
| 拦截效果 | 需要真实访问 | 打开几个广告密集的站点看 |
| 误杀 | 需要真实访问 | `github.com` / `jsdelivr.net` / `icloud.com` 是否能开 |
| 节点可用性 | 需要真实网络 | 面板上逐个测 |
| NAT 类型 / 时间同步 | 需要真实设备 | 游戏机连一下 |

> ⚠️ 这是本项目的核心立场：**审计通过 ≠ 配置可用。**
> 每修好一次判据，都要假设「还存在审计器看不见的维度」。
