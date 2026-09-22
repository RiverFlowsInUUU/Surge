# 更新日志

本文件按 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 规范编写。

---

## 2026-09-22

### 新增

- 🚫 **广告拦截补第二条清单 `AWAvenue-Ads-Rule`** —— 此前本仓只有 `Jinx`
  一条黑名单（姊妹仓 `Egern` 是**两条并列**），本次补齐，**两份配置的两种形态共 4 个文件**
  均已加入：`lazy.conf` / `lazy.min.conf` / `routing.conf` / `routing.min.conf`。
  - 📍 **位置**：紧跟 `Jinx` 那条之后、`AI.list` 之前 —— 与 Egern 的相对顺序一致
    （`白名单 → Jinx → AWAvenue → 应用分流`）。规则数 `13 → 14`（lazy）、`26 → 27`（routing）。
  - 🔧 **策略与参数同 Jinx**：`REJECT,pre-matching,extended-matching`。
    本仓的广告拦截走**字面量 `REJECT`** 而非 `AD` 组（理由见 `DetailsReadme` §13.3），
    所以这里同样不指向 `AD` 组。
  - ⚠️ **地址用的是 `...-RULE-SET.list`（965 条），不是 `...-Surge.list`（961 条）** ——
    后者是**裸域名**（`.8le8le.com`）对应 `DOMAIN-SET` 类型，与本仓消费的 `RULE-SET` 不匹配。
  - 📊 **收益按「净新增覆盖」量化**：AWAvenue 965 条中 **884 条**已被 Jinx 的后缀 / 通配
    规则覆盖，**净新增 81 条（8.4%）**。
  - ✅ **规则集本体已核对**：DOMAIN 949 / DOMAIN-SUFFIX 12 / DOMAIN-KEYWORD 4，
    **100% 域名类**，无 IP-CIDR / URL-REGEX / USER-AGENT ⇒ `pre-matching` 安全。
  - ⚠️ **顺序警告（已写进配置注释）**：AWAvenue 会命中白名单里的 **10 条**功能域
    （`jpush.cn` / `appcfg.v.qq.com` / `p.l.qq.com` / 微信登录 `apd-pcdnwx*` / 字节 `tnc3-*`）——
    白名单必须留在两条清单**之前**；两条清单也都不能落到 `direct.txt` / `GEOIP,CN` 之后。
  - 📝 同步文档读数与清单：`README`（规则顺序表 + 规则来源）、`DetailsReadme` §11.1 引用清单 /
    新增 §11.4、§14 规则逐条表、`docs/04` §4、`docs/07` §3.3、`docs/09`、`docs/10`、
    `docs/11` §1 / §5、`skill/reference/hardening-template.md`。

### 变更

- 🪟 **README 去掉「防泄露原理」整节 —— 门面只讲功能** —— 原 `## 🌐 防泄露原理` 是一张「出口 / 机制 / 堵法」三列表，属机制推导，不该出现在产品门面。改为 `## 🌐 DNS 防泄漏` 的**能力清单**：`hijack-dns` 接管硬编码明文 · 引导解析器显式写死 · IP 类规则全 `no-resolve` · DoH 固定直连不成环 · 走代理的域名由节点侧解析 · 审计读数 **0 high / 0 medium**、路由覆盖 **33/33**。只讲「得到什么」，不讲「为什么」。
  - 📌 与上面 §2.4.1 的**层级要求**同源，这次更严一档：连「原理」二字都不该出现在门面标题里。
  - ✅ 配置与 `[General]` 的 16 个 DNS 键一行未动；机制推导仍在 `DetailsReadme` 与 `docs/03` 的 12 项加固清单里。
- 📘 **公开仓规范补 §2.4.1「README 与 `DetailsReadme` 的分工」** —— 原 §2.4 只管「哪些题材不许进 README」，本次补上**层级**要求：合法的产品内容也要分层 —— `README` 只放「有什么 · 怎么用 · 防在哪」（地址 / 组表 / 规则顺序 / 出口结论表），机制推导、逐键说明、实测读数、已知取舍进 `DetailsReadme/`，README 用一行 `🔍` 指路（与 `Surge` / `Egern` 同一体例）。
  起因：`Clash` 仓 README 把「防泄露原理」写成 3 张表（三条出口 + 四个解析器键分工 + `respect-rules` 连带要求），用户判「DNS 防泄漏这块不需要说得那么详细吧……README 作为首页就应该介绍亮点，突出核心，而不是什么都堆上去」。
