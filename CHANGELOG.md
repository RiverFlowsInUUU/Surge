# 更新日志

本文件按 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 规范编写。

---

## 2026-09-21

### 新增

- 📄 **一份懒人配置**：`profiles/lazy.conf`（带注释）与 `lazy.min.conf`（纯配置），
  内容一致、只差注释；3 组 / 13 条规则，含防 DNS 泄露结构 + 广告拦截 + AI 分流
- 🧭 **一份分流配置**：`profiles/routing.conf`（带注释）与 `routing.min.conf`（纯配置）；
  26 组 / 26 条规则，按**应用**分并在组内按**地区**再分
  （中国香港 / 美国 / 日本 / 中国台湾 / 新加坡 / 韩国 / 其它地区 + 低倍率池）
- 🧩 **15 个应用分流组**，取向与 egern v2.5 逐组对齐：
  ChatGPT / Gemini / Claude / AI / Google / Spotify / YouTubeMusic / YouTube /
  Telegram / Twitter / GitHub / Microsoft / WeChat / Final
  - 🤖 AI 与开发类默认走代理（ChatGPT / Gemini / Spotify / YouTube / Telegram /
    Twitter / GitHub / Google），Claude 默认落**中国台湾**组
  - 🪟 `Microsoft` 与 💚 `WeChat` **默认直连** —— 微信单列一组的意义是把它从兜底里
    摘出来，避免被 `Final` 送进代理
  - 🔎 `Google` 首项指向 `Gemini` 组 ⇒ 「Google 走 Gemini → Proxy」，与 egern 一致
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
  且 `Microsoft` / `WeChat` 的直连取向与 egern v2.5 不一致
- 🐛 **Apple 规则集改用 `No_Resolve` 版**（两份配置都改）：`Apple_All.list` 里有 13 条
  `IP-CIDR` 没带 `no-resolve`，而该规则排在 IP 类规则之前且策略是 `DIRECT` ⇒
  每个未命中的域名经过这里都会被**强制解析一次**
- 🐛 **修正配置内关于广告组的说明**：`AD` 组是独立的手动开关，
  拦截动作走字面量策略，两者分层存在、职责不重叠
- 🐛 **移除空转参数**：`update-interval` 写在非订阅型策略组上不生效

### 说明

- 🔐 **本仓库是脱敏模板**。所有节点地址均为文档专用地址段，凭据均为占位符，
  导入前需替换为自己的节点
- 🔀 **`flatten` 的 Surge 对应物是 `include-other-group`**：egern 的 `flatten: true`
  把组名替换成组内具体节点，Surge 用 `include-other-group` 达到同样效果（官方原文：
  "includes the resolved member policies from other policy groups"）
- ⚠️ **Smart 组不能拿组名当子策略**：官方明文限制，所以「地区组作子节点」只用于
  `select` 组；需要 `smart` 自动选优的地方一律走 `include-other-group`
- 🔁 **地区关键词有两份拷贝**：`Other Regions` 的负向断言把另外 6 个地区组的
  关键词逐字抄了一遍。Surge 的 filter 不支持引用变量，消灭不掉 ⇒ 新增
  `audit_region_filters.py` 逐词比对，并由回归测试守着它的判别力
- 🧪 **全部验证都在本地完成**，本仓库不挂 CI / 任何自动化
- ⚠️ 审计脚本只覆盖可静态判定的部分。拦截效果、误杀与节点可用性需自行实测
