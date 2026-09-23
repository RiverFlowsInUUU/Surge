#!/usr/bin/env bash
# ── 架构不变量检查（不需要网络，不需要 Surge）────────────────────────────────
#
# 为什么需要这个脚本：
#   本仓库的 profiles/*.conf 是**脱敏模板**，里面的节点是占位符。
#   占位符一旦被"顺手改回"真实值，或某个版本忘了同步 DNS 段，
#   问题不会在审计脚本里暴露 —— 那批脚本审的是"结构对不对"，
#   不是"这份文件该不该公开"。
#
#   所以这里守三条**只有本项目才成立**的不变量：
#     ① 占位符纪律：节点地址必须是 RFC 5737 文档地址段 / example.com，
#        凭据必须是 REPLACE_WITH_*，**绝不能**出现真实 IP / 真实域名 / 真实凭据。
#     ② 带注释版与 min 版的 DNS 段必须**逐字相同** ——
#        min 版的定位是"去掉注释"，不是"裁剪配置"，DNS 段被改动即是缺陷。
#     ③ 规则顺序铁律：每个 profile 里，白名单 → REJECT → 域名类直连 → IP 类 → FINAL。
#
#   ②的目标是**两组**文件：lazy / lazy.min 与 routing / routing.min。
#   两组共用同一份 DNS 段定义（见 DNS_KEYS），是刻意的：
#   防泄露结构不该因为"这份配置是分流版"就降级。
#
# 退出码：0 = 通过；1 = 有违规；2 = 环境问题（文件缺失 / python 不可用）。
#
# 用法：
#   bash skill/tests/architecture.sh
#   PY=/path/to/python bash skill/tests/architecture.sh

set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
PROFILES="$ROOT/profiles"
PY="${PY:-python3}"

# ⚠️ Git Bash / MSYS 下 `pwd` 返回 `/c/Users/...`，Windows 版 Python 打不开。
if command -v cygpath >/dev/null 2>&1; then
  ROOT_W="$(cygpath -w "$ROOT")"
  PROFILES_W="$(cygpath -w "$PROFILES")"
else
  ROOT_W="$ROOT"
  PROFILES_W="$PROFILES"
fi

if ! "$PY" -c "import sys" >/dev/null 2>&1; then
  printf '\n❌ 前置检查失败：解释器不可用。PY=%s\n' "$PY" >&2
  exit 2
fi
if [ ! -d "$PROFILES" ]; then
  printf '\n❌ 前置检查失败：找不到 %s\n' "$PROFILES" >&2
  exit 2
fi

printf '%s\n' "架构不变量检查"
printf '%s\n' "────────────────────────────────────────────────────────────"

"$PY" - "$PROFILES_W" <<'PYEOF'
import os, re, sys

profiles_dir = sys.argv[1]
files = sorted(f for f in os.listdir(profiles_dir) if f.endswith(".conf"))
if not files:
    print("❌ profiles/ 里没有 .conf 文件")
    sys.exit(2)

fails = []
oks = []

# ── ① 占位符纪律 ────────────────────────────────────────────────────────────
# RFC 5737 文档地址段：192.0.2.0/24、198.51.100.0/24、203.0.113.0/24
DOC_NETS = ("192.0.2.", "198.51.100.", "203.0.113.")
# 允许出现在模板里的域名（占位域名 + 公开规则集/测试端点域名）
ALLOWED_DOMAINS = (
    "example.com", "example.net", "example.org",
    "sub.example.com",                 # 订阅 URL 的占位域名（routing_v3.conf）
    "cdn-relay.example.com",
    "connect.rom.miui.com",            # 连通性测试端点
    "www.gstatic.com",                 # TCP 测速端点（性能探针，刻意境外）
    "raw.githubusercontent.com",       # 规则集地址
    "cdn.jsdelivr.net",                # 规则集地址
    "github.com", "api.github.com", "objects.githubusercontent.com",
    "www.google.com", "g.cn", "google.cn",   # [URL Rewrite] 的目标
    "apple.com",                       # proxy-test-udp 的探针
    "Surge",             # README / 图标路径里的仓库名
    "Jinx", "ACL4SSR", "Loyalsoldier", "adysec",  # 上游仓库名
    "blackmatrix7",                    # 上游规则集仓库名
    "nintendo.net", "playstation.net", "xboxlive.com",      # 规则匹配值
    "pool.ntp.org", "market.xiaomi.com", "home.arpa",
)
# 敏感串黑名单：真实凭据的常见形态 + 本项目源配置里的私有域名
FORBIDDEN_SUBSTRINGS = [
    "couldflare-cdn.com",   # 源配置里的私有中转域名（已脱敏）
    "tange365.com",         # 源配置里提到的私有业务域
    "wangxinyu",            # 个人信息残留的常见形态
]

