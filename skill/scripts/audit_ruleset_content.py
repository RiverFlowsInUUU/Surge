#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""远程规则集审计 —— 下载 Surge profile 引用的**全部**规则集，逐个数它们的内容。

两个必须审、且 profile 里看不见的东西：

  A. **不带 no-resolve 的 IP 类条目**（`IP-CIDR,x/y` 后面没有 `no-resolve`）
     Surge 文档：`no-resolve` 为 true 才"不触发 DNS 解析" ⇒ **不带就触发**。
     一条启用的 RULE-SET 里只要有**一条**这种条目，**每个走到该规则的域名
     都会被强制本地解析一次**。
     实测：`blackmatrix7/Surge/Apple/Apple_All.list` 有 13 条 —— 这就是
     "规则判定 `FINAL → Proxy`、upstream 却是明文引导"的成因。

  B. **直连规则集里到底有没有域名条目**
     给 IP 规则补 no-resolve 会**同时**关掉「靠解析判 IP 归属」这条直连路径。
     此时若没有一个真正的**域名类**规则集接住国内域名，它们会整片落到 FINAL → 代理。
     ⚠️ 判据是「数域名条目」，**不是**看规则集名字，也不是看 README 标题。
     实测：`ChinaMax.list` 只有 64 条域名 / 12472 条 IP —— 名字叫 ChinaMax，
     但 99.5% 是 IP，**单独引用它等于国内域名全靠 IP 判定**。

退出码：0 = 全部通过；1 = 有发现；2 = 用法 / 网络错误。

用法：
    python audit_ruleset_content.py Profile.conf
    python audit_ruleset_content.py Profile.conf --show-domestic   # 打印直连集合明细
    python audit_ruleset_content.py --cache-dir /tmp/ruleset-cache
