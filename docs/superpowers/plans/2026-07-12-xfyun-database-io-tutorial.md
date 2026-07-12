# 讯飞星辰数据库与输入输出教程 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为讯飞星辰平台生成 11 张共享业务表的可导入模板，并把 WF-01～WF-12 补成从平台入口开始、逐项配置数据库和节点输入输出的完整新手教程。

**Architecture:** 11 张表使用平台自动字段 `id`、`uid`、`create_time` 做主键、用户隔离和创建时间，导入文件只包含业务字段。数据库总教程、字段字典、SQL 示例和 WF 映射作为统一来源，各 WF 文件引用统一表并给出自身节点的逐屏配置。

**Tech Stack:** Markdown、讯飞星辰数据库与工作流、SQL、`@oai/artifact-tool`、XLSX。

## Global Constraints

- 每张表自动存在 `id`、`uid`、`create_time`，导入模板不得重复包含。
- 所有用户数据查询和写入必须使用系统 `uid` 隔离。
- 11 份 Excel 必须保留用户模板的 `Sheet1`、五列表头、表格结构和样式。
- JSON 保存为 `String`，时间保存为 `Time`，计数保存为 `Integer`。
- 每个 WF 必须说明从哪里点击、拖什么节点、输入值在哪里选、输出在哪里查看。
- 每个数据库节点必须区分 `isSuccess=false`、`isSuccess=true + outputList=[]` 和正常有记录。
- 字符串 SQL 参数写为 `'{{参数名}}'`，非字符串参数不加单引号。
- 正式写入必须检查 `isSuccess`，关键写入尽可能回读验证。

---

### Task 1: 数据库字段字典与生成清单

**Files:**
- Create: `docs/database/DATABASE-SCHEMA.md`
- Create: `docs/database/WF-DATABASE-MATRIX.md`

**Interfaces:**
- Consumes: PRD、共享契约、12 个 WF 和数据库教程设计。
- Produces: 11 张表的业务字段以及每个 WF 数据库节点到表/操作/输入/输出的唯一映射。

- [ ] **Step 1:** 为 DB-01～DB-11 定义英文表名、中文名称、简介和全部业务字段。
- [ ] **Step 2:** 每个字段写明类型、描述、默认值、必填、业务键、写入工作流和读取工作流。
- [ ] **Step 3:** 建立 WF-01～WF-12 的数据库节点矩阵，逐节点列出表、模式、参数和结果用途。
- [ ] **Step 4:** 验证字段中不存在 `id`、`uid`、`create_time` 重复定义，所有字段名为 snake_case。

Run: `rg -n "DB-01|DB-02|DB-03|DB-04|DB-05|DB-06|DB-07|DB-08|DB-09|DB-10|DB-11" docs/database/DATABASE-SCHEMA.md`

Expected: DB-01～DB-11 均出现。

### Task 2: 生成 11 份数据库导入模板

**Files:**
- Create: `scripts/build_database_templates.mjs`
- Create: `docs/database/import-templates/DB-01-user-profiles.xlsx`
- Create: `docs/database/import-templates/DB-02-simulation-states.xlsx`
- Create: `docs/database/import-templates/DB-03-route-assessments.xlsx`
- Create: `docs/database/import-templates/DB-04-parallel-versions.xlsx`
- Create: `docs/database/import-templates/DB-05-main-plans.xlsx`
- Create: `docs/database/import-templates/DB-06-semester-tasks.xlsx`
- Create: `docs/database/import-templates/DB-07-growth-reviews.xlsx`
- Create: `docs/database/import-templates/DB-08-resume-entries.xlsx`
- Create: `docs/database/import-templates/DB-09-decision-trials.xlsx`
- Create: `docs/database/import-templates/DB-10-habit-logs.xlsx`
- Create: `docs/database/import-templates/DB-11-session-recaps.xlsx`

**Interfaces:**
- Consumes: `D:/DB_TABLE_导入模板.xlsx` 和 Task 1 字段字典。
- Produces: 可由讯飞星辰“导入字段”直接上传的 11 份 XLSX。

- [ ] **Step 1:** 使用 artifact-tool 导入用户模板并读取表头、表格和样式。
- [ ] **Step 2:** 为每张表复制模板并填入对应业务字段，不加入系统默认三字段。
- [ ] **Step 3:** 调整列宽、自动换行和行高，保持原模板表头样式。
- [ ] **Step 4:** 导出 11 份 XLSX 到 `docs/database/import-templates/`。
- [ ] **Step 5:** 检查每份文件的 Sheet、表头、字段类型、必填值和重复字段。
- [ ] **Step 6:** 渲染 11 个 Sheet1 并逐一检查可读性。

### Task 3: 数据库逐屏教程与 SQL 示例

**Files:**
- Create: `docs/database/README.md`
- Create: `docs/database/SQL-EXAMPLES.md`

