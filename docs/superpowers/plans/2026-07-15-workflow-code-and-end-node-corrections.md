# Workflow Code and End-Node Corrections Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct WF-01 through WF-12 so every documented code node works in the observed restricted Python environment and every terminal branch reaches a correctly configured shared end node.

**Architecture:** Code nodes use no imports and return only explicitly declared primitive/Object/Array outputs. JSON structure is produced by large-model or variable-extractor nodes as Object/Array before code validation. Each message node renders the complete final JSON text in its answer-content field; all message nodes connect to one shared end node whose `output` references the message input value, with a fixed-text fallback documented when the platform cannot expose a message result.

**Tech Stack:** Markdown workflow guides, XFYUN workflow UI, restricted Python code nodes, database form-processing nodes.

## Global Constraints

- Match the configuration panels shown by the user on 2026-07-15.
- Code nodes must not use `import`, `None`, undeclared output keys, or unavailable libraries.
- Database nodes retain every required field shown by the selected table.
- Required time values come from start-node `request_time:String` and pass through code unchanged.
- Every branch must terminate at a message node and the shared end node; no dangling edges.
- End node uses answer mode `返回设定格式配置的回答`, one `output` parameter, streaming disabled, blank thinking content, and a non-empty answer-content field.

---

### Task 1: Correct WF-01 verified runtime nodes

**Files:**
- Modify: `docs/workflows/WF-01-user-profile.md`

- [x] Replace N03/N06/N09/N17/N23 with no-import implementations.
- [x] Restore required `updated_at` mappings through `request_time`.
- [x] Correct N13 required-field and output explanations.
- [x] Replace N30 instructions with the observed end-node configuration.

### Task 2: Correct WF-02 through WF-12 code and end nodes

**Files:**
- Modify: `docs/workflows/WF-02-virtual-university.md`
- Modify: `docs/workflows/WF-03-survival-adventure.md`
- Modify: `docs/workflows/WF-04-path-recommendation.md`
- Modify: `docs/workflows/WF-05-parallel-lives.md`
- Modify: `docs/workflows/WF-06-main-plan.md`
- Modify: `docs/workflows/WF-07-semester-tasks.md`
- Modify: `docs/workflows/WF-08-growth-review.md`
- Modify: `docs/workflows/WF-09-resume-entry.md`
- Modify: `docs/workflows/WF-10-decision-and-trial.md`
- Modify: `docs/workflows/WF-11-micro-habits.md`
- Modify: `docs/workflows/WF-12-session-recap.md`

- [x] Remove imports and align each function signature with the node input table.
- [x] Align every return key and type with the node output table.
- [x] Add an exact end-node configuration section and connect every message branch.

### Task 3: Static and executable verification

**Files:**
- Test: `docs/workflows/WF-01-user-profile.md`
- Test: `docs/workflows/WF-02-virtual-university.md` through `WF-12-session-recap.md`

- [x] Verify no Python block contains import statements or `None` returns.
- [x] Extract and compile every Python block.
- [x] Verify each guide contains the shared end-node settings and no dangling terminal description.
- [ ] Review the git diff, commit, and push the documentation update.