"""

import argparse
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _surge_common import parse_conf, policy_index, split_csv, strip_comment  # noqa: E402

UA = "surge-audit/1.0"

# 规则集条目类型分类
_DOMAIN_TYPES = {
    "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "DOMAIN-WILDCARD",
    "DOMAIN-SET", "DOMAIN-REGEX", "HOST", "HOST-SUFFIX", "HOST-KEYWORD",
    "HOST-WILDCARD",
}
_IP_TYPES = {"IP-CIDR", "IP-CIDR6", "IP6-CIDR", "SRC-IP", "DEST-IP", "IP-ASN"}
_OTHER_TYPES = {"URL-REGEX", "USER-AGENT", "PROCESS-NAME", "PROTOCOL", "DEST-PORT", "SRC-PORT"}

# 内置规则集（不需要下载）
BUILTIN_SETS = {"system", "lan", "direct", "proxy", "final", "reject",
                "domestic", "foreign", "cellular", "wifi"}


def fetch(url, cache_dir, timeout=45, force=False):
    """下载规则集，带本地缓存。返回 (text, from_cache)。"""
    key = re.sub(r"[^A-Za-z0-9._-]", "_", url)[-120:]
    path = os.path.join(cache_dir, key)
    if os.path.isfile(path) and not force:
        return open(path, encoding="utf-8", errors="replace").read(), True
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8", errors="replace")
    os.makedirs(cache_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(raw)
    return raw, False


def parse_ruleset(text):
    """把规则集文本切成条目，返回统计字典。"""
    stats = {
        "total": 0,
        "by_type": {},
        "domain_types": {},
        "ip_types": {},
        "other_types": {},
        "ip_without_no_resolve": [],   # [(lineno, 条目)]
        "samples_domain": [],
        "samples_ip": [],
    }
    for i, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if not s or s.startswith("#") or s.startswith(";") or s.startswith("//"):
            continue
        stats["total"] += 1
        # Surge 规则集也容忍 `A,B` 形式，与 profile 的规则同构
        parts = [p.strip() for p in s.split(",")]
        t = parts[0].upper()
        stats["by_type"][t] = stats["by_type"].get(t, 0) + 1
        if t in _DOMAIN_TYPES:
            stats["domain_types"][t] = stats["domain_types"].get(t, 0) + 1
            if len(stats["samples_domain"]) < 3:
                stats["samples_domain"].append(s)
        elif t in _IP_TYPES:
            stats["ip_types"][t] = stats["ip_types"].get(t, 0) + 1
            if len(stats["samples_ip"]) < 3:
                stats["samples_ip"].append(s)
            opts = [p.lower() for p in parts[2:]]
            if "no-resolve" not in opts:
                stats["ip_without_no_resolve"].append((i, s))
        elif t in _OTHER_TYPES:
            stats["other_types"][t] = stats["other_types"].get(t, 0) + 1
        # 裸域名（无逗号）也按 DOMAIN-SUFFIX 处理 —— 部分社区的 .list 这么写
        else:
            if "," not in s and re.match(r"^[A-Za-z0-9*._-]+$", s):
                stats["domain_types"]["<裸域名>"] = stats["domain_types"].get("<裸域名>", 0) + 1
                stats["domain_types"]["DOMAIN-SUFFIX"] = stats["domain_types"].get("DOMAIN-SUFFIX", 0) + 1
    return stats


def collect_ruleset_refs(sections):
    """从 [Rule] 段抽出所有 RULE-SET 引用，返回 [(lineno, 标识, 策略, 选项)]。

    `标识` 是 URL / 本地路径 / 内置集合名三者之一。内置集合名不下载，只记录。
    """
    out = []
    for lineno, raw in sections.get("rule", []):
        s = strip_comment(raw)
        if not s:
            continue
        parts = split_csv(s)
        if not parts or parts[0].strip().upper() != "RULE-SET":
            continue
        ident = parts[1].strip() if len(parts) > 1 else ""
        pi = policy_index(parts)
        pol = parts[pi].strip() if pi is not None and len(parts) > pi else "?"
        opts = [p.strip() for p in parts[3:]]
        out.append((lineno, ident, pol, opts))
    return out


def main():
    ap = argparse.ArgumentParser(description="远程规则集内容审计（no-resolve / 域名条目）")
    ap.add_argument("profile", help="Surge .conf 文件路径")
    ap.add_argument("--cache-dir", default=None, help="规则集缓存目录")
    ap.add_argument("--force", action="store_true", help="忽略缓存重新下载")
    ap.add_argument("--show-domestic", action="store_true", help="打印直连集合明细")
    a = ap.parse_args()

    if not os.path.isfile(a.profile):
        print(f"❌ 找不到文件：{a.profile}", file=sys.stderr)
        return 2

    cache = a.cache_dir or os.path.join(tempfile.gettempdir(), "surge-ruleset-cache")
    sections, _ = parse_conf(a.profile)
    refs = collect_ruleset_refs(sections)

    if not refs:
        print("⚠️  这份 profile 没有任何 RULE-SET 规则（无事可做）")
        return 0

    print(f"规则集缓存：{cache}")
    print(f"共 {len(refs)} 条 RULE-SET 规则\n")

    high = 0
    medium = 0
    domestic_domain_rules = []   # [(标识, 域名条目数)] 判给 DIRECT 的集合

    for lineno, ident, policy, opts in refs:
        is_builtin = "/" not in ident and "\\" not in ident and "." not in ident
        if is_builtin and ident.lower() in BUILTIN_SETS:
            print(f"── 第 {lineno} 行 · {ident}（Surge 内置集合，跳过）→ {policy}")
            continue
        try:
            text, cached = fetch(ident, cache, force=a.force)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            print(f"── 第 {lineno} 行 · {ident}")
            print(f"   ⚠️  下载失败：{e}（跳过，结论未知）\n")
            medium += 1
            continue

        st = parse_ruleset(text)
        dcount = sum(st["domain_types"].values())
        icount = sum(st["ip_types"].values())
        flag = "（缓存）" if cached else "（新下载）"

        print(f"── 第 {lineno} 行 · {ident.split('/')[-1]} {flag} → {policy}")
        print(f"   共 {st['total']} 条：域名类 {dcount} / IP 类 {icount} / "
              f"其他 {sum(st['other_types'].values())}")
        if st["domain_types"]:
            print(f"   域名类型：{st['domain_types']}")
        if st["ip_types"]:
            print(f"   IP 类型：{st['ip_types']}")

        # A. 缺 no-resolve 的 IP 条目
        bad = st["ip_without_no_resolve"]
        if bad:
            high += 1
            print(f"   🔴 HIGH：{len(bad)} 条 IP 类条目**不带 no-resolve**"
                  f" —— 每个走到本规则的域名都会被强制本地解析一次")
            for ln, entry in bad[:5]:
                print(f"        第 {ln} 行：{entry}")
            if len(bad) > 5:
                print(f"        …另有 {len(bad) - 5} 条")
        elif icount:
            print(f"   ✅ IP 类条目全部带 no-resolve")

        # B. 判给 DIRECT 的集合是否真的能接住域名
        if policy.strip().upper() == "DIRECT":
            domestic_domain_rules.append((ident.split("/")[-1], dcount, icount))

        print()

    # ── B 的汇总判据 ────────────────────────────────────────────────────────
    if domestic_domain_rules:
        total_domain = sum(x[1] for x in domestic_domain_rules)
        print("─" * 62)
        print("直连（DIRECT）规则集的域名条目统计：")
        for name, d, i in domestic_domain_rules:
            print(f"   {name:<44} 域名 {d:>6} / IP {i:>6}")
        if a.show_domestic:
            print()
        print()
        if total_domain < 1000:
            high += 1
            print(f"🔴 HIGH：所有 DIRECT 规则集加起来只有 {total_domain} 条域名条目")
            print("   判据是「数域名条目」，不是看规则集名字。IP 规则带了 no-resolve 之后")
            print("   不再匹配域名，国内域名只能靠域名类规则集接住 —— 这个量级接不住，")
            print("   国内网站会整片落到 FINAL → 代理。")
        else:
            print(f"✅ 直连集合共 {total_domain} 条域名条目 —— 足以接住国内域名")
        print()

    print("─" * 62)
    print(f"result: {high} high, {medium} unknown")
    if high:
        print("❌ 未通过")
        return 1
    print("✅ 通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
