# WF-01 Complete Branch Diagrams Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the incomplete WF-01 overview image with two replication-safe diagrams in which every condition has explicit success/failure destinations and every terminal message connects to N30.

**Architecture:** Split the workflow visualization into a draft/modify round and a confirm round. Keep N00–N30 as the single node contract, render both Mermaid blocks to separate PNG files, and validate source-level edge requirements before publishing.

**Tech Stack:** Markdown, Mermaid subset, Python/Pillow deterministic renderer, PowerShell verification, Git.

## Global Constraints

- N01 and N21 remain custom-SQL database nodes.
- N11, N13, and N19 use the platform's form-processing UI.
- Every brancher shown in a diagram must include both normal and failure/default destinations.
- N15, N16, N25, N26, N27, N28, and N29 must terminate at N30.
- Do not invent platform controls that are not supported by the supplied screenshots.

---

### Task 1: Add multi-diagram rendering support

**Files:**
- Modify: `scripts/render_workflow_diagrams.py`

**Interfaces:**
- Consumes: ordered Mermaid blocks and ordered `images/*.png` references in each workflow guide.
- Produces: one deterministic PNG per Mermaid/image pair.

- [x] **Step 1: Change the renderer to collect all Mermaid blocks and PNG references**

Use `re.findall` for both collections and reject missing or unequal pair counts.

- [x] **Step 2: Render every pair in document order**

Parse and render each Mermaid block to its corresponding image reference.

- [x] **Step 3: Run the renderer**

Run: `python scripts/render_workflow_diagrams.py`

Expected: exit 0 and two WF-01 image output lines.

### Task 2: Split WF-01 into two complete diagrams

**Files:**
- Modify: `docs/workflows/WF-01-user-profile.md`
- Create: `docs/workflows/images/WF-01-draft-round.png`
- Create: `docs/workflows/images/WF-01-confirm-round.png`

**Interfaces:**
- Consumes: node contract N00–N30.
- Produces: a complete draft/modify graph and a complete confirmation graph.

- [x] **Step 1: Write the draft/modify Mermaid graph**

Include N02 and N07 failure exits, N08 draft/modify/cancel/default exits, N10 true/false exits, N12 and N14 true/false exits, and N15/N16/N27/N28/N29 to N30.

- [x] **Step 2: Write the confirmation Mermaid graph**

Include N18, N20, N22, and N24 true/false exits and N25/N26/N27 to N30.

- [x] **Step 3: Remove the incomplete-main-graph disclaimer**

State that both diagrams are authoritative and must be reproduced exactly.

### Task 3: Verify the complete workflow contract

**Files:**
- Verify: `docs/workflows/WF-01-user-profile.md`
- Verify: `docs/workflows/images/WF-01-draft-round.png`
- Verify: `docs/workflows/images/WF-01-confirm-round.png`

**Interfaces:**
- Consumes: final Markdown and PNGs.
- Produces: evidence that required edges and artifacts exist.

- [x] **Step 1: Assert required Mermaid edges**

Check N12/N14 yes→N15 and no→N16; N20 yes→N21 and no→N26; N15/N16/N25/N26→N30.

- [x] **Step 2: Run repository formatting checks**

Run: `git diff --check`

Expected: exit 0.

- [x] **Step 3: Visually inspect both PNG files**

Expected: labels are readable, no branch appears to terminate in empty space, and no line visually enters the wrong node.

- [x] **Step 4: Commit and push**

Commit message: `docs: make wf01 branch diagrams complete`
