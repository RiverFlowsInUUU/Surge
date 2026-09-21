"""从带注释的 .conf 生成 .min.conf：去注释、折叠空行、恢复 audit-waive 行。
用法：python make_min.py profiles/routing.conf
"""
import io
import re
import sys

src = sys.argv[1]
dst = src[:-5] + ".min.conf"

lines = io.open(src, encoding="utf-8").read().split("\n")
out = []
prev_blank = False
for ln in lines:
    s = ln.rstrip()
    stripped = s.strip()
    if stripped.startswith("#"):
        # audit-waive 是语义行，必须保留
        if "audit-waive" in stripped and not any("audit-waive" in o for o in out):
            out.append(stripped)
            prev_blank = False
        continue
    if stripped == "":
        if prev_blank:
            continue
        prev_blank = True
        out.append("")
        continue
    prev_blank = False
    out.append(stripped)

# 去掉末尾空行，保证一个结尾换行
while out and out[-1] == "":
    out.pop()

txt = "\n".join(out) + "\n"
io.open(dst, "w", encoding="utf-8", newline="\n").write(txt)
print("✅ 生成 %s（%d 行）" % (dst, len(out)))
