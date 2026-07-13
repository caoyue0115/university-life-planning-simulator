# All Workflows Platform-UI Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite WF-01 through WF-12 as platform-accurate, node-by-node build tutorials with explicit inputs, outputs, UI fields, complete branches, and non-dangling diagrams.

**Architecture:** Treat the user's screenshots as the platform UI contract. Standardize deterministic logic on branch nodes, Python `main(...)` code nodes, custom SQL reads, form add/update writes, model prompt role separation, description-driven variable extraction, and a shared end node. Preserve workflow-specific business logic while removing unsupported assumptions and replacing WF-05 iteration with one validated model call that generates and compares all 2～3 versions.

**Tech Stack:** Markdown, Mermaid, Python/Pillow diagram renderer, Python code-node snippets, PowerShell validation, Git.

## Global Constraints

- Code nodes support Python only and return a dict from `main(...)`.
- “决策” is model intent classification; deterministic comparisons use “分支器”.
- Database reads use “自定义 SQL”; writes use “表单处理数据” with “新增数据” or “更新数据”.
- Every node must state UI configuration, exact input source, output name, output type, and downstream consumer.
- Every model node must separate system prompt and user prompt.
- Every extractor output must include variable name, type, and extraction description.
- Every branch must include comparison type/value and destination; every default/failure path must terminate.
- Every message node must state inputs and answer content; every terminal message connects to the shared end node.
- End nodes use “返回设定格式配置的回答” and map an explicit `output` reference.
- Knowledge base nodes use `query`, Top K `3`, Score threshold `0.20`, forced invocation, and `results`.
- Iteration is not used because its inner-item mapping UI was not confirmed; WF-05 generates all selected versions in one model output and validates their count in Python.
- The total-workflow UI field names remain explicitly unverified until a “工作流” node screenshot is supplied.

---

### Task 1: Platform contract and validators

**Files:**
- Create: `docs/workflows/PLATFORM-UI-CONTRACT.md`
- Create: `scripts/validate_workflow_guides.py`

- [x] Document every confirmed node page and its exact fixed outputs.
- [x] Add validation for JavaScript remnants, Python syntax, Mermaid/image count mismatches, incomplete branchers, and dangling terminal messages.

### Task 2: WF-01 correction

**Files:**
- Modify: `docs/workflows/WF-01-user-profile.md`

- [x] Rewrite N03/N06/N09/N17/N23 as Python `main(...)` functions.
- [x] Align every declared output with returned dict keys and downstream references.
- [x] Re-run WF-01 diagram and edge validation.

### Task 3: WF-02 through WF-04

**Files:**
- Modify: `docs/workflows/WF-02-virtual-university.md`
- Modify: `docs/workflows/WF-03-survival-adventure.md`
- Modify: `docs/workflows/WF-04-path-recommendation.md`

- [x] Number every node and add exact UI/input/output tables.
- [x] Preserve cross-run state behavior and complete success/failure diagrams.
- [x] Configure WF-04 knowledge-base retrieval with confirmed fields.

### Task 4: WF-05 through WF-08

**Files:**
- Modify: `docs/workflows/WF-05-parallel-lives.md`
- Modify: `docs/workflows/WF-06-main-plan.md`
- Modify: `docs/workflows/WF-07-semester-tasks.md`
- Modify: `docs/workflows/WF-08-growth-review.md`

- [x] Replace WF-05 iteration with one validated model call for all selected routes.
- [x] Number and fully configure all nodes, branches, writes, messages, and ends.

### Task 5: WF-09 through WF-12

**Files:**
- Modify: `docs/workflows/WF-09-resume-entry.md`
- Modify: `docs/workflows/WF-10-decision-and-trial.md`
- Modify: `docs/workflows/WF-11-micro-habits.md`
- Modify: `docs/workflows/WF-12-session-recap.md`

- [x] Replace JavaScript with Python and model “决策” misuse with branchers.
- [x] Fully specify pending-confirm-write and failure paths.

### Task 6: Diagrams, integration, and release

**Files:**
- Modify: `docs/workflows/README.md`
- Modify/create: `docs/workflows/images/WF-*.png`

- [x] Render all Mermaid blocks and visually inspect each PNG.
- [x] Run guide validator and `git diff --check`.
- [x] State the verified 12-workflow integration contract without inventing unconfirmed “工作流” node UI fields.
- [ ] Commit and push the verified result.