- 🏷️ **项目定位调整** —— 本仓交付的是**两份模板**（`lazy` / `routing`），
  **防 DNS 泄露是它们的特色，不是全部定位**。README 首页标题由「Surge 防 DNS 泄露配置」
  改为「Surge 配置模板」，副标题摆出两个模板、DNS 零泄露降为特色一句；
  badge 行把 `Profiles` / `Rules` 提到 `DNS` 之前。
- 📦 **仓库改名 `surge-anti-dns-leak` → `Surge`** —— 原名把定位写死在「防泄露」上；
  同日随后做了**大小写规范化**（`surge` → `Surge`），与官方写法一致。
  ⚠️ **旧链接不会失效**：GitHub 对改名仓保留 301 跳转，旧订阅地址与图标 URL 仍能下载
  （**实测**：raw 旧名 HTTP 200、jsDelivr 旧名 HTTP 200、`github.com` 旧名 301 → 新名）。
  仓内引用共改两轮 —— 首轮 88 处（图标 URL / 订阅地址 / 文档自引用 / 审计脚本 UA / 架构断言），
  本轮再改 **233 处**。姊妹项目 `egern-anti-dns-leak` 同步改名为 `Egern`。
  - 📌 **代码标识符与文件名保持小写**：`check_surge_dns.py` / `_surge_common.py` /
    `surge-profile-dns-hardening` / `surge-ads.list` 等一律未动，只改文本里的裸称呼。
- 📝 **GitHub 仓库描述同步修正** —— 改为「两个模板 + DNS 特色」的说法，
  并修掉两处过期数字（审计脚本 3 → **4** 个、回归断言 13 → **15** 条）。
- 🏷️ **规则集命名与上游对齐 + 过期读数修正** —— 上游 `Jinx` 已取消差集版，
  并把「完整版 / 白名单守卫」改名为「黑名单 / 白名单」。本仓同步：
  - 文档与配置注释里「白名单守卫」→「**白名单**」共 **28 处**（另 4 处散文泛指「守卫」一并理顺）
  - 广告规则集条数 `3891` → **`3889`**（上游剔除 2 条与自身白名单冲突的条目）；
    `ruleset-weight.md` 的示例读数随之修正 —— 分布 `{'DOMAIN-SUFFIX': 3820, 'DOMAIN-WILDCARD': 71}`
    → **`{'DOMAIN-SUFFIX': 3740, 'DOMAIN-WILDCARD': 149}`**
  - 核查确认本仓**从无差集版引用**（`delta` / `差集` 零命中），订阅地址不变
  - ⚠️ 本仓「完整版」指**带注释的 profile**（与 `.min` 相对），与上游那个同名词**无关**，未动

### 修复

- ✂️ **README 去掉一处「跨仓比对」句** —— 分流版段原写「26 组 / 27 条规则。先按应用分，
  再按地区分。**组序与 Egern v2.5 对齐。**」末句是在讲本仓参照谁排的序，
  读者不需要知道，且对「怎么用」零影响 —— 已删（组数与规则数、分流口径一字未动）。
  - 📌 **口径扩充进 `skill/reference/public-repo.md` §2.4**：README 禁入内容
    由三类增至四类，新增「**设计沿革 / 跨仓比对**」（实例：`与 Surge · Egern 同构`、
    `组序与 Egern v2.5 对齐`、`姐妹仓`）。**此类直接删** —— 前三类是「挪走」，
    判据必须仍能在 `DetailsReadme` / `CHANGELOG` 查到；跨仓比对没有需要保留的判据。
  - 🧭 **自查判据**：这句话对读者「**用它**」有没有帮助？没有就是自述。
  - 🔧 README 语气闸门新增三组正则（`同构|同源|对标|看齐|姐妹仓`、
    `<仓名>…对齐|一致|相同|同步`、`与 <仓名> …一致`）；负样本 5/5 全抓、正样本 0 误报。
