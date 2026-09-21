#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Markdown 相对链接与锚点检查 —— 确认本仓库所有内部链接真的能跳到。

为什么要单独一个脚本：
    改了标题之后，**引用它的所有链接都会静默失效** —— GitHub 不会报错，
    读者点了 404。这类问题肉眼扫不出来（尤其锚点里含中文、emoji、全角标点）。

⭐ 锚点算法按 GitHub 的 slug 规则（`github-slugger` 的行为）实现：
    1. 转小写
    2. 剥掉 Markdown 行内代码的反引号
    3. 只保留 `a-z` / `0-9` / 中日韩汉字 / 空格 / `-`，**其余全删**
       —— 包含 emoji、全角标点（`：` `·` `「」`）、`/`、`_`、`[` `]`
    4. 空格 -> `-`

    ⇒ 两个容易记错的推论：
      · emoji 被删掉了，但它**后面的空格留下** ⇒ `## 🚀 快速开始` -> `#-快速开始`
        （前导一个 `-`）
      · `## 2 · 防泄露原理：从机制到推导` -> `#2--防泄露原理从机制到推导`
        （`·` 与 `：` 被删，两侧空格各留一个 `-`，于是出现**连续两个** `-`）

退出码：0 = 全部可解析；1 = 有失效链接；2 = 环境问题。
"""

import os
import re
import sys

# 用 GitHub 的字符类做白名单：ASCII 小写字母、数字、汉字、空格、连字符
_KEEP = re.compile(r"[a-z0-9\u3400-\u4dbf\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")
_SKIP_DIRS = {".git", "icons", "node_modules", "__pycache__", ".workbuddy-ai"}
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_LINK = re.compile(r"\]\(([^)\s]+)\)")


def gh_slug(heading):
    """按 GitHub 规则把标题文本转成锚点。"""
    s = heading.strip().lower()
    s = s.replace("`", "")          # 行内代码反引号在锚点里不存在
    out = []
    for ch in s:
        if ch == " " or ch == "-":
            out.append(ch)
        elif _KEEP.match(ch):
            out.append(ch)
        # 其余（emoji / 全角标点 / `.` / `/` / `_` / `[` `]` …）全部丢弃
    return "".join(out).replace(" ", "-")


def collect(dirpath):
    files = []
    for root, dirs, names in os.walk(dirpath):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        for n in names:
            if n.endswith((".md", ".markdown")):
                files.append(os.path.join(root, n))
    return sorted(files)


def anchors_of(path):
    s = set()
    for line in open(path, encoding="utf-8"):
        m = _HEADING.match(line.rstrip())
        if m:
            s.add(gh_slug(m.group(2)))
    return s


def main():
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
        for lineno, line in enumerate(open(p, encoding="utf-8"), 1):
            # 跳过 fenced code block 里的行 —— 那里面的 `](...)` 往往是示例
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
