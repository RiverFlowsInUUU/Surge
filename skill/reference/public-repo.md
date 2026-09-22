# 公开仓库的交付物与维护

> **何时读**：要更新模板、加新版本、或了解这个仓库为什么长这样。

---

## 1 · 交付物清单

```
surge/
├── README.md                    # 门面：快速开始 / 两份配置 / 原理 / 组结构 / 规则顺序 / 来源
├── CHANGELOG.md                 # 更新日志（Keep a Changelog，时间倒序）
├── LICENSE                      # MIT
├── .gitignore
├── profiles/                    # 4 份配置 = 2 种分工 × 2 种形态
│   ├── lazy.conf                # 懒人版（带注释）—— 改这份
│   ├── lazy.min.conf            # 懒人版（纯配置）—— 导入用
│   ├── routing.conf             # 分流版（带注释）—— 改这份
│   └── routing.min.conf         # 分流版（纯配置）—— 导入用
├── icons/                       # 26 个 PNG（本地，不跨项目引用）
├── docs/                        # 01–11 专题
├── DetailsReadme/
│   └── DetailsReadme.md         # 完整技术文档（18 节）
└── skill/
    ├── SKILL.md                 # 方法论主干
    ├── README.md                # 脚本用法
    ├── reference/               # 引用文件（含本文）
    ├── scripts/                 # 4 个审计脚本 + 1 个共享模块
    └── tests/                   # 6 阶段回归 + 4 个 fixture + architecture.sh + check_links.py
```

### 1.1 各层的职责边界

| 层 | 装在什么 | **不装什么** |
|:---|:---------|:-------------|
| `README.md` | 能用起来所需的一切 | 原理推导、逐行理由 |
| `docs/` | 每个专题一篇，**单一主题** | 跨主题的综合 |
| `DetailsReadme/` | 完整技术文档、原理推导、FAQ | 快速开始（README 有） |
| `skill/` | 方法论与脚本 | 面向使用者的说明 |
| `CHANGELOG.md` | 面向用户的变更 | **工作过程、内部重构** |

⚠️ **不要把工作过程倒进产品文档。** 判断一条要不要写进 `CHANGELOG` 只问：
**对使用者有影响吗？** 内部重构、仓库运维、行尾规范化 —— 用户无感，不进。

⚠️ 细节该进 `DetailsReadme` / `docs`，不进 README。

---

## 2 · 面向用户的文档规范

### 2.1 清单类内容用列表，不用表格

GitHub 上**表格宽度不可控**（`.markdown-body table` 是
`display:block; width:max-content`，CSS 会盖掉 HTML 的 `width` 属性）。

⇒ **清单类内容用列表。** 表格只留「短单元格 + 真正需要列对齐比较」的。

| 场景 | 用 |
|:-----|:---|
| 功能清单 / 特性列表 / 步骤 | 列表 |
| 两三个短值的对照（如某配置项 vs 默认值） | 表格 |
| 逐条规则清单（长文本） | 列表 |

⚠️ 长文本列**左对齐**（居中长文本换行后参差不齐），短枚举列居中。
删掉逐行重复的冗余列。

### 2.2 emoji 只放在条目最前面

```
✅ 正确：
- 🔒 零明文 DNS —— 引导 / 端点 / 劫持三处收口
- 🧩 不绑节点与订阅 —— 节点全为占位符

❌ 错误：
- 零明文 DNS 🔒 —— 引导 / 端点 🔒 / 劫持三处收口
```

**每条最前面一个，句中零个。** 同理适用所有列表型面向用户文档
（更新日志 / 功能清单 / 版本对比）。

### 2.3 相对链接必须能解析

`README.md` 里指向 `DetailsReadme/DetailsReadme.md#<anchor>` 的链接，
锚点必须真的存在。

**中英混排标题的 GitHub 锚点规则**：

