# 讯飞星辰工作流搭建指南 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 PRD 中 `WF-01` 至 `WF-12` 生成可直接照着讯飞星辰编辑器搭建的分文件指南，并明确说明如何把 12 个工作流整合为一个总业务流程。

**Architecture:** `SHARED-CONTRACTS.md` 定义跨工作流变量和状态规则，12 个独立文件分别描述一个可调试模块，`README.md` 负责总编排。总编排同时覆盖“总工作流通过工作流节点调用子流程”和“主 Agent 路由独立工作流”两种平台落地方式。

**Tech Stack:** Markdown、Mermaid/文本流程图、讯飞星辰 Agent 工作流编辑器、数据库、长期记忆、知识库与大模型节点。

## Global Constraints

- 只使用已从用户截图确认的讯飞星辰节点名称。
- 每份指南必须写明拖拽、连线、重命名、变量映射、提示词、调试和验收步骤。
- 平台字段或能力无法确认时，注明“以当前编辑器显示为准”并提供降级搭法。
- 每个复杂工作流均提供最小可运行版与完整业务版。
- 未经用户确认不得保存关键画像、主规划或重要履历。
- 写入失败不得声称保存成功。
- 最终总览必须明确说明如何把 12 个工作流整合为一个大的工作流。

---

### Task 1: 共享协议与标准模板

**Files:**
- Create: `docs/workflows/SHARED-CONTRACTS.md`
- Create: `docs/workflows/WORKFLOW-TEMPLATE.md`

**Interfaces:**
- Consumes: `docs/PRD.md` 与已批准的设计文档。
- Produces: 统一的开始输入、结束输出、JSON 包装、确认状态、错误状态和数据库共享键。

- [ ] **Step 1: 编写共享协议**

定义 `user_id`、`session_id`、`AGENT_USER_INPUT`、`status`、`reply`、`data`、`suggested_writes`、`next_action` 与 `error`；定义 `draft`、`awaiting_confirmation`、`confirmed`、`write_succeeded`、`write_failed` 状态语义。

- [ ] **Step 2: 编写可复制模板**

模板固定包含目标、准备、画布结构、节点表、逐步搭建、完整提示词、变量映射、调试、故障排查、验收和衔接逻辑。

- [ ] **Step 3: 校验共享字段**

Run: `rg -n "user_id|session_id|AGENT_USER_INPUT|suggested_writes|next_action|write_failed" docs/workflows/SHARED-CONTRACTS.md`

Expected: 每个字段至少出现一次，且确认与写入失败规则均有明确说明。

- [ ] **Step 4: 提交共享文档**

Run: `git add docs/workflows/SHARED-CONTRACTS.md docs/workflows/WORKFLOW-TEMPLATE.md && git commit -m "docs: add shared workflow contracts and template"`

Expected: 提交成功且只包含两份共享文档。

### Task 2: 首次体验工作流 WF-01 至 WF-04

**Files:**
- Create: `docs/workflows/WF-01-user-profile.md`
- Create: `docs/workflows/WF-02-virtual-university.md`
- Create: `docs/workflows/WF-03-survival-adventure.md`
- Create: `docs/workflows/WF-04-path-recommendation.md`

**Interfaces:**
- Consumes: `AGENT_USER_INPUT`、用户画像、试玩选择、场景题答案。
- Produces: `profile_json`、`simulation_summary_json`、`adventure_result_json`、`route_recommendation_json`。

- [ ] **Step 1: 编写 WF-01**

包含用户当前已搭建的 `开始 → 大模型 → 结束` 最小版，以及读取旧画像、提取字段、确认/修改分支、数据库或长期记忆写入、写入校验的完整版；明确开始节点输入选择 `AGENT_USER_INPUT`，结束节点输出选择大模型文本结果。

- [ ] **Step 2: 编写 WF-02**

用大模型、变量提取器、决策/分支器和变量存储器实现按剩余学年推进的试玩，说明如何保存 `simulation_state` 以支持中断续接，并禁止覆盖正式主规划。

