#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分流覆盖审计 —— 拿真实域名把 [Rule] 段从头走一遍，看它最终命中哪条规则。

为什么必须有这个脚本：
    `check_surge_dns.py` 只审文件内部的**结构**（顺序、no-resolve、策略可解析）。
    结构全绿**不等于**分流正确 —— Egern 项目实测过：两个审计脚本双双通过，
    分流却整片是坏的（`ChinaMax.list` 里 99.5% 是 IP，国内域名全落到了 Final → 代理）。

    判据必须是「拿真实域名走一遍」，**不是**「有没有一条叫 China 的规则」，
    也**不是**「规则集名叫 direct.txt」。

它做两件事：
    A. **国内探针**（15 个非 `.cn` 的国内域名 + 若干 `.cn`）必须命中 DIRECT。
       ⚠️ 刻意包含非 `.cn` 的国内域名（`qq.com` / `taobao.com` / `miui.com` …）：
          只有 `.cn` 后缀能直连的配置是**假通过** —— 它靠的是 `DOMAIN-SUFFIX,cn`
          这条兜底，而不是真的接住了国内域名。
    B. **境外探针**（OpenAI / GitHub / Google …）必须命中代理或 AI 组，
       且**绝不能被广告规则误杀**（提前发现误杀比等用户报障好）。

退出码：0 = 全部符合预期；1 = 有探针落错；2 = 用法 / 网络错误。

用法：
    python audit_routing_coverage.py Profile.conf
    python audit_routing_coverage.py Profile.conf --show-all    # 打印全部探针明细
