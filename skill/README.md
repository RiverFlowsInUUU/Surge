# skill · surge-profile-dns-hardening

给 AI Agent 用的**审计方法论 + 可复跑脚本**。也可以纯手工用（每个脚本都能独立跑）。

## 安装

```bash
# 拷到 Agent skills 目录（以 WorkBuddy 为例）
cp -r skill ~/.workbuddy-ai/skills/surge-profile-dns-hardening
```

之后对话里提到「Surge 配置」「DNS 泄露」「引导解析」「规则集缺 no-resolve」等，
Agent 会自动加载。

## 内容

| 文件 | 作用 |
|---|---|
| `SKILL.md` | **主干**：三条出口模型、12 项审计清单、加固模板、三条铁律、坑索引、验收 6 条 |
| `reference/hardening-template.md` | 加固模板逐段完整版（含逐行理由） |
| `reference/pitfalls.md` | **已踩过的坑** —— 事故复盘全文 |
| `reference/leak-localization.md` | 定位「泄露到运营商」的网络侧实测流程 |
| `reference/checker.md` | 三个审计脚本的命令 + 12 项判据 + 判据演进史 |
| `reference/ruleset-weight.md` | 规则集"重量"：按类型数条目 / 识破名字骗人 |
| `reference/public-repo.md` | 公开模板仓库的交付物清单与维护方式 |
| `scripts/check_surge_dns.py` | **profile 层审计**（清单 1–12）。端点是 IP 字面量吗、`dns-server` 是不是 `system`、IP 规则带 `no-resolve` 吗、策略名能解析吗、`pre-matching` 是不是字面量、规则顺序对不对 |
| `scripts/audit_ruleset_content.py` | **规则集层审计**（远程内容）。下载全部被引用的远程规则集，数「缺 `no-resolve` 的 IP 条目」与「直连集合的域名条目总量」 |
| `scripts/audit_routing_coverage.py` | **分流覆盖审计**。域名 → 命中规则 → 策略；17 个国内探针（**刻意混入非 `.cn`**）+ 8 个境外探针 + 8 个误杀探针 |
| `scripts/_surge_common.py` | 共享逻辑（INI 解析 / 端点判据 / `policy_index`），**所有脚本从这里 import** |
| `tests/run.sh` | 5 阶段回归，13 个断言 |
| `tests/architecture.sh` | 三条项目不变量（占位符纪律 / v0-v1 DNS 段一致性 / 规则顺序铁律） |
| `tests/*.conf` | 3 个 fixture（1 个期望通过 + 2 个**期望判负**） |

> 📐 **为什么拆**：Anthropic 官方 skill 撰写规范要求 `SKILL.md` 正文 **< 500 行**
> （原文：*Keep SKILL.md body under 500 lines for optimal performance. If your content exceeds
> this, split it into separate files*），超出部分按 **progressive disclosure** 移入 `reference/`。
> 引用只嵌**一层**（`SKILL.md` → `reference/*.md`）。
> ⚠️ `reference/` 与 `scripts/` / `tests/` 同级，都在 `skill/` 目录内 ⇒ `cp -r skill ...` 仍然一次拷全。

## 依赖

Python 3.8+，**仅标准库**（`urllib` / `re` / `argparse` / `tempfile`）。
不需要 `requests`、不需要 `pyyaml`。

## 用法

```bash
S=./skill/scripts

python "$S/check_surge_dns.py"          profiles/v1.conf   # 期望 0 high
python "$S/check_surge_dns.py"          profiles/v1.conf --strict   # medium 也算失败
python "$S/check_surge_dns.py"          profiles/v1.conf --quiet    # 只打印计数

python "$S/audit_ruleset_content.py"    profiles/v1.conf   # 期望通过（需联网）
python "$S/audit_ruleset_content.py"    profiles/v1.conf --show-domestic

python "$S/audit_routing_coverage.py"   profiles/v1.conf   # 期望 33/33（需联网）
python "$S/audit_routing_coverage.py"   profiles/v1.conf --show-all

bash ./skill/tests/run.sh                                  # 5 阶段，13 断言
SKIP_NET=1 bash ./skill/tests/run.sh                       # 跳过联网阶段 4
```

退出码 **0 = 通过**，用于提交前检查。

规则集缓存写在系统临时目录（`%TEMP%\surge-ruleset-cache` / `/tmp/surge-ruleset-cache`），
约 10 MB —— `direct.txt` 一份就有 11 万条。

> 📌 **全部验证都在本地完成 —— 本仓库刻意不挂 CI / 任何自动化。**
> 这是个人模板仓库，不会有外部贡献者，"自动验 PR"价值接近于零，而本地跑一次只要几十秒；
> 少一个对外暴露的面就少一份事。
> 全部验证用上面的本地命令即可完整复现，功能上没有任何损失。

### `tests/run.sh` 的五个阶段

| 阶段 | 断言对象 | 断言数 | 需要联网 |
|:----:|:---------|:------:|:--------:|
| 1 | 3 个 fixture × `check_surge_dns.py` | 3 | ❌ |
| 2 | 4 份 `profiles/*.conf` × `check_surge_dns.py` | 4 | ❌ |
| 3 | `architecture.sh`（架构不变量） | 1 | ❌ |
| 4 | 2 份 profile × 2 个联网审计脚本 | 4 | ✅ |
| 5 | `check_links.py`（markdown 链接与锚点） | 1 | ❌ |

> ⚠️ **阶段 1 里有两个"期望判负"的 fixture**（`bad_bootstrap` / `bad_order_and_policy`）。
> 它们的存在是为了证明审计器**真的有判别力**，而不是恒返回 0。
>
> ⚠️ 也因此，`run.sh` 一开始就有「解释器与依赖」的前置检查：解释器坏掉时脚本会以
> **退出码 1** 结束 —— 而那正是 `bad_*` 期望的值，会被误判成"通过"。
> **环境故障用退出码 2 单独表示**（`audit_ruleset_content.py` 的用法错误、
> `architecture.sh` 的文件缺失也都用 2）。
> 铁律：**审计器的故障绝不能被计成一次成功的判负。**
>
> ⚠️ 阶段 2 的断言对象必须是**真实 profile** —— 阶段 1 的 fixture 是 DNS 面的合成配置
> （不含完整 DNS 段、不引用远程规则集），喂给 `architecture.sh` 会因为"缺少 DNS 键"而假红。
> **改完脚本或 profile 后手动跑一次。**

## 三条必须记住的判据

1. **`no-resolve` 与「域名体量足够的国内直连规则集」必须成对交付。**
   给 IP 规则补 `no-resolve` 会**同时**关掉「靠解析判 IP 归属」这条直连路径。
   只交一半 → 国内域名整片落 `FINAL → Proxy`。
2. **判据是「数域名条目」，不是看规则集名字，也不是看 README 标题。**
3. **审计通过 ≠ 配置可用。** 审计脚本只覆盖**静态可判定**的部分。
   拦截效果、误杀、节点可用性必须实测。