| 标题 | 锚点 |
|:-----|:-----|
| `## 🚀 快速开始` | `#-快速开始` ← emoji 被剥掉，**它后面的空格变成前导 `-`** |
| `## 🔷 mihomo / OpenClash 配置` | `#-mihomo--openclash-配置` ← `/` 与全角标点被删，两侧空格各留一个 `-` |
| `## 2 · 防泄露原理：从机制到推导` | `#2--防泄露原理从机制到推导` |

⚠️ 改标题之后**必须重算锚点**并同步所有引用处。

---

## 3 · 文件组织

### 3.1 不设版本号，但可以有「分工」

这是**模板**不是软件。使用者关心的是「结构是什么样」，不是「补丁号」。

本仓库有**两份配置**：`lazy.conf`（懒人版）与 `routing.conf`（分流版）。
**这是分工关系，不是版本关系** —— 像"基础款"和"进阶款"，
而不是 v1 和 v2。选一份用，不要叠加。

⚠️ **判断标准**：两份是否在解决**不同的需求**？
- 是 → 可以共存（`lazy` 一个出口够用 / `routing` 要按应用按地区分流）
- 否、只是同一需求的两种取舍 → **那是版本分叉，必须消灭第二处**
  （这就是 `v0` 被删的原因，见 [`docs/07`](../../docs/07-文件版本沿革.md) §3）

想让你手头那份更轻，就在**它上面直接删**，不另开第三份。

### 3.2 两种形态

`.conf`（带注释，给人读）+ `.min.conf`（纯配置）。
**内容必须一致，只差注释** —— 由 `architecture.sh` 的 16 键一致性断言兜底
（②-a 管 lazy、②-b 管 routing、②-c 管两份之间）。

⚠️ `.min.conf` 里**必须保留 `# audit-waive:` 行** —— 那是有语义的注释。
⚠️ `.min.conf` 是**脚本生成的**，生成器会剥掉注释，这行要**手工补回**。

### 3.3 想加第三份配置的 6 条清单

**先问：这是新分工，还是老配置的另一种写法？** 后者不推荐。
确认是新分工后，必须同时满足：

1. **DNS 段与 `lazy.conf` 逐字节一致**（这是本仓库唯一的跨配置断言 ②-c；
   若确实必须不同，要说明理由并改测试）
2. 规则顺序符合铁律：白名单 → 黑名单 → 常规分流
3. `FINAL` 之前有域名体量足够的国内直连规则集
4. 所有 IP 类规则带 `no-resolve`
5. 节点全部占位化（`203.0.113.x` + `REPLACE_WITH_*`），订阅 token 用 `REPLACE_WITH_YOUR_TOKEN`
6. 若有豁免，`# audit-waive:` 写在文件里

这 6 条基本就是 `architecture.sh` 的全部断言。
**能过测试的才叫一份新配置，否则只是一个改坏了的副本。**

---

## 4 · 脱敏规则（公开模板的底线）

| 字段 | 占位形式 |
|:-----|:---------|
| 节点 IP | RFC 5737 文档段：`192.0.2.0/24` / `198.51.100.0/24` / `203.0.113.0/24` |
| 中转域名 | `cdn-relay.example.com`（RFC 2606 保留域） |
| 密码 / 用户名 | `REPLACE_WITH_YOUR_PASSWORD` / `REPLACE_WITH_USERNAME` |
| SNI | `REPLACE_WITH_YOUR_SNI` 或与 server 相同 |

检验由 `architecture.sh` 第 ① 组断言自动完成。

### 4.1 上传前的检查

```bash
bash skill/tests/architecture.sh     # 占位符纪律 + DNS 段一致性 + 规则顺序
```

⚠️ **`git push` 前必须跑一次。** 它会拦住：
- 非文档段 IPv4（真实节点 IP）
- 非 `REPLACE_WITH_*` 的凭据
- 不在允许清单的节点主机名
- 若干禁止出现的敏感子串（在 `FORBIDDEN_SUBSTRINGS` 里，**注释里也不许出现**）

### 4.2 全仓扫描（补一道）

`architecture.sh` 只扫 `profiles/*.conf`。改 `docs/` / `skill/` 之后要另扫一遍：