- [ ] **Step 3: 编写 WF-03**

用问答节点或大模型逐题呈现场景，用变量存储器累计答案，使用迭代或分段调用控制题目轮次，最后输出竞争力与路径信号。

- [ ] **Step 4: 编写 WF-04**

读取画像和 WF-03 结果，结合知识库生成五路径分级推荐；用代码或变量提取器校验必须包含主路径、备选路径、依据和待验证假设。

- [ ] **Step 5: 校验四份指南结构**

Run: `rg -L "最小可运行版" docs/workflows/WF-0[1-4]-*.md; rg -L "验收清单" docs/workflows/WF-0[1-4]-*.md`

Expected: 两条命令均无输出。

- [ ] **Step 6: 提交首次体验指南**

Run: `git add docs/workflows/WF-0[1-4]-*.md && git commit -m "docs: add onboarding workflow build guides"`

Expected: 提交包含 WF-01 至 WF-04 四份文件。

### Task 3: 规划执行工作流 WF-05 至 WF-08

**Files:**
- Create: `docs/workflows/WF-05-parallel-lives.md`
- Create: `docs/workflows/WF-06-main-plan.md`
- Create: `docs/workflows/WF-07-semester-tasks.md`
- Create: `docs/workflows/WF-08-growth-review.md`

**Interfaces:**
- Consumes: `profile_json`、`route_recommendation_json`、用户选择、行动记录。
- Produces: `parallel_versions_json`、`main_plan_json`、`semester_tasks_json`、`growth_review_json`。

- [ ] **Step 1: 编写 WF-05**

说明使用迭代节点对 2～3 条路径使用相同初始条件生成版本，再由大模型按统一维度汇总比较；给出版本数量和字段完整性校验。

- [ ] **Step 2: 编写 WF-06**

说明如何从平行版本生成路径、学期、月度和每周四层规划，使用确认分支后再写数据库，并保留旧版本和切换原因。

- [ ] **Step 3: 编写 WF-07**

说明任务创建、查询、更新、完成和延期的意图分支，定义数据库读写映射和写入失败返回。

- [ ] **Step 4: 编写 WF-08**

说明如何读取主规划、近期任务和行为证据，判断继续、微调或建议切换；任何覆盖动作返回 WF-06 再次确认。

- [ ] **Step 5: 校验关键安全规则**

Run: `rg -n "确认|写入失败|不得.*覆盖|历史版本" docs/workflows/WF-0[5-8]-*.md`

Expected: WF-05 至 WF-08 均覆盖与自身职责相关的确认、失败或历史规则。

- [ ] **Step 6: 提交规划执行指南**

Run: `git add docs/workflows/WF-0[5-8]-*.md && git commit -m "docs: add planning workflow build guides"`

Expected: 提交包含 WF-05 至 WF-08 四份文件。

### Task 4: 长期陪伴工作流 WF-09 至 WF-12

**Files:**
- Create: `docs/workflows/WF-09-resume-entry.md`
- Create: `docs/workflows/WF-10-decision-and-trial.md`
- Create: `docs/workflows/WF-11-micro-habits.md`
- Create: `docs/workflows/WF-12-session-recap.md`

**Interfaces:**
- Consumes: 经历描述、决策问题、七天记录、习惯记录和会话变化。
- Produces: `resume_entry_json`、`decision_trial_json`、`habit_log_json`、`session_recap_json`。

- [ ] **Step 1: 编写 WF-09**

说明如何收集背景、目标、职责、行动、工具、结果、指标和证据位置，并在用户确认后写入履历数据库。

- [ ] **Step 2: 编写 WF-10**

使用决策或分支器区分即时决策分析与七天试错；定义试错状态、每日最小行动、投入上限和第七天复盘。

- [ ] **Step 3: 编写 WF-11**

说明习惯、记账和入门健身三类意图分支；加入休息/补签语义以及疼痛、疾病、极端节食和高风险动作的安全出口。