- ✂️ **README 移除一段「归类辩护」—— 产品介绍不写改动过程** —— 上一轮修 `WeChat` 归类时，
  在组表下补了一段 📌 解释「`WeChat` 为什么不算开关」（位置分节 ≠ 功能归类、
  排在 `Airport` 之后 `AD` 之前、配置注释「③ 订阅槽位 + 开关」也是按位置切的…）。
  那是**改动记录**，不是产品说明：README 的读者只关心「哪个是开关」，
  不关心它当初为什么被写错。已整段移除 —— 判据本来就在 `DetailsReadme` §13.1 / §13.3、
  `docs/11` §2 与配置注释里，无需在 README 重复一遍。
  - 组表「开关」行备注：`手动，**不被规则引用**` → **`手动，独立于规则链路`** ——
    同一事实，换成使用者读得懂的性质，而不是内部判据。
  - 表内数据一行未动（仍 13 个应用组、只 `AD` 是开关）；配置与组序未动。
  - 📌 **口径入 `skill/reference/public-repo.md` §2.4**：README 不写归类辩护 / 评审对话 /
    内部断言名；自查词表「为什么…」「不算」「误标」「判据」「原写」「位置分节」。
  - 🔧 顺手修 `skill/tests/run.sh` 头部注释 `五阶段` → **`六阶段`**（实际列出 6 个阶段，
    与 `skill/README.md` 的「6 阶段」口径一致）。
- 🐛 **`DetailsReadme` §14 小节编号与物理顺序错位** —— 「为什么 Apple 规则集必须用
  `No_Resolve` 版」那节编号是 `§14.4`，却排在 `§14.1` 铁律**之前**。按物理顺序重编：
  `§14.1` Apple / `§14.2` 铁律 / `§14.3` IP 类规则 / `§14.4` `FINAL`；
  并把 §14 的规则逐条表里指向 Apple 的引用 `§14.4` 同步改指 `§14.1`（全仓仅此 1 处引用）。
- 🐛 **策略组归类：「开关」行把 `WeChat` 与 `AD` 并列属误标，已按功能拆开** ——
  `README` 的组表原写「🛑 开关 | `WeChat` · `AD`」，但本仓对「开关」的定义是
  **不被任何规则引用**（`DetailsReadme` §13.3）。判据一查就清楚：
  `WeChat` 被 `RULE-SET,…,WeChat.list,WeChat` 引用 ⇒ 它是**应用组**；只有 `AD` 是开关。
  那行的来源是把配置里 `# --- ③ 订阅槽位 + 开关 ---` 这个**位置分节**当成了功能分类 ——
  `WeChat` 排在订阅槽位与 `AD` 之间，只是随 Egern v2.5 的**组序**
  （由 `architecture.sh` ④ 断言守着），**配置与组序一律未动**。
  - `README`：应用 `12 组` → **`13 组`**（并注明 `Microsoft` · `WeChat` 首项 `DIRECT`）；
    「开关」行只留 `AD`；表下新增 📌 说明「位置分节 ≠ 功能归类」
  - `DetailsReadme` §13.1：② 应用补 `WeChat`（13 组）、③ 开关只留 `AD`，并加同一条位置说明
  - `docs/11` §2：③ 分节补 📌 对照表（被规则引用 = 应用组 / 不被引用 = 开关）
- 📝 **应用分流的条数口径统一为「规则行」**：`README` 规则顺序表 `13 条` → **`14 条`**、
  `docs/11` §5「拆成 13 条」→ **「拆成 14 条（13 个目标组）」**。
  本仓「条」= 规则行（同页表头写的即 27 条），而 `Anthropic.list` 与 `Claude.list`
  两行同指 `Claude` 组，此前是把「目标组数」当成了「规则数」。

---

## 2026-09-21

### 新增

- 📄 **一份懒人配置**：`profiles/lazy.conf`（带注释）与 `lazy.min.conf`（纯配置），
  内容一致、只差注释；3 组 / 13 条规则，含防 DNS 泄露结构 + 广告拦截 + AI 分流