# ⚠️ 订阅 token 纪律：`policy-path=` 里的 URL **只能有占位 token**。
#    真实 token 一旦公开 = 别人能刷你的机场流量，是本仓库最严重的一类泄露。
#    判据：URL 里若出现 `token=` / `key=` / `sub=` 参数，其值必须含 REPLACE_WITH。
TOKEN_RE = re.compile(r"(?:token|key|sub)\s*=\s*([A-Za-z0-9_\-]{6,})", re.I)
_IPV4 = re.compile(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b")

def strip_c(s):
    """去掉整行注释与行尾注释（` #` / ` ;` 起）。"""
    if s.startswith("#") or s.startswith(";"):
        return ""
    for i in range(1, len(s)):
        if s[i] in "#;" and s[i - 1] in " \t":
            return s[:i].strip()
    return s.strip()

for f in files:
    raw_text = open(os.path.join(profiles_dir, f), encoding="utf-8").read()
    # ⚠️ 只检查**有效配置行**，不检查注释。
    #    第一版没做这一步，`# …跟 10.0.0.0/8 比一下` 这句注释被当成真实 IP 报负 ——
    #    "注释里出现私有网段"是说明性文字，不是泄露。
    text = "\n".join(strip_c(l) for l in raw_text.splitlines())

    # ①-a 禁止的敏感子串（注释里也不许出现 —— 那是真实凭据的残留）
    for bad in FORBIDDEN_SUBSTRINGS:
        if bad in raw_text:
            fails.append(f"{f}: 出现禁止的敏感串 `{bad}`")

    # ①-b 每个出现的 IPv4 必须是文档地址段或已知公共 DNS（只看有效行）
    KNOWN_DNS = {
        "223.5.5.5", "119.29.29.29", "1.1.1.1", "8.8.8.8", "8.8.4.4",
        "1.0.0.1", "9.9.9.9", "208.67.222.222", "114.114.114.114",
    }
    for ip in set(_IPV4.findall(text)):
        if ip.startswith(DOC_NETS) or ip in KNOWN_DNS:
            continue
        fails.append(f"{f}: 出现非占位 IPv4 `{ip}`（必须用 192.0.2.x / 198.51.100.x / 203.0.113.x）")

    # ①-c 凭据字段必须显式写成 REPLACE_WITH_*
    for m in re.finditer(r"(password|username|auth)\s*=\s*\"?([^,\"\n]+)", text):
        val = m.group(2).strip()
        if val.startswith("REPLACE_WITH_"):
            continue
        fails.append(f"{f}: 凭据字段 `{m.group(1)}` 的值不是占位符（`{val[:24]}…`）")
    for m in re.finditer(r"sni\s*=\s*([^,\n]+)", text):
        val = m.group(1).strip()
        if val.startswith("REPLACE_WITH_") or val.startswith("192.0.2.") \
                or val.startswith("198.51.100.") or val.startswith("203.0.113.") \
                or val.endswith("example.com"):
            continue
        fails.append(f"{f}: sni 的值不是占位符（`{val}`）")

    # ①-c2 订阅 token / key 必须占位符化（最严重的一类泄露：泄露即被盗刷流量）
    for m in TOKEN_RE.finditer(raw_text):
        val = m.group(1)
        if "REPLACE_WITH" in val.upper():
            continue
        fails.append(f"{f}: 订阅 URL 里出现疑似真实 token（`{val[:8]}…`）—— "
                     f"必须写成 REPLACE_WITH_YOUR_TOKEN")

    # ①-d 节点行里的主机名必须落在允许清单（只看有效行）
    in_proxy = False
    for i, line in enumerate(text.splitlines(), 1):
        s = line
        if s.startswith("[Proxy]"):
            in_proxy = True
            continue
        if s.startswith("[") and in_proxy:
            in_proxy = False
        if not in_proxy or not s or "=" not in s:
            continue
        rhs = s.split("=", 1)[1]
        p = [x.strip() for x in rhs.split(",")]
        if len(p) < 2:
            continue
        server = p[1]
        if _IPV4.match(server) or server.startswith("["):
            continue
        if not any(a in server for a in ALLOWED_DOMAINS):
            fails.append(f"{f}:{i}: [Proxy] 里的节点主机名 `{server}` 不在允许清单内")

# ── ② DNS 段一致性：带注释版与 min 版的 DNS 相关键逐字相同 ─────────────────
DNS_KEYS = [
    "dns-server", "encrypted-dns-server", "encrypted-dns-follow-outbound-mode",
    "hijack-dns", "allow-dns-svcb", "exclude-simple-hostnames", "read-etc-hosts",
    "use-local-host-item-for-proxy", "ipv6", "ipv6-vif",
    "geoip-maxmind-url", "disable-geoip-db-auto-update",
    "internet-test-url", "proxy-test-url", "proxy-test-udp",
    "always-real-ip",
]

def dns_kv(path):
    d = {}
    for line in open(path, encoding="utf-8"):
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        if k.strip() in DNS_KEYS:
            d[k.strip()] = v.strip()
    return d

# ⚠️ 两组形态，各查一遍。routing 与 lazy 的 DNS 段**必须逐字相同** ——
#    "这份配置是分流版"不构成降低防泄露标准的理由。
for _stem in ("lazy", "routing_v3"):
    full_p = os.path.join(profiles_dir, f"{_stem}.conf")
    min_p = os.path.join(profiles_dir, f"{_stem}.min.conf")
    if not (os.path.isfile(full_p) and os.path.isfile(min_p)):
        fails.append(f"找不到 {_stem}.conf 或 {_stem}.min.conf —— 两份形态必须同时存在")
        continue
    a, b = dns_kv(full_p), dns_kv(min_p)
    bad = False
    for k in DNS_KEYS:
        if k not in a or k not in b:
            # min 版与完整版都应含全部 DNS 键；缺一个就说明有人漏抄
            if k in a or k in b:
                fails.append(f"DNS 段不一致：`{k}` 只在 "
                             f"{_stem + '.conf' if k in a else _stem + '.min.conf'} 里存在")
                bad = True
            continue
        if a[k] != b[k]:
            fails.append(f"DNS 段不一致：`{k}` 的值不同\n"
                         f"        {_stem}.conf:     {a[k]}\n"
                         f"        {_stem}.min.conf: {b[k]}")
            bad = True
    if not bad:
        oks.append(f"{_stem}.conf / {_stem}.min.conf 的 {len(DNS_KEYS)} 个 DNS 相关键逐字相同")

# ②-b 跨形态：routing 与 lazy 的 DNS 段也必须相同（防泄露结构不因分流粒度而变）
_lf = os.path.join(profiles_dir, "lazy.conf")
_rf = os.path.join(profiles_dir, "routing_v3.conf")
if os.path.isfile(_lf) and os.path.isfile(_rf):
    a, b = dns_kv(_lf), dns_kv(_rf)
    diff = [k for k in DNS_KEYS if a.get(k) != b.get(k)]
    if diff:
        for k in diff:
            fails.append(f"lazy 与 routing 的 DNS 段不一致：`{k}`\n"
                         f"        lazy.conf:    {a.get(k)}\n"
                         f"        routing_v3.conf: {b.get(k)}")
    else:
        oks.append(f"lazy.conf 与 routing_v3.conf 的 {len(DNS_KEYS)} 个 DNS 键也逐字相同"
                   f"（防泄露结构不因分流粒度而变）")

# ── ③ 规则顺序铁律 ──────────────────────────────────────────────────────────
def rules_of(path):
    out, cur = [], False
    for ln, line in enumerate(open(path, encoding="utf-8"), 1):
        s = line.strip()
        if s.startswith("[Rule]"):
            cur = True
            continue
        if s.startswith("[") and cur:
            break
        if cur and s and not s.startswith("#"):
            out.append((ln, s))
    return out

for f in files:
    rs = rules_of(os.path.join(profiles_dir, f))
    if not rs:
        fails.append(f"{f}: [Rule] 段为空")
        continue
    types, pols = [], []
    for ln, s in rs:
        p = [x.strip() for x in s.split(",")]
        types.append(p[0].upper())
        pols.append(p[2].upper() if len(p) > 2 else (p[1].upper() if len(p) > 1 else ""))

    # ③-a FINAL 必须是最后一条
    if types[-1] != "FINAL":
        j = types.index("FINAL") if "FINAL" in types else -1
        if j >= 0:
            fails.append(f"{f}: FINAL 不是最后一条（第 {rs[j][0]} 行）")
        else:
            fails.append(f"{f}: 没有 FINAL 兜底规则")

    # ③-b 白名单必须在拦截之前，且拦截必须在**域名类直连**之前。
    #
    # ⚠️ 判据不是"第一条 DIRECT 在第一条 REJECT 之前" —— 第一版这么写，
    #    把**白名单**（它本来就是 DIRECT，且**必须**排在 REJECT 前面）判成了违规。
    #    这里的真实铁律是两条独立的约束：
    #      (i) 白名单 DIRECT 在本文件的第一条 REJECT 之前（否则白名单形同虚设）；
    #      (ii) 第一条 REJECT 在第一条"域名类直连规则"之前
    #           （否则国内广告域名被 direct.txt 接走，REJECT 永远轮不到）。
    #    (ii) 没法用"策略==DIRECT"表达 —— direct.txt 是 RULE-SET 也是 DIRECT。
    #    改用"白名单之后的第一条 DIRECT"近似：白名单是紧挨着 REJECT 的那条规则。
    REJECT_I = [i for i, p in enumerate(pols) if p.startswith("REJECT")]
    DIRECT_I = [i for i, p in enumerate(pols) if p == "DIRECT"]
    first_reject = REJECT_I[0] if REJECT_I else None
    if first_reject is not None:
        before = [i for i in DIRECT_I if i < first_reject]
        after = [i for i in DIRECT_I if i > first_reject]
        if not before:
            fails.append(f"{f}: 没有白名单（第一条 REJECT 在第 {rs[first_reject][0]} 行，"
                         f"它之前没有任何 DIRECT 规则）")
        elif len(before) > 1:
            fails.append(f"{f}: 第一条 REJECT 之前有 {len(before)} 条 DIRECT 规则"
                         f"（第 {rs[before[0]][0]}…{rs[before[-1]][0]} 行）—— "
                         f"白名单应当只有一条")
        else:
            oks.append(f"{f}: 白名单（第 {rs[before[0]][0]} 行）在拦截"
                       f"（第 {rs[first_reject][0]} 行）之前 👍")
        if not after:
            fails.append(f"{f}: 拦截之后没有任何 DIRECT 规则 —— 国内流量会整片走代理")

    # ③-c 所有 IP 类规则必须在所有域名类规则之后
    IP_TYPES = {"IP-CIDR", "IP-CIDR6", "IP-ASN", "GEOIP", "IP-GEOIP"}
    DOM_TYPES = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "DOMAIN-WILDCARD", "RULE-SET"}
    first_ip = next((i for i, t in enumerate(types) if t in IP_TYPES), None)
    last_dom = max((i for i, t in enumerate(types) if t in DOM_TYPES), default=None)
    if first_ip is not None and last_dom is not None and first_ip < last_dom:
        fails.append(f"{f}: 第 {rs[first_ip][0]} 行的 IP 类规则排在 "
                     f"第 {rs[last_dom][0]} 行的域名类规则之前")

    # ③-d IP 类规则全带 no-resolve
    for (ln, s), t in zip(rs, types):
        if t in IP_TYPES and "no-resolve" not in s.lower():
            fails.append(f"{f}:{ln}: IP 类规则缺 no-resolve → {s}")

    oks.append(f"{f}: {len(rs)} 条规则，顺序与 no-resolve 均符合铁律")

