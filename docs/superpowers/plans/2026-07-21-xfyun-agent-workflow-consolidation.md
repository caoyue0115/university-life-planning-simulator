# XFYUN Agent Workflow Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a GitHub review branch containing one publishable XFYUN MAIN workflow, nine single-parameter MCP business workflows, aligned database templates/contracts, rendered diagrams, and executable validation at WF-01's operational detail level.

**Architecture:** MAIN-00 is the only user-facing workflow and the only workflow allowed to use Agent intelligent decision. It stores an opaque per-conversation `user_key`, then dynamically calls WF-01 through WF-09 as same-account MCP tools; children accept one flat JSON String through `AGENT_USER_INPUT`, validate `user_key`, read their own state, and return a compact `result_json`. WF-01 through WF-04 preserve their existing business canvases where possible; old WF-05 through WF-12 are consolidated into five workflows without child-to-child calls.

**Tech Stack:** Markdown, Mermaid, PNG renderer using Pillow, Python validation scripts, XFYUN workflow UI, Python code nodes without imports, XFYUN database SQL/form-processing nodes, XLSX platform import templates.

## Global Constraints

- The final publishing surface is XFYUN Spark/Desk; no external API is part of the runtime.
- MAIN-00 may call multiple MCP tools in one turn; do not impose a product-level one-tool or two-tool cap.
- Platform hard limits remain 30 tools and 100 Agent reasoning rounds.
- Only MAIN-00 may call MCP tools; business workflows may not call tools or other workflows.
- Every business Start node has exactly one input: `AGENT_USER_INPUT:String`.
- Every variable extractor has exactly one `input:String`; combine multiple values in a text-processing node first.
- Every database table has business field `user_key:String`; platform field `uid` is never a business filter.
- The user never supplies JSON, user IDs, timestamps, record IDs, or confirmation tokens.
- Python code nodes contain no imports, return dictionaries, and declare every return key in the output panel.
- Boolean/enum conditions use branchers with explicit default/failure exits; natural-language classification alone may use model extraction/decision.
- Every terminal route produces compact `result_json:String` and reaches the End node.
- Guides must include exact UI values, prompts, SQL, code, output declarations, per-round inputs, expected routes, database checks, failure injection, and restoration.
- Preserve WF-01 through WF-04's core business behavior and node intent; adapter, extractor, routing, identity, database, and endpoint changes are authorized.
- Work only in branch `agent/rewrite-wf02-wf12-single-param-v2`; do not merge `main`.

---

### Task 1: Add executable repository invariants

**Files:**
- Modify: `scripts/validate_workflow_guides.py`
- Create: `scripts/validate_agent_architecture.py`
- Modify: `scripts/validate_database_templates_exact.py`

**Interfaces:**
- Consumes: Markdown under `docs/workflows`, database Markdown, XLSX import templates.
- Produces: exit code `0` only when the final nine-workflow architecture and database identity contract are consistent.

- [ ] **Step 1: Write the architecture validator before changing production documents**

Implement checks for exactly `WF-01` through `WF-09`, presence of `MAIN-00-agent-orchestrator.md`, absence of WF-10～WF-12 navigation, one Start parameter wording, one extractor input wording, forbidden business `uid`, forbidden user-facing token copy, child MCP nesting, required `result_json`, required default/failure branch wording, and required tutorial/debug sections.

- [ ] **Step 2: Run the new validator and verify RED**

Run:

```powershell
python scripts/validate_agent_architecture.py
```

Expected: non-zero exit with failures for missing MAIN-00, eleven legacy business guides, multi-parameter Start sections, business `uid`, external tokens, and missing compact MCP results.

- [ ] **Step 3: Strengthen existing Python/diagram validation**

Update `validate_workflow_guides.py` to scan the final nine files, compile every Python block, require Mermaid/PNG pairs, reject imports and dangling message routes, and validate at least two outgoing routes for every brancher.

- [ ] **Step 4: Add exact XLSX field assertions**