- 🧭 **一份分流配置**：`profiles/routing.conf`（带注释）与 `routing.min.conf`（纯配置）；
  26 组 / 26 条规则，按**应用**分并在组内按**地区**再分
  （中国香港 / 美国 / 日本 / 中国台湾 / 新加坡 / 韩国 / 其它地区 + 低倍率池）
- 🧩 **12 个应用分流组**，取向与 Egern v2.5 逐组对齐：
  ChatGPT / Gemini / Claude / AI / Google / Spotify / YouTubeMusic / YouTube /
  GitHub / Microsoft / Telegram / Twitter
  - 🤖 AI 与开发类默认走代理（ChatGPT / Gemini / Spotify / YouTube / Telegram /
    Twitter / GitHub），Claude 默认落**中国台湾**组
  - 🪟 `Microsoft` 与 💚 `WeChat` **默认直连** —— 微信单列一组的意义是把它从兜底里
    摘出来，避免被 `Final` 送进代理
  - 🔎 `Google` 首项指向 `Gemini` 组 ⇒ 「Google 走 Gemini → Proxy」，与 Egern 一致
- 🍎 **Apple 服务直连**：在 Surge 内置 `SYSTEM` 之外补 `Apple_All_No_Resolve.list` ——
  `SYSTEM` 只覆盖激活 / 推送 / 配对核心主机，覆盖面明显不够
- 🌏 **地区组用正则筛节点**：`policy-regex-filter` 匹配节点名里的地区关键词；
  支持 emoji、中文、城市名与机场三字码
- 🧪 **四个审计脚本**：防泄露结构审计（12 项）、远程规则集内容审计、分流覆盖审计、
  地区组正则一致性审计；都是仅依赖 Python 标准库的单文件脚本
- ✅ **回归测试**：6 个阶段、15 个断言，含三个「期望判负」的坏配置样本，
  用于证明审计脚本真的有判别能力
- 📐 **架构不变量检查**：占位符纪律、订阅 token 纪律、两组形态 DNS 段一致性、
  lazy 与 routing 的 DNS 段一致性、规则顺序铁律
- 📚 **专题文档 11 篇**：DNS 怎么工作 / 为什么泄露 / 12 项加固清单 / 逐段讲解 /
  分流与 `no-resolve` 必须成对交付 / 实测数据 / 文件版本沿革 / 审计读数 /
  注意事项 / 图标与许可 / 分流版设计
- 📘 **完整技术文档**：18 节，含原理推导、逐键理由、已知取舍与 FAQ
- 🧩 **方法论包**：审计流程、加固模板、坑复盘、泄露定位、规则集轻重、公开仓库维护

### 变更

- 🔄 **测速端点保持原样**：`proxy-test-url` 沿用 `gstatic.com` 的境外 204 ——
  它是**性能探针**不是泄露通道，境外端点测出的延迟含国际段，对 `smart` 的选点决策
  更有意义。`internet-test-url`（连通性检测）用国内 204
- 🔒 **所有 IP 类规则加 `no-resolve`**：去掉「规则匹配时额外触发一次本地解析」，
  并把「IP 规则不触发解析」固化成配置约束。⚠️ 它**不是**泄露补丁 ——
  走代理时解析本就在代理服务器进行（官方 KB）；它的代价是必须同时保留
  域名型国内直连规则集，否则国内域名会整片走代理
- 🎛️ **`Proxy` / `AI` 组改用 `smart`**：按真实首字节延迟、TCP 重传、UDP 响应评分
- 🤖 **AI 流量独立成组**：出口与日常流量分开
- 🚫 **广告拦截启用 `pre-matching` + `extended-matching`**：拦截在
  DNS 查询与连接建立阶段生效
- 🛑 **保留 `AD` 组为独立手动开关**：拦截图走字面量策略，`AD` 组独立存在供人工干预
- 📥 **README 首页加「复制链接」区**：两份配置 × 两种形态共 4 条 raw 链接直接可复制，
  不再需要进 `profiles/` 目录逐个点开