# ── ④ routing_v3.conf 的组顺序必须与 Egern v3 对齐 ───────────────────────────
#
# ⚠️ 为什么必须有这一条（这是**踩过两次**的坑）：
#    [Proxy Group] 的**先后顺序**此前没有任何断言守着 —— 改一个组、挪一段注释，
#    顺序就可能悄悄漂走，而所有其它断言（成员可解析、规则可解析、地区正则一致）
#    **照样全绿**。老板两次发现"分流组前后顺序又错了"，两次都是靠肉眼。
#    ⇒ 顺序是**被承诺过的对外特征**（README 明写"与 Egern v3 对齐"），
#      就必须有机械对账。
#
# 顺序来源（唯一真值）：仓库外的参考配置 Egern v3。
# ⚠️ 该文件**不在本仓库内**，所以断言采用"**把顺序写死在这里**"的做法：
#    它是承诺值，不是从外部文件推导出来的。改顺序 = 必须同时改这里，
#    这正是我们想要的 —— 逼改动者显式面对"我在改一个承诺"。
PG_ORDER = [
    "Proxy", "Smart",
    "ChatGPT", "Gemini", "Claude", "AI",
    "Spotify", "YouTubeMusic", "YouTube", "GitHub", "Google", "Microsoft",
    "Telegram", "Twitter",
    "Airport", "WeChat", "AD",
    "Hong Kong", "USA", "Japan", "Taiwan", "Singapore", "Korea",
    "Other Regions", "MAX",
    "Final",
]

