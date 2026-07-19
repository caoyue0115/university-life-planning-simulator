# WF-02～WF-12 Debug Guide Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 WF-02～WF-12 的上游依赖说明和调试指南扩写到新手可逐项复刻、可制造故障并可核验数据库结果的程度。

**Architecture:** 每个工作流文档保留现有节点配置和流程图，只重写末尾调试区域，并在调试区域前加入该工作流独立的前置准备。每个测试均使用“准备—输入—预期节点—数据库核验—恢复”的固定结构，但内容、节点编号和表名按工作流分别填写。

**Tech Stack:** Markdown、Mermaid、PowerShell、仓库现有 `scripts/validate_workflow_guides.py`。

## Global Constraints

- 只修改 `docs/workflows/WF-02-*.md` 至 `WF-12-*.md`，另增加本设计和计划文档。
- 不修改工作流业务节点逻辑、数据库模板或流程图连线。
- 不使用“参考 WF-01”“同上”代替具体操作。
- 所有测试使用测试 uid，不指导用户修改正式数据。
- SQL 失败测试必须写明恢复原表名；写入失败测试必须写明恢复必填字段或范围。
- 成功必须以写入和必要回读结果为依据，不以消息节点出现为唯一依据。

---

### Task 1: 扩写 WF-02～WF-04

**Files:**
- Modify: `docs/workflows/WF-02-virtual-university.md`
- Modify: `docs/workflows/WF-03-survival-adventure.md`
- Modify: `docs/workflows/WF-04-path-recommendation.md`

**Interfaces:**
- Consumes: WF-01 confirmed `profile_json`、WF-03 `assessment_id`、KB-01 命中结果。
- Produces: DB-02 状态、DB-03 评估与推荐的可核验调试记录。

- [ ] 为每份文档写明如何完成上游工作流并取得输入值。
- [ ] 为跨轮状态写明同一 uid、递增 request_time 和上一轮答案的使用方式。
- [ ] 写正常、空记录、无效回答、SQL 失败、写入失败、完成门禁和数据库核验测试。
- [ ] 检查所有测试节点编号与正文流程图一致。

### Task 2: 扩写 WF-05～WF-08

**Files:**
- Modify: `docs/workflows/WF-05-parallel-lives.md`
- Modify: `docs/workflows/WF-06-main-plan.md`
- Modify: `docs/workflows/WF-07-semester-tasks.md`
- Modify: `docs/workflows/WF-08-growth-review.md`

**Interfaces:**
- Consumes: WF-04 推荐、WF-05 comparison_id、WF-06 active plan_id、WF-07 任务证据。
- Produces: DB-04 比较、DB-05 主规划、DB-06 任务、DB-07 复盘记录。

- [ ] 写明从上游消息和数据库取得 comparison_id、plan_id、task_id 的具体位置。
- [ ] 覆盖草稿、确认、错误 token、取消、归档失败、更新失败和回读失败。
- [ ] 明确 WF-08 的 adjust/consider_switch 只是建议，不直接修改上游表。
- [ ] 为每个写操作给出数据库字段核验方法。

### Task 3: 扩写 WF-09～WF-12

**Files:**
- Modify: `docs/workflows/WF-09-resume-entry.md`
- Modify: `docs/workflows/WF-10-decision-and-trial.md`
- Modify: `docs/workflows/WF-11-micro-habits.md`
- Modify: `docs/workflows/WF-12-session-recap.md`

**Interfaces:**
- Consumes: 用户真实经历、试错 trial_id/token、生活记录原话、会话文本和成功写入清单。
- Produces: DB-08～DB-11 的可回读记录。

- [ ] 覆盖履历两轮确认、伪造安全出口、七天试错全生命周期、生活记录事实边界和会话复盘事实边界。
- [ ] 写明无强制上游工作流时应如何准备独立测试数据。
- [ ] 为 WF-12 给出 `successful_writes_json` 的正反例和获取规则。
- [ ] 为每份文档加入失败恢复和最终留证步骤。

### Task 4: 全量验证与发布

**Files:**
- Verify: `docs/workflows/WF-02-virtual-university.md` through `docs/workflows/WF-12-session-recap.md`

**Interfaces:**
- Consumes: 所有扩写后的工作流文档。
- Produces: 通过结构、节点、链接和 Git 差异检查的提交。

- [ ] 运行 `python scripts/validate_workflow_guides.py`，预期 `PASS: validated 12 workflow guides`。
- [ ] 检查每份文档都含调试前置、详细测试、数据库核验和恢复说明。
- [ ] 运行 `git diff --check`，预期无错误。
- [ ] 复核只包含本任务文件后提交并推送 `main`。