### 修复

- 🐛 **补上国内直连的域名类规则集**：给 IP 规则加 `no-resolve` 会同时关闭
  「解析后判 IP 归属」这条直连通路，若不另配域名类规则集，国内网站会整片走代理
- 🐛 **补上 10 个漏掉的分流组**：`Gemini` / `Spotify` / `YouTubeMusic` / `YouTube` /
  `GitHub` / `Google` / `Microsoft` / `Telegram` / `Twitter` / `WeChat`。
  此前这些应用的流量**全部落到兜底 `Final → Proxy`**：能通，但"按应用分流"是空的，
  且 `Microsoft` / `WeChat` 的直连取向与 Egern v2.5 不一致
- 🐛 **Apple 规则集改用 `No_Resolve` 版**（两份配置都改）：`Apple_All.list` 里有 13 条
  `IP-CIDR` 没带 `no-resolve`，而该规则排在 IP 类规则之前且策略是 `DIRECT` ⇒
  每个未命中的域名经过这里都会被**强制解析一次**
- 🐛 **修正配置内关于广告组的说明**：`AD` 组是独立的手动开关，
  拦截动作走字面量策略，两者分层存在、职责不重叠
- 🐛 **移除空转参数**：`update-interval` 写在非订阅型策略组上不生效
- 🐛 **`[Proxy Group]` 段序改为与 Egern v2.5 逐位对齐**：
  ① 总入口 → ② 应用组 → ③ 订阅槽位 + 开关 → ④ 地区组 + 精选 → ⑤ 兜底。
  并把 `MAX` 放回 `Proxy` 的**首项**（Egern 的 `Proxy.policies[0]` 就是 `MAX`）。
  此前顺序与应用组写法都是自创的，与 Egern 不符
- 🐛 **应用组改为 `select, include-other-group="Proxy"`**：Egern 的应用组
  `policies` 只有 `[Proxy]` 一项（外加 `flatten: true`），此前"把地区组一个个列成成员"
  是读错 `flatten` 之后的自创写法
- 🐛 **审计器允许策略组前向引用**：Surge 官方文档的
  `include-other-group="A,B"` 示例本身就是引用后面才定义的组。此前审计器要求
  "被引用的组必须先定义"，会把合法的配置误判为 high
- 🐛 **把 `[Proxy Group]` 组顺序钉进回归测试**：此前**没有任何断言守着顺序**，
  改一个组就可能让顺序悄悄漂走而所有测试照旧全绿

### 说明

- 🔐 **本仓库是脱敏模板**。所有节点地址均为文档专用地址段，凭据均为占位符，
  导入前需替换为自己的节点
- 🔀 **`flatten` 的 Surge 对应物是 `include-other-group`**：Egern 的 `flatten: true`
  把**组名**替换成组内具体节点，Surge 用 `include-other-group` 达到同样效果（官方原文：
  "includes the resolved member policies from other policy groups"）。
  ⇒ 应用组因此写成 `select, include-other-group="Proxy"`，与 Egern 逐字对齐
- ⚠️ **Smart 组不能拿组名当子策略**：官方明文限制，需要 `smart` 自动选优的地方
  一律走 `include-other-group`
- ⚠️ **应用组没有自动故障转移**：Egern 的应用组是 `fallback` / `smart`（自动），
  Surge 的 `select` 是纯手动 ⇒ 本配置的应用组是「默认走 `Proxy` 全部节点 + 面板可改道」。
  想要自动选优就把某个组换成 `smart, include-other-group="Proxy"`
  （代价：面板上不能再手动挑节点）
- 🔁 **地区关键词有两份拷贝**：`Other Regions` 的负向断言把另外 6 个地区组的
  关键词逐字抄了一遍。Surge 的 filter 不支持引用变量，消灭不掉 ⇒ 新增
  `audit_region_filters.py` 逐词比对，并由回归测试守着它的判别力
- 🧪 **全部验证都在本地完成**，本仓库不挂 CI / 任何自动化
- ⚠️ 审计脚本只覆盖可静态判定的部分。拦截效果、误杀与节点可用性需自行实测