"""

import argparse
import os
import sys
import tempfile
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _surge_common import (  # noqa: E402
    parse_conf,
    policy_index,
    split_csv,
    strip_comment,
)
from audit_ruleset_content import fetch, parse_ruleset  # noqa: E402

# ── 探针清单 ────────────────────────────────────────────────────────────────
# ⭐ 国内探针刻意混入**非 .cn** 的域名 —— 这是本脚本的核心判据之一。
#    只靠 `DOMAIN-SUFFIX,cn` 兜住的配置会在这些域名上暴露。
DOMESTIC_PROBES = [
    "www.baidu.com", "www.qq.com", "www.taobao.com", "www.jd.com",
    "www.bilibili.com", "www.163.com", "www.zhihu.com", "www.miui.com",
    "connect.rom.miui.com", "www.aliyun.com", "www.huawei.com",
    "www.iqiyi.com", "www.douyin.com", "www.meituan.com", "www.12306.cn",
    "www.gov.cn", "www.people.com.cn",
]

# 境外探针：期望走代理（不落到 DIRECT）。allow = 允许命中的策略名集合。
FOREIGN_PROBES = {
    "chat.openai.com": {"AI", "PROXY"},
    "api.anthropic.com": {"AI", "PROXY"},
    "gemini.google.com": {"AI", "PROXY"},
    "github.com": {"PROXY"},
    "www.google.com": {"PROXY"},
    "www.youtube.com": {"PROXY"},
    "t.me": {"PROXY"},
    "x.com": {"PROXY"},
}

# ⭐ 误杀探针：这些域名**一定不能**被广告规则拦。
#    它们几乎必然出现在广告黑名单的误杀面里（Egern 项目的 jinx-surge-white-guard
#    那 42 条就是为它们准备的）。
FALSE_POSITIVE_PROBES = [
    "github.com", "objects.githubusercontent.com", "cdn.jsdelivr.net",
    "www.icloud.com", "gateway.icloud.com", "swcdn.apple.com",
    "www.apple.com", "api.github.com",
]

IP_RULE_TYPES = {"IP-CIDR", "IP-CIDR6", "IP-ASN", "GEOIP", "IP-GEOIP", "SRC-IP", "DEST-IP"}


class Matcher:
    """按 [Rule] 段顺序，对给定域名逐条判定。"""

    def __init__(self, profile_path, cache_dir):
        self.cache = cache_dir
        sections, _ = parse_conf(profile_path)
        self.rules = []
        for lineno, raw in sections.get("rule", []):
            s = strip_comment(raw)
            if not s:
                continue
            parts = split_csv(s)
            if not parts:
                continue
            t = parts[0].strip().upper()
            pi = policy_index(parts)
            pol = parts[pi].strip() if pi is not None and len(parts) > pi else "?"
            arg = parts[1].strip() if len(parts) > 1 else ""
            self.rules.append({"lineno": lineno, "type": t, "arg": arg,
                               "policy": pol, "parts": parts})
        self._sets = {}          # ident -> {"DOMAIN": set(), "SUFFIX": set(), ...}

    # -- 规则集懒加载 ---------------------------------------------------------
    def _load_set(self, ident):
        if ident in self._sets:
            return self._sets[ident]
        store = {"DOMAIN": set(), "DOMAIN-SUFFIX": set(), "DOMAIN-KEYWORD": set(),
                 "DOMAIN-WILDCARD": set()}
        if "/" not in ident and "." not in ident:
            self._sets[ident] = store      # 内置集合：内容不可得，视作不命中
            return store
        try:
            text, _ = fetch(ident, self.cache)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            print(f"   ⚠️  规则集下载失败 {ident.split('/')[-1]}：{e}", file=sys.stderr)
            self._sets[ident] = store
            return store
        for ln, line in enumerate(text.splitlines(), 1):
            s = line.strip()
            if not s or s.startswith("#") or s.startswith(";") or s.startswith("//"):
                continue
            p = [x.strip() for x in s.split(",")]
            tt = p[0].upper()
            val = p[1] if len(p) > 1 else ""
            if tt == "DOMAIN":
                store["DOMAIN"].add(val.lower())
            elif tt == "DOMAIN-SUFFIX":
                store["DOMAIN-SUFFIX"].add(val.lower())
            elif tt == "DOMAIN-KEYWORD":
                store["DOMAIN-KEYWORD"].add(val.lower())
            elif tt == "DOMAIN-WILDCARD":
                store["DOMAIN-WILDCARD"].add(val.lower())
            elif "," not in s:
                store["DOMAIN-SUFFIX"].add(s.lower())
        self._sets[ident] = store
        return store

    # -- 单条规则的匹配 -------------------------------------------------------
    @staticmethod
    def _suffix_hit(domain, suffix):
        d, sf = domain.lower(), suffix.lower().lstrip(".")
        return d == sf or d.endswith("." + sf)

    def _domain_in_store(self, store, domain):
        d = domain.lower()
        if d in store["DOMAIN"]:
            return True
        for sf in store["DOMAIN-SUFFIX"]:
            if self._suffix_hit(d, sf):
                return True
        for kw in store["DOMAIN-KEYWORD"]:
            if kw in d:
                return True
        for w in store["DOMAIN-WILDCARD"]:
            # Surge 通配：`*` 跨点、`?` 单字符 —— 转成正则保守实现
            import re as _re
            pat = "^" + _re.escape(w).replace(r"\*", ".*").replace(r"\?", ".") + "$"
            if _re.match(pat, d):
                return True
        return False

    def match(self, domain):
        """返回命中的规则 dict，或 None（没有任何规则命中）。"""
        for r in self.rules:
            t, arg = r["type"], r["arg"]
            if t == "RULE-SET":
                store = self._load_set(arg)
                if self._domain_in_store(store, domain):
                    return r
            elif t == "DOMAIN":
                if domain.lower() == arg.lower():
                    return r
            elif t == "DOMAIN-SUFFIX":
                if self._suffix_hit(domain, arg):
                    return r
            elif t == "DOMAIN-KEYWORD":
                if arg.lower() in domain.lower():
                    return r
            elif t == "DOMAIN-WILDCARD":
                import re as _re
                pat = "^" + _re.escape(arg).replace(r"\*", ".*").replace(r"\?", ".") + "$"
                if _re.match(pat, domain.lower()):
                    return r
            elif t == "FINAL":
                return r
            # IP 类 / URL-REGEX / USER-AGENT 等无法用"域名"判定 —— 跳过
        return None


def main():
    ap = argparse.ArgumentParser(description="分流覆盖审计（真实域名走一遍）")
    ap.add_argument("profile", help="Surge .conf 文件路径")
    ap.add_argument("--cache-dir", default=None)
    ap.add_argument("--show-all", action="store_true", help="打印全部探针明细")
    a = ap.parse_args()

    if not os.path.isfile(a.profile):
        print(f"❌ 找不到文件：{a.profile}", file=sys.stderr)
        return 2

    cache = a.cache_dir or os.path.join(tempfile.gettempdir(), "surge-ruleset-cache")
    print(f"规则集缓存：{cache}")
    m = Matcher(a.profile, cache)
    print(f"[Rule] 段共 {len(m.rules)} 条规则\n")

    fails = []

    # ── A. 国内探针必须 DIRECT ──────────────────────────────────────────────
    print("── A · 国内探针（期望命中 DIRECT）")
    ok_dom = 0
    for d in DOMESTIC_PROBES:
        r = m.match(d)
        pol = r["policy"] if r else "（无规则命中）"
        if pol.strip().upper() == "DIRECT":
            ok_dom += 1
            if a.show_all:
                print(f"   ✅ {d:<32} → {pol}   (第 {r['lineno']} 行 {r['type']})")
        else:
            fails.append((d, pol, r))
            print(f"   ❌ {d:<32} → {pol}   "
                  f"(第 {r['lineno'] if r else '—'} 行 {r['type'] if r else '—'})")
    print(f"   {ok_dom}/{len(DOMESTIC_PROBES)} 命中 DIRECT\n")

    # ── B. 境外探针不能落 DIRECT ────────────────────────────────────────────
    print("── B · 境外探针（期望走代理 / AI 组，不能落 DIRECT）")
    ok_for = 0
    for d, allow in FOREIGN_PROBES.items():
        r = m.match(d)
        pol = r["policy"] if r else "（无规则命中）"
        if pol.strip().upper() in allow:
            ok_for += 1
            if a.show_all:
                print(f"   ✅ {d:<32} → {pol}")
        else:
            fails.append((d, pol, r))
            print(f"   ❌ {d:<32} → {pol}（期望 {sorted(allow)}）")
    print(f"   {ok_for}/{len(FOREIGN_PROBES)} 符合预期\n")

    # ── C. 误杀探针不能被广告规则拦 ─────────────────────────────────────────
    print("── C · 误杀探针（绝不能命中 REJECT）")
    ok_fp = 0
    for d in FALSE_POSITIVE_PROBES:
        r = m.match(d)
        pol = r["policy"] if r else "（无规则命中）"
        if pol.strip().upper().startswith("REJECT"):
            fails.append((d, pol, r))
            print(f"   ❌ {d:<32} → {pol}（被广告规则误杀！）")
        else:
            ok_fp += 1
            if a.show_all:
                print(f"   ✅ {d:<32} → {pol}")
    print(f"   {ok_fp}/{len(FALSE_POSITIVE_PROBES)} 未被误杀\n")

    print("─" * 62)
    total = len(DOMESTIC_PROBES) + len(FOREIGN_PROBES) + len(FALSE_POSITIVE_PROBES)
    print(f"result: {total - len(fails)} passed, {len(fails)} failed")
    if fails:
        print("❌ 未通过")
        return 1
    print("✅ 通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