Update `validate_database_templates_exact.py` to parse sheet rows and require `user_key` in all eleven templates, require `DB-10-action-logs.xlsx`, reject `DB-10-habit-logs.xlsx`, and reject a business field named `uid`.

- [ ] **Step 5: Run current unaffected baseline checks**

Run:

```powershell
python scripts/validate_workflow_guides.py
python scripts/validate_database_templates_exact.py
```

Expected: the workflow check may fail only for newly enforced final-architecture rules; the exact package-structure part of the XLSX check still passes until field assertions report missing `user_key`.

- [ ] **Step 6: Commit the validation gate**

```powershell
git add scripts/validate_workflow_guides.py scripts/validate_agent_architecture.py scripts/validate_database_templates_exact.py
git commit -m "test: enforce consolidated agent contracts"
```

### Task 2: Rewrite shared architecture and MAIN-00 guide

**Files:**
- Create: `docs/workflows/MAIN-00-agent-orchestrator.md`
- Modify: `README.md`
- Modify: `docs/PRD.md`
- Modify: `docs/workflows/README.md`
- Modify: `docs/workflows/SHARED-CONTRACTS.md`
- Modify: `docs/workflows/PLATFORM-UI-CONTRACT.md`
- Modify: `docs/workflows/WORKFLOW-TEMPLATE.md`
- Create: `docs/workflows/images/MAIN-00-agent-orchestrator.png`

**Interfaces:**
- Consumes: official XFYUN Start, variable storage, Agent intelligent decision, MCP publish, extractor, text-processing, brancher, database, and End UI contracts.
- Produces: the authoritative natural-language entry, per-conversation identity protocol, MCP tool catalog, stop conditions, and exact MAIN canvas.

- [ ] **Step 1: Rewrite shared contracts around one String envelope**

Define `{"user_key":"uk_<32hex>","user_input":"..."}`, compact result fields, per-conversation recovery behavior, no account-level recovery claim, no external time/id/token, and append/version ordering using `create_time`.

- [ ] **Step 2: Correct the platform UI contract**

Record the exact one-input extractor UI, upstream-only references, database fixed outputs, variable-storage lifetime, Agent intelligent decision tool/round limits, MCP publishing path, non-streaming child output, and trace-log path. Clearly label official facts versus project rules.

- [ ] **Step 3: Write MAIN-00 node-by-node**

Document Start, variable storage get, key-presence normalization, key generation/validation/storage, Agent intelligent decision inputs, role/steps/query prompts, nine MCP tools, max rounds `100`, final output, failure paths, publish order, review wait, and end-to-end natural-language tests.

- [ ] **Step 4: Update navigation and PRD**

Replace the 12-workflow architecture with MAIN + nine business tools, WFB optional exploration, consolidated WF-05～WF-09, same-conversation recovery, and explicit platform limitations.

- [ ] **Step 5: Render MAIN diagram and run RED-to-GREEN architecture check for shared files**

Run:

```powershell
python scripts/render_workflow_diagrams.py
python scripts/validate_agent_architecture.py
```

Expected: MAIN/shared contract errors disappear; legacy workflow/database errors remain.

- [ ] **Step 6: Commit shared architecture**

```powershell
git add README.md docs/PRD.md docs/workflows/MAIN-00-agent-orchestrator.md docs/workflows/README.md docs/workflows/SHARED-CONTRACTS.md docs/workflows/PLATFORM-UI-CONTRACT.md docs/workflows/WORKFLOW-TEMPLATE.md docs/workflows/images/MAIN-00-agent-orchestrator.png
git commit -m "docs: add XFYUN MAIN MCP orchestration"
```

### Task 3: Migrate database contracts and eleven import templates