**Interfaces:**
- Consumes: Task 1 字段字典和 Task 2 导入文件。
- Produces: 从平台数据库入口到建表、导入、保存、检查和 SQL 节点配置的完整教程。

- [ ] **Step 1:** 写从数据库列表进入“新建数据表”的点击路径。
- [ ] **Step 2:** 解释表名称、表简介和自动字段 `id/uid/create_time`，说明不能删除且无需导入。
- [ ] **Step 3:** 逐表列出名称、简介和应上传的 XLSX 链接。
- [ ] **Step 4:** 写“导入字段”选择文件、检查预览、补字段和保存的步骤。
- [ ] **Step 5:** 写数据库节点的“表单处理数据”与“自定义SQL”选择规则。
- [ ] **Step 6:** 提供按 `uid` 查询、插入、更新、读取最新记录和回读验证的可复制 SQL。
- [ ] **Step 7:** 解释输入参数引用、字符串引号、`isSuccess/message/outputList` 和空结果。

### Task 4: WF-01～WF-04 数据库与输入输出教程

**Files:**
- Modify: `docs/workflows/WF-01-user-profile.md`
- Modify: `docs/workflows/WF-02-virtual-university.md`
- Modify: `docs/workflows/WF-03-survival-adventure.md`
- Modify: `docs/workflows/WF-04-path-recommendation.md`

- [ ] **Step 1:** 每份增加依赖表、导入文件和上游准备。
- [ ] **Step 2:** 增加开始节点输入表，说明 `AGENT_USER_INPUT`、`uid` 和调试值来源。
- [ ] **Step 3:** 为每个数据库节点逐项写模式、表、参数、引用来源、SQL、输出和三种结果分支。
- [ ] **Step 4:** 增加全节点输入输出映射和结束节点 `result_json` 选择方法。
- [ ] **Step 5:** 增加从点击“调试”开始的成功、空数据和失败测试。

### Task 5: WF-05～WF-08 数据库与输入输出教程

**Files:**
- Modify: `docs/workflows/WF-05-parallel-lives.md`
- Modify: `docs/workflows/WF-06-main-plan.md`
- Modify: `docs/workflows/WF-07-semester-tasks.md`
- Modify: `docs/workflows/WF-08-growth-review.md`

- [ ] **Step 1:** 补齐依赖表、开始输入、数据库节点和 SQL。
- [ ] **Step 2:** 明确平行版本、主规划历史、待确认草稿、任务变更和成长复盘如何通过 `uid + 业务键` 查询。
- [ ] **Step 3:** 明确历史写入、正式写入和回读验证的先后顺序。
- [ ] **Step 4:** 补齐节点映射、结束输出和逐项调试教程。

### Task 6: WF-09～WF-12 数据库与输入输出教程

**Files:**
- Modify: `docs/workflows/WF-09-resume-entry.md`
- Modify: `docs/workflows/WF-10-decision-and-trial.md`
- Modify: `docs/workflows/WF-11-micro-habits.md`
- Modify: `docs/workflows/WF-12-session-recap.md`

- [ ] **Step 1:** 补齐履历、试错、微习惯和会话复盘所需表及开始输入。
- [ ] **Step 2:** 明确 pending 草稿、确认令牌、每日记录和会话增量的查询/写入配置。
- [ ] **Step 3:** 补齐安全出口、写入失败、空查询、节点映射和结束输出。
- [ ] **Step 4:** 补齐成功、确认、失败及下一次会话续接的调试步骤。

### Task 7: 总编排和仓库导航

**Files:**
- Modify: `docs/workflows/README.md`
- Modify: `docs/workflows/SHARED-CONTRACTS.md`
- Modify: `README.md`

- [ ] **Step 1:** 在总编排中解释主 Agent 如何传递系统 `uid`、`AGENT_USER_INPUT` 和业务键。
- [ ] **Step 2:** 在共享契约中把旧 `user_id` 表述统一迁移为平台 `uid`，保留兼容说明。
- [ ] **Step 3:** 从根 README 添加数据库教程、字段字典、SQL、WF 映射和 11 个导入模板入口。

### Task 8: 全量验证与发布

**Files:**
- Verify: `docs/database/**/*`
- Verify: `docs/workflows/*.md`

- [ ] **Step 1:** 验证 11 份 XLSX 均可重新导入，表头和字段与 schema 一致。
- [ ] **Step 2:** 验证 11 份模板均不包含 `id`、`uid`、`create_time`。
- [ ] **Step 3:** 验证 12 个 WF 均包含数据库表、开始输入、数据库配置、节点映射、结束输出和调试章节。
- [ ] **Step 4:** 扫描 SQL，确认所有用户数据条件包含 `uid`。
- [ ] **Step 5:** 检查 Markdown 链接、占位符和 Git 空白错误。
- [ ] **Step 6:** 提交、推送并确认远端 `main` 与本地提交一致。