def group_order(path):
    out, cur = [], False
    import re as _re
    for ln, line in enumerate(open(path, encoding="utf-8"), 1):
        s = line.strip()
        if s == "[Proxy Group]":
            cur = True
            continue
        if s.startswith("[") and cur:
            break
        if not cur or not s or s.startswith("#") or "=" not in s:
            continue
        name = s.split("=", 1)[0].strip()
        rhs = s.split("=", 1)[1].strip()
        if _re.match(r"^(select|smart|url-test|load-balance|fallback|round-robin)\b", rhs):
            out.append((ln, name))
    return out

_rf_full = os.path.join(profiles_dir, "routing_v3.conf")
if os.path.isfile(_rf_full):
    got = group_order(_rf_full)
    got_names = [n for _, n in got]
    if got_names == PG_ORDER:
        oks.append(f"routing_v3.conf: [Proxy Group] 的 {len(PG_ORDER)} 个组顺序"
                   f"与 Egern v3 对齐 👍")
    else:
        diffs = []
        for i in range(max(len(got_names), len(PG_ORDER))):
            a = PG_ORDER[i] if i < len(PG_ORDER) else "<缺>"
            b = got_names[i] if i < len(got_names) else "<多>"
            if a != b:
                line = got[i][0] if i < len(got) else None
                diffs.append(f"        第 {i+1} 位：期望 `{a}`，实际 `{b}`"
                             + (f"（第 {line} 行）" if line else ""))
        fails.append("routing_v3.conf: [Proxy Group] 顺序与 Egern v3 不一致\n"
                     + "\n".join(diffs)
                     + "\n        ⇒ 顺序是对外承诺（README 明写与 Egern 对齐）；"
                       "确实要改就同时更新本文件的 PG_ORDER")

    # ④-b min 版必须与完整版组顺序一致（min 是同一份配置去注释，不能各排各的）
    _rf_min = os.path.join(profiles_dir, "routing_v3.min.conf")
    if os.path.isfile(_rf_min):
        got_min = [n for _, n in group_order(_rf_min)]
        if got_min == got_names:
            oks.append("routing_v3.conf / routing_v3.min.conf 的组顺序一致 👍")
        else:
            fails.append("routing_v3.min.conf 的组顺序与 routing_v3.conf 不同 —— "
                         "min 版应由完整版机械生成，不该各排各的")

# ── 输出 ────────────────────────────────────────────────────────────────────
for o in oks:
    print(f"   ✅ {o}")
for x in fails:
    print(f"   ❌ {x}")
print("────────────────────────────────────────────────────────────")
print(f"result: {len(oks)} passed, {len(fails)} failed")
sys.exit(1 if fails else 0)
PYEOF
rc=$?
if [ "$rc" = "0" ]; then
  printf '%s\n' "✅ 通过"
else
  printf '%s\n' "❌ 未通过"
fi
exit $rc