**Files:**
- Modify: `docs/database/README.md`
- Modify: `docs/database/DATABASE-SCHEMA.md`
- Modify: `docs/database/SQL-EXAMPLES.md`
- Modify: `docs/database/WF-DATABASE-MATRIX.md`
- Modify: `scripts/build_database_templates.mjs`
- Modify: `docs/database/import-templates/DB-01-user-profiles.xlsx`
- Modify: `docs/database/import-templates/DB-02-simulation-states.xlsx`
- Modify: `docs/database/import-templates/DB-03-route-assessments.xlsx`
- Modify: `docs/database/import-templates/DB-04-parallel-versions.xlsx`
- Modify: `docs/database/import-templates/DB-05-main-plans.xlsx`
- Modify: `docs/database/import-templates/DB-06-semester-tasks.xlsx`
- Modify: `docs/database/import-templates/DB-07-growth-reviews.xlsx`
- Modify: `docs/database/import-templates/DB-08-resume-entries.xlsx`
- Modify: `docs/database/import-templates/DB-09-decision-trials.xlsx`
- Delete: `docs/database/import-templates/DB-10-habit-logs.xlsx`
- Create: `docs/database/import-templates/DB-10-action-logs.xlsx`
- Modify: `docs/database/import-templates/DB-11-session-recaps.xlsx`

**Interfaces:**
- Consumes: shared `user_key`, final WF responsibilities, platform automatic `id/uid/create_time`.
- Produces: exact import templates and copyable SQL/form-processing mappings for WF-01～WF-09 and MAIN.

- [ ] **Step 1: Define exact rows in the generator**

Add `user_key:String` to all tables; remove external confirmation token and caller time fields; add deterministic version/status fields; replace `habit_logs` with `action_logs` containing `log_id`, `task_id`, `log_type`, `content_json`, `evidence_text`, `day_number`, `record_version`.

- [ ] **Step 2: Update the field dictionary and creation tutorial**

Explain that automatic `uid` is retained but never used as the business key, and every SQL/form range must explicitly use upstream `user_key` parsed before the database node.

- [ ] **Step 3: Rewrite SQL examples and WF matrix**

Use only `user_key` conditions, distinguish empty query from failure, use version/create-time ordering, and map merged workflows to all tables they read/write.

- [ ] **Step 4: Regenerate XLSX field rows while preserving the platform package**

Use the bundled spreadsheet dependency runtime to generate source rows, then repack them through the byte-preserving platform template process. Rename DB-10 to `DB-10-action-logs.xlsx`.

- [ ] **Step 5: Render and inspect all eleven templates**

Render each worksheet to PNG, confirm headers, field order, Chinese descriptions, `是/否` validations, no truncated columns, and correct DB-10 filename/content.

- [ ] **Step 6: Run exact template validation**

```powershell
python scripts/validate_database_templates_exact.py
python scripts/validate_agent_architecture.py
```

Expected: eleven XLSX templates pass package and field checks; database contract errors disappear.

- [ ] **Step 7: Commit database migration**

```powershell
git add docs/database scripts/build_database_templates.mjs scripts/validate_database_templates_exact.py
git commit -m "docs: migrate databases to internal user keys"
```

### Task 4: Minimally adapt WF-01 through WF-04

**Files:**
- Modify: `docs/workflows/WF-01-user-profile.md`
- Modify: `docs/workflows/WF-02-virtual-university.md`
- Modify: `docs/workflows/WF-03-survival-adventure.md`
- Modify: `docs/workflows/WF-04-path-recommendation.md`
- Modify: corresponding PNGs under `docs/workflows/images/`

**Interfaces:**
- Consumes: single envelope, `user_key`, DB-01～DB-03, KB-01, compact result contract.
- Produces: four MCP-ready guides that preserve their existing core behavior and can be built/tested independently.

- [ ] **Step 1: Adapt WF-01 entry and output without redesigning its business state machine**

Remove caller `request_time` and external token; parse `user_key/user_input`; use DB versions/create_time; keep draft→modify→confirm; add compact result builder and MCP publishing/debug section.

- [ ] **Step 2: Adapt WF-02 entry and fix the known extractor/branch defect**

Parse one envelope; read the confirmed profile internally; place a text-processing node before answer extraction; extractor references only its output; preserve one-event-per-round state; explicitly test both `has_pending` routes and both completion routes.

- [ ] **Step 3: Adapt WF-03 entry and fix the known extractor/branch defect**

