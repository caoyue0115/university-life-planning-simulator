# WF-02–WF-12 WF-01-Standard Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite WF-02 through WF-12 into beginner-safe, screen-matched, node-by-node XFYUN build tutorials at the same operational detail level as WF-01.

**Architecture:** Every guide follows one fixed teaching sequence: outcome and prerequisites, non-crossing branch diagrams, node inventory, start inputs, one section per numbered node, exact right-panel configuration, terminal message and API output behavior, ordered debugging cases, and acceptance checklist. Shared platform controls use the UI labels confirmed by the user's screenshots; business-specific prompts, code, SQL, database fields, branches, and outputs remain inside each workflow file.

**Tech Stack:** Markdown, Mermaid, XFYUN workflow UI, restricted Python code nodes, database SQL/form-processing nodes.

## Global Constraints

- The reader is a first-time user and must not be told to infer a missing setting.
- Use only platform controls observed in the supplied screenshots: 开始、大模型、代码、问答节点、工作流、插件、MCP、RPA、知识库、知识库 Pro、长期记忆写入/检索、数据库、决策、分支器、迭代、Agent智能决策、变量存储器、变量提取器、文本处理节点、消息、结束.
- Decision-node instructions use Query + intent descriptions; deterministic Boolean/String comparisons use a branch node.
- Large-model nodes document model, every input name/reference, system prompt, user prompt, output name/type, and exception switch.
- Code nodes use no imports and declare every input and return key in the output panel.
- Database nodes state SQL versus form-processing mode, selected database/table, every input/condition/value, and fixed outputs `isSuccess`, `message`, `outputList`.
- Every branch is labelled and ends in a message plus a terminal/API result path; no dangling diagram edges.
- Each guide includes concrete debug input values, expected node route, expected result, database verification, and failure cases.
- Preserve the user's uncommitted WF-01 corrections and treat WF-01 as read-only reference for this rewrite.

---

### Task 1: Establish the reusable tutorial skeleton

**Files:**
- Reference: `docs/workflows/WF-01-user-profile.md`
- Modify: `docs/workflows/WF-02-virtual-university.md` through `docs/workflows/WF-12-session-recap.md`

- [x] Add the same ordered teaching sections to all eleven guides.
- [x] Add one exact platform-control reference block to every guide.
- [x] Remove vague phrases such as “按上图配置”“参考前文”“上游最终结果” where no literal value follows.

### Task 2: Rewrite WF-02 through WF-05

**Files:**
- Modify: `docs/workflows/WF-02-virtual-university.md`
- Modify: `docs/workflows/WF-03-survival-adventure.md`
- Modify: `docs/workflows/WF-04-path-recommendation.md`
- Modify: `docs/workflows/WF-05-parallel-lives.md`

- [x] Replace crossing diagrams with separate entry, continuation, success, and failure diagrams.
- [x] Add exact node panel instructions for every numbered node.
- [x] Add ordered multi-round debug cases and database verification.

### Task 3: Rewrite WF-06 through WF-09

**Files:**
- Modify: `docs/workflows/WF-06-main-plan.md`
- Modify: `docs/workflows/WF-07-semester-tasks.md`
- Modify: `docs/workflows/WF-08-growth-review.md`
- Modify: `docs/workflows/WF-09-resume-entry.md`

- [x] Expand every confirmation/pending/write/readback path into literal node settings.
- [x] Document every code input/output and every mandatory database field.
- [x] Add wrong-token, expired-pending, write-failure, and readback-mismatch tests.

### Task 4: Rewrite WF-10 through WF-12

**Files:**
- Modify: `docs/workflows/WF-10-decision-and-trial.md`
- Modify: `docs/workflows/WF-11-micro-habits.md`
- Modify: `docs/workflows/WF-12-session-recap.md`

- [x] Split multi-mode diagrams into independent readable subflows.
- [x] Document safety exits, confirmation gates, required table fields, and terminal results.
- [x] Add one debug case per mode plus safety and database failure cases.

### Task 5: Verify guide completeness and consistency

**Files:**
- Test: `docs/workflows/WF-02-virtual-university.md` through `docs/workflows/WF-12-session-recap.md`

- [x] Verify every node listed in each inventory has a detailed configuration subsection.
- [x] Verify every Mermaid node has a terminal route and every decision edge is labelled.
- [x] Extract and compile all Python code blocks; reject imports and undeclared `None` outputs.
- [x] Scan for placeholders and ambiguous instructions.
- [x] Review the complete diff without modifying unrelated files.