```bash
grep -rn -iE '<你的私有域名|你的密码片段|你的用户名>' . \
  --exclude-dir=.git --exclude-dir=icons
```

> ⚠️ **不要用 `grep -rn 'github'` 这类宽泛关键词** —— 仓库里的规则集 URL
> 全含 `githubusercontent`，几百条假阳性会把真命中淹没。

---

## 5 · 全部验证都在本地 —— 刻意不挂 CI

```bash
bash skill/tests/run.sh              # 6 阶段，15 个断言
SKIP_NET=1 bash skill/tests/run.sh   # 跳过联网阶段
```

**本仓库刻意不挂 CI / 任何自动化。** 理由：

- 这是个人模板仓库，不会有外部贡献者 —— "自动验 PR"价值接近于零
- 本地跑一次只要几十秒
- 少一个对外暴露的面就少一份事
- 用上面的本地命令可完整复现，**功能上没有任何损失**

⚠️ **文档里不要出现「可直接接进 CI」这类措辞。** 与"刻意不挂 CI"直接矛盾。
动「验证 / 测试 / 退出码」相关文档时顺手 grep 一遍 `CI` 清掉。

---

## 6 · 维护者自检流程

改完任何东西之后：

```
1. bash skill/tests/run.sh                      → 15 passed, 0 failed
2. python skill/scripts/check_surge_dns.py  profiles/lazy.conf     → exit 0
3. python skill/scripts/check_surge_dns.py  profiles/routing.conf  → exit 0
4. （改了地区关键词时）python skill/scripts/audit_region_filters.py profiles/routing.conf  → 9 passed
5. （改了规则集引用时）python skill/scripts/audit_ruleset_content.py  profiles/{lazy,routing}.conf
6. （改了规则时）      python skill/scripts/audit_routing_coverage.py profiles/{lazy,routing}.conf
7. （改了标题时）重算所有锚点，检查相对链接
8. （push 前）grep 一遍敏感串 + 跑一次 `architecture.sh`
```

> 📌 `run.sh` 已经把上面第 2–6 步全跑了一遍（含联网阶段）。
> 单独跑这几条只在**定位失败原因**时用。

### 6.1 相对链接检查

```bash
# 列出所有 markdown 里的相对链接目标，逐个确认存在
grep -rnoE '\]\(([^)#][^)]*)\)' --include='*.md' . | sed 's/.*](//' | sed 's/)$//' | sort -u
```

⚠️ 排除 `http` 开头的（外链）与纯 `#anchor`（页内跳转，单独验锚点）。

---

## 7 · 这个仓库最容易被改坏的地方

按风险排序：

| # | 位置 | 改坏的症状 | 守它的东西 |
|:-:|:-----|:-----------|:-----------|
| 1 | `[Proxy]` 段的节点（填成真实值） | 隐私泄露 | `architecture.sh` ① |
| 2 | `[Rule]` 的顺序（`direct.txt` 挪到 REJECT 前） | 广告拦截失效 | `architecture.sh` ③-b |
| 3 | IP 类规则的 `no-resolve`（删掉） | DNS 泄露 | `architecture.sh` ③-d + `check_12` |
| 4 | 只改 `.conf` 或只改 `.min.conf` 的 DNS 段 | 两份行为不一致；使用者拿到的与文档说的不一致 | `architecture.sh` ②（只覆盖 DNS 段） |
| 5 | `pre-matching` 的策略（改成策略组） | **Surge 拒绝加载** | `check_10` |
| 6 | `underlying-proxy` 指向的名字 | **Surge 拒绝加载** | `check_7` |
| 7 | `# audit-waive:` 行（删掉） | 从 2 waived 变 2 high | 无（靠"知道它是有语义的"） |

> ⚠️ **第 4 条的覆盖是部分的**：`architecture.sh` ② 只比对 **16 个 DNS 键**，
> `.min.conf` 里其余部分（规则、组、节点）改歪了不会被拦住。
> 第 7 条则完全没有自动化覆盖。
>
> 📌 这两条是**已知的测试盲区**，靠纪律补：改配置时两份一起改。