- [ ] **Step 4: 编写 WF-12**

说明如何生成用户复盘和 Agent 复盘，只提取新增或变化事实，写入后返回下次对话入口。

- [ ] **Step 5: 校验长期陪伴边界**

Run: `rg -n "用户确认|投入上限|专业求助|新增或变化" docs/workflows/WF-(09|10|11|12)-*.md`

Expected: 四个关键词分别出现在对应工作流中。

- [ ] **Step 6: 提交长期陪伴指南**

Run: `git add docs/workflows/WF-(09|10|11|12)-*.md && git commit -m "docs: add long-term companion workflow guides"`

Expected: 提交包含 WF-09 至 WF-12 四份文件。

### Task 5: 总编排与 12 工作流整合说明

**Files:**
- Create: `docs/workflows/README.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: 12 个工作流的统一输入输出和依赖关系。
- Produces: 一份可照做的总流程搭建顺序，以及两种可落地的整合架构。

- [ ] **Step 1: 编写支持子工作流调用时的总画布**

给出总工作流节点顺序：开始 → 读取共享状态 → Agent 智能决策/决策 → 分支器 → 对应“工作流”节点 → 统一结果处理 → 状态写入 → WF-12 → 结束；逐一列出 12 个工作流节点的输入输出映射。

- [ ] **Step 2: 编写不支持嵌套时的主 Agent 路由方案**

说明不创建巨型画布，由主 Agent 根据意图调用独立发布的 WF-01 至 WF-12，数据库/长期记忆作为共享状态层；给出主 Agent 路由提示词和工作流调用表。

- [ ] **Step 3: 编写端到端闭环**

明确首次闭环 `WF-01 → WF-02 → WF-03 → WF-04 → WF-05 → WF-06 → WF-07 → WF-12`，执行闭环 `WF-07 → WF-09 → WF-08 → WF-06/WF-07 → WF-12`，辅助入口 `WF-10/WF-11 → WF-08/WF-12`。

- [ ] **Step 4: 更新仓库入口**

在根 `README.md` 添加 PRD、总搭建指南、共享协议、模板和 12 个工作流文件的链接。

- [ ] **Step 5: 验证整合覆盖**

Run: `1..12 | ForEach-Object { $id = 'WF-{0:D2}' -f $_; if (-not (Select-String -Path docs/workflows/README.md -SimpleMatch $id)) { throw "Missing $id" } }`

Expected: 命令无错误，WF-01 至 WF-12 均在总编排中出现。

- [ ] **Step 6: 提交总编排说明**

Run: `git add README.md docs/workflows/README.md && git commit -m "docs: explain end-to-end workflow orchestration"`

Expected: 根入口和总编排指南同时提交。

### Task 6: 全量一致性验证与发布

**Files:**
- Verify: `docs/workflows/*.md`

**Interfaces:**
- Consumes: 全部指南文件。
- Produces: 无断链、无占位符、节点名称合规且已推送的 GitHub 文档集。

- [ ] **Step 1: 检查文件数量**

Run: `(Get-ChildItem docs/workflows -Filter '*.md').Count`

Expected: `15`。

- [ ] **Step 2: 检查占位符和格式错误**

Run: `rg -n "待.{0,1}定|待.{0,2}补写|稍.{0,2}补充|同.{0,1}上" docs/workflows; git diff --check`

Expected: `rg` 无输出，`git diff --check` 无输出。

- [ ] **Step 3: 检查平台节点用词**

核对所有画布图和节点表只使用设计文档确认的节点名称；产品逻辑词必须明确映射到代码、决策、分支器、变量提取器或文本处理节点。

- [ ] **Step 4: 检查链接**

Run: `rg -n "docs/workflows|WF-[0-9]{2}" README.md docs/workflows/README.md`

Expected: 根入口和总览包含完整导航。

- [ ] **Step 5: 推送 GitHub**

Run: `git status --short; git push origin main`

Expected: 推送成功，远端 `main` 包含全部指南提交。