Parse one envelope; read profile internally; join pending question plus user answer before extraction; explicitly test new-question, valid-answer, invalid-answer, next-question, and completed-assessment routes.

- [ ] **Step 4: Make WF-04 evidence-tolerant**

Read profile plus latest WF-02/WF-03 evidence internally. Continue when profile exists and at least one exploration source exists; mark missing evidence and lower confidence. Keep five-path KB grounding and flattened extractor output.

- [ ] **Step 5: Replace `workflow_finished` with compact MCP result output**

Every terminal route supplies status/reply/next_action/error_code to a common result builder and then the End node references `result_json:String`.

- [ ] **Step 6: Regenerate diagrams and run targeted validation**

```powershell
python scripts/render_workflow_diagrams.py
python scripts/validate_workflow_guides.py
python scripts/validate_agent_architecture.py
```

Expected: WF-01～WF-04 pass single-entry, extractor, user_key, branch, Python, diagram, tutorial, and result checks; only WF-05～WF-12 consolidation errors remain.

- [ ] **Step 7: Commit the preserved-canvas migration**

```powershell
git add docs/workflows/WF-01-user-profile.md docs/workflows/WF-02-virtual-university.md docs/workflows/WF-03-survival-adventure.md docs/workflows/WF-04-path-recommendation.md docs/workflows/images
git commit -m "docs: adapt WF01-WF04 for MCP orchestration"
```

### Task 5: Consolidate direction and execution workflows

**Files:**
- Delete: `docs/workflows/WF-05-parallel-lives.md`
- Delete: `docs/workflows/WF-06-main-plan.md`
- Delete: `docs/workflows/WF-07-semester-tasks.md`
- Create: `docs/workflows/WF-05-direction-and-main-plan.md`
- Create: `docs/workflows/WF-06-semester-actions.md`
- Replace/delete corresponding old PNGs and create new WF-05/WF-06 PNGs.

**Interfaces:**
- WF-05 consumes `user_key/user_input`, profile/recommendation records; produces direction comparisons and pending/active main-plan versions.
- WF-06 consumes `user_key/user_input`, active plan/tasks/action logs; produces task and evidence state updates.

- [ ] **Step 1: Write WF-05 as one bounded state machine**

Implement natural intent extraction for compare/draft/modify/confirm/cancel/show; read prerequisites internally; generate comparison and four-layer plan together; keep pending confirmation internal; activate only after explicit object-specific confirmation and readback.

- [ ] **Step 2: Write WF-06 around five actions**

Support `list/create/update/log/complete`; task type includes academic/project/habit/life; completion requires evidence; action logs append to DB-10; updates use deterministic branches; no standalone habit workflow.

- [ ] **Step 3: Add full per-round debug scripts**

Cover no profile, no recommendation, comparison draft, plan modification, ambiguous confirm, explicit confirm, DB failure/readback mismatch, empty task list, create/update/log/complete, missing evidence, and safety input.

- [ ] **Step 4: Generate diagrams and validate**

```powershell
python scripts/render_workflow_diagrams.py
python scripts/validate_workflow_guides.py
python scripts/validate_agent_architecture.py
```

- [ ] **Step 5: Commit WF-05/WF-06 consolidation**

```powershell
git add -A docs/workflows
git commit -m "docs: consolidate planning and action workflows"
```

### Task 6: Consolidate review, evidence, and decision workflows

**Files:**
- Delete: `docs/workflows/WF-08-growth-review.md`
- Delete: `docs/workflows/WF-09-resume-entry.md`
- Delete: `docs/workflows/WF-10-decision-and-trial.md`
- Delete: `docs/workflows/WF-11-micro-habits.md`
- Delete: `docs/workflows/WF-12-session-recap.md`
- Create: `docs/workflows/WF-07-review-and-recap.md`
- Create: `docs/workflows/WF-08-resume-evidence.md`
- Create: `docs/workflows/WF-09-decision-trial.md`
- Replace/delete corresponding old PNGs and create new WF-07/WF-08/WF-09 PNGs.

