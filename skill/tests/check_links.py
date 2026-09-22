#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Markdown 相对链接与锚点检查 —— 确认本仓库所有内部链接真的能跳到。

为什么要单独一个脚本：
    改了标题之后，**引用它的所有链接都会静默失效** —— GitHub 不会报错，
    读者点了 404。这类问题肉眼扫不出来（尤其锚点里含中文、emoji、全角标点）。

⭐ 锚点算法：自实现（不依赖 node），但**逐条与 github-slugger 对拍过**。
    规则 ≈ 删掉标点 / 符号 / 控制字符，其余保留，空格转 `-`。
    三个最容易写错的点（曾经全踩过，2026-09-22 修正）：

      · `_`(U+005F) **保留** —— 它不在 github-slugger 的删除字符类里。
        `## 4. `policy_groups` 段`  ->  `#4-policy_groups-段`
        （错写成 `4-policygroups-段` 就点不动）
      · FE0F 变体选择符 **保留**（它是 Mn 组合符，不是符号），emoji 本体删掉。
        `## 🛡️ Clash 配置模板`  ->  `#️-clash-配置模板`
        （`#` 后紧跟一个**看不见**的 U+FE0F，别手打）
      · 同名标题从第 2 次出现起加后缀：`#新增` / `#新增-1` / `#新增-2`

    ⚠️ 适用范围：本实现按「中日韩汉字 + 拉丁字母数字 + `_`/`-`/空格 + FE0F」白名单。
       若标题引入新字符类别（希腊 / 西里尔字母、上标数字、`Ⓐ` 这类带圈字母…
       github-slugger 对这些的处理与直觉不同），**必须重跑对拍**：
           node _tools/dump_slugs.mjs <repo> out.json
           python _tools/compare_slug.py out.json
       自检：python check_links.py --selftest

退出码：0 = 全部可解析；1 = 有失效链接；2 = 环境问题。
"""

import os
import re
import sys

# 保留集：ASCII 小写字母、数字、下划线、汉字、假名、谚文、变体选择符 / 键帽组合符
# （`_` 与 `\ufe0f` 是 2026-09-22 的对拍结论：github-slugger 保留它们）
_KEEP = re.compile(r"[a-z0-9_\u3400-\u4dbf\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af"
                   r"\ufe0e\ufe0f\u20e3]")
_SKIP_DIRS = {".git", "icons", "node_modules", "__pycache__", ".workbuddy-ai"}
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_LINK = re.compile(r"\]\(([^)\s]+)\)")
_FENCE = re.compile(r"^\s*(```+|~~~+)")


def gh_slug(heading):
    """按 GitHub（github-slugger）规则把标题文本转成锚点 —— 不含去重后缀。"""
    s = heading.strip().lower()
    s = s.replace("`", "")          # 行内代码反引号在锚点里不存在
    out = []
    for ch in s:
        if ch == " " or ch == "-":
            out.append(ch)
        elif _KEEP.match(ch):
            out.append(ch)
        # 其余（emoji / 全角标点 / `.` / `/` / `[` `]` …）全部丢弃
    return "".join(out).replace(" ", "-")


def anchors_of(path):
    """收集文件里所有可用锚点 —— 含同名标题的 `-1` / `-2` 去重后缀。"""
    occ = {}          # slug -> 已出现次数
    out = set()
    for line in open(path, encoding="utf-8"):
        m = _HEADING.match(line.rstrip())
        if not m:
            continue
        result = gh_slug(m.group(2))
        original = result
        while result in occ:
            occ[original] += 1
            result = f"{original}-{occ[original]}"
        occ[result] = 0
        out.add(result)
    return out


def collect(dirpath):
    files = []
    for root, dirs, names in os.walk(dirpath):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        for n in names:
            if n.endswith((".md", ".markdown")):
                files.append(os.path.join(root, n))
    return sorted(files)


SELFTEST = [
    ("🛡️ Clash 配置模板", "️-clash-配置模板"),
    ("4. `policy_groups` 段", "4-policy_groups-段"),
    ("1.3 `policy_groups` —— 四种类型、组间引用、图标",
     "13-policy_groups--四种类型组间引用图标"),
    ("## 2 · 防泄露原理：从机制到推导", "2--防泄露原理从机制到推导"),
    ("📁 文件结构", "-文件结构"),
    ("abc_def", "abc_def"),
]


def selftest():
    bad = 0
    for head, want in SELFTEST:
        got = gh_slug(head.lstrip("# "))
        flag = "✅" if got == want else "❌"
        if got != want:
            bad += 1
        print(f"  {flag} {head!r}\n     得到 {got!r}  期望 {want!r}")
    # 去重后缀
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("## 新增\n\ntext\n\n## 新增\n\n## 新增\n")
        tmp = f.name
    got = anchors_of(tmp)
    os.unlink(tmp)
    want = {"新增", "新增-1", "新增-2"}
    ok = got == want
    print(f"  {'✅' if ok else '❌'} 同名标题去重 -> {sorted(got)}")
    if not ok:
        bad += 1
    print("─" * 62)
    print("✅ 自检通过" if not bad else f"❌ 自检失败 {bad} 项")
    return 0 if not bad else 1


def main():
    if "--selftest" in sys.argv:
        return selftest()

    root = sys.argv[1] if len(sys.argv) > 1 else "."
    if not os.path.isdir(root):
        print(f"❌ 找不到目录：{root}", file=sys.stderr)
        return 2

    mds = collect(root)
    if not mds:
        print("⚠️  没有找到任何 markdown 文件", file=sys.stderr)
        return 2

    anchors = {os.path.relpath(p, root).replace(os.sep, "/"): anchors_of(p)
               for p in mds}

    bad = []
    checked = 0
    for p in mds:
        rel = os.path.relpath(p, root).replace(os.sep, "/")
        base = os.path.dirname(p)
        fence = None
        for lineno, line in enumerate(open(p, encoding="utf-8"), 1):
            # 跳过 fenced code block 里的行 —— 那里的 `](...)` 往往是示例
            f = _FENCE.match(line)
            if fence:
                if f and line.strip().startswith(fence):
                    fence = None
                continue
            if f:
                fence = f.group(1)
                continue
            for tgt in _LINK.findall(line):
                if tgt.startswith(("http://", "https://", "mailto:", "tel:")):
                    continue
                checked += 1
                path, _, frag = tgt.partition("#")
                if not path:
                    if frag and frag not in anchors.get(rel, set()):
                        bad.append((rel, lineno, "页内锚点不存在", tgt))
                    continue
                tgt_fs = os.path.normpath(os.path.join(base, path))
                tgt_rel = os.path.relpath(tgt_fs, root).replace(os.sep, "/")
                if os.path.isdir(tgt_fs):
                    continue
                if not os.path.exists(tgt_fs):
                    bad.append((rel, lineno, "目标文件不存在", tgt))
                    continue
                if frag and tgt_rel in anchors and frag not in anchors[tgt_rel]:
                    bad.append((rel, lineno, "目标锚点不存在", tgt))

    print(f"扫描 {len(mds)} 个 markdown 文件，检查 {checked} 条相对链接")
    print("─" * 62)
    if bad:
        for rel, lineno, why, tgt in bad:
            print(f"   ❌ {rel}:{lineno}  [{why}]  {tgt}")
        print("─" * 62)
        print(f"result: {len(bad)} 条失效")
        return 1
    print("   ✅ 全部相对链接与锚点均可解析")
    print("─" * 62)
    print("✅ 通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