**Interfaces:**
- WF-07 reads main plan/tasks/action logs and writes evidence-grounded review plus compact session recap.
- WF-08 reads/writes resume entries through draft/modify/confirm without external token.
- WF-09 reads/writes decision trial state through analysis/create/confirm/log/review/stop.

- [ ] **Step 1: Write WF-07 review and recap**

Separate user facts, database evidence, and Agent inference; permit review with incomplete evidence but label gaps; write DB-07 and DB-11 only after validating the model output; return next recommended business action.

- [ ] **Step 2: Write WF-08 resume evidence**

Require real action/result/evidence, reject fabrication, keep pending and formal versions separate, support natural-language modify/confirm/cancel, and read back before claiming save.

- [ ] **Step 3: Write WF-09 decision trial**

Use one top-level mode extractor and deterministic router; allow immediate analysis without persistence; require explicit confirmation before active trial; append daily logs; require sufficient evidence for day-seven review; provide stop and high-risk exits.

- [ ] **Step 4: Add full debug lifecycles and restore steps**

For each workflow include exact natural-language rounds, expected nodes, expected table rows, forced SQL/model/write/readback failures, and the exact configuration to restore.

- [ ] **Step 5: Generate diagrams and reach GREEN**

```powershell
python scripts/render_workflow_diagrams.py
python scripts/validate_workflow_guides.py
python scripts/validate_database_templates_exact.py
python scripts/validate_agent_architecture.py
```

Expected: all final architecture checks pass with exactly nine WF guides.

- [ ] **Step 6: Commit WF-07～WF-09 consolidation**

```powershell
git add -A docs/workflows
git commit -m "docs: consolidate review evidence and trial workflows"
```

### Task 7: Final consistency, visual QA, and GitHub delivery

**Files:**
- Review: all tracked files changed from `40ca333`
- Modify only if verification finds a defect.

**Interfaces:**
- Consumes: all previous deliverables.
- Produces: a pushed review branch with clean status, passing validation evidence, and no merge to main.

- [ ] **Step 1: Run full fresh verification**

```powershell
python scripts/render_workflow_diagrams.py
python scripts/validate_workflow_guides.py
python scripts/validate_database_templates_exact.py
python scripts/validate_agent_architecture.py
git diff --check 40ca333..HEAD
```

Expected: every command exits `0` and reports exactly nine business guides plus eleven database templates.

- [ ] **Step 2: Inspect generated images and spreadsheets**

Open every new MAIN/WF PNG and every rendered XLSX preview; correct clipped labels, overlapping edges, missing headers, or unreadable column widths, then rerun the full verification.

- [ ] **Step 3: Critical requirements audit**

Search for forbidden patterns:

```powershell
rg -n "WHERE\s+uid|N00\s*/\s*uid|复制.*token|填写.*token|confirmation_token.*用户|request_time.*开始" README.md docs scripts
rg -n "WF-10|WF-11|WF-12|habit_logs" README.md docs scripts
```

Expected: no active instruction violates the final design; any historical spec/plan occurrence is explicitly historical and excluded by the architecture validator.

- [ ] **Step 4: Review commit history and status**

```powershell
git log --oneline --decorate 40ca333..HEAD
git status --short
```

Expected: staged/tracked changes are committed; only deliberately ignored temporary previews/caches may be untracked, and none are pushed.

- [ ] **Step 5: Push the isolated branch**

```powershell
git push -u origin agent/rewrite-wf02-wf12-single-param-v2
```

Expected: remote branch updated successfully; `main` remains at `40ca333` or any independently advanced remote state and is not merged by this task.

## Self-Review

- Spec coverage: every design section maps to Tasks 1–7, including identity, single input, MCP topology, database templates, preserved WF-01～WF-04, merged WF-05～WF-09, UI guides, diagrams, validation, commits, and push.
- Placeholder scan: no implementation step uses TBD/TODO; security-specific runtime values are generated in MAIN rather than committed.
- Type consistency: child input is always `AGENT_USER_INPUT:String`; parsed fields are `user_key:String` and `user_input:String`; tool output is always `result_json:String`; all database keys use `user_key:String`.

