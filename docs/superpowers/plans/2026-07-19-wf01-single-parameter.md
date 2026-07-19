# WF-01 Single-Parameter Entry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert WF-01 into a one-input workflow whose only start parameter is `AGENT_USER_INPUT:String`, with a dedicated parser module that safely exposes the business fields required by all existing nodes.

**Architecture:** Keep N01 through N30 unchanged in number and responsibility. Insert N00A parser, N00B validation branch, and N00C input-error message between the start node and N01; downstream nodes consume N00A outputs instead of extra start parameters. Re-render the workflow images and validate that no old multi-parameter references remain in the WF-01 guide.

**Tech Stack:** Markdown, Mermaid, Python code embedded in the Xfyun code-node tutorial, repository Python documentation validators and diagram renderer.

## Global Constraints

- N00 must expose exactly one input: `AGENT_USER_INPUT:String`.
- The inner payload must be a JSON object containing non-empty String fields `uid` and `user_input`.
- `confirmation_token` is optional and normalizes to an empty String.
- `request_time` is required inside the single JSON String and must use `YYYY-MM-DD HH:mm:ss`; this supplies the database's required Time field without unsupported imports.
- Parser failures must return six declared outputs and route to N00C without executing N01.
- Existing nodes N01 through N30 keep their current numbers.
- All branches, including invalid entry input, must terminate at N30.
- The guide must match the Xfyun page controls previously confirmed by the user.

---

### Task 1: Add the one-parameter entry module to the WF-01 guide

**Files:**
- Modify: `docs/workflows/WF-01-user-profile.md`
- Modify: `docs/workflows/SHARED-CONTRACTS.md`
- Modify: `docs/workflows/README.md`

**Interfaces:**
- Consumes: `N00/AGENT_USER_INPUT:String` containing the inner JSON object as text.
- Produces: `N00A/uid:String`, `user_input:String`, `confirmation_token:String`, `request_time:String`, `input_valid:Boolean`, and `input_error:String`.

- [ ] **Step 1: Replace the current start-node contract**

Document N00 with only:

```text
AGENT_USER_INPUT | String | 包含 uid、user_input、confirmation_token、request_time 的 JSON 字符串 | 是
```

Delete the N00 output declarations for `uid`, `confirmation_token`, and `request_time`.

- [ ] **Step 2: Document N00A with exact Xfyun fields and executable code**

Use one input row:

```text
raw_input | 引用 | N00 / AGENT_USER_INPUT
```

Use this code:

```python
def skip_spaces(text, index):
    while index < len(text) and text[index] in " \t\r\n":
        index += 1
    return index

def parse_json_string(text, index):
    if index >= len(text) or text[index] != '"':
        raise ValueError("JSON 的键和值都必须使用双引号")
    index += 1
    chars = []
    escapes = {'"':'"', '\\':'\\', '/':'/', 'b':'\b', 'f':'\f', 'n':'\n', 'r':'\r', 't':'\t'}
    while index < len(text):
        char = text[index]
        if char == '"':
            return "".join(chars), index + 1
        if char == '\\':
            index += 1
            if index >= len(text):
                raise ValueError("JSON 转义字符不完整")
            escaped = text[index]
            if escaped == 'u':
                code = text[index + 1:index + 5]
                if len(code) != 4:
                    raise ValueError("JSON Unicode 转义不完整")
                try:
                    chars.append(chr(int(code, 16)))
                except:
                    raise ValueError("JSON Unicode 转义无效")
                index += 5
                continue
            if escaped not in escapes:
                raise ValueError("JSON 包含不支持的转义字符")
            chars.append(escapes[escaped])
            index += 1
            continue
        if ord(char) < 32:
            raise ValueError("JSON 字符串包含控制字符")
        chars.append(char)
        index += 1
    raise ValueError("JSON 字符串缺少结束双引号")

def parse_flat_string_object(raw_input):
    if not isinstance(raw_input, str) or raw_input.strip() == "":
        raise ValueError("AGENT_USER_INPUT 不能为空")
    text = raw_input
    index = skip_spaces(text, 0)
    if index >= len(text) or text[index] != '{':
        raise ValueError("JSON 顶层必须是对象")
    index = skip_spaces(text, index + 1)
    result = {}
    if index < len(text) and text[index] == '}':
        index = skip_spaces(text, index + 1)
        if index != len(text):
            raise ValueError("JSON 对象结束后不能有其他内容")
        return result
    while index < len(text):
        key, index = parse_json_string(text, index)
        index = skip_spaces(text, index)
        if index >= len(text) or text[index] != ':':
            raise ValueError("JSON 键后缺少冒号")
        index = skip_spaces(text, index + 1)
        value, index = parse_json_string(text, index)
        result[key] = value
        index = skip_spaces(text, index)
        if index < len(text) and text[index] == ',':
            index = skip_spaces(text, index + 1)
            continue
        if index < len(text) and text[index] == '}':
            index = skip_spaces(text, index + 1)
            if index != len(text):
                raise ValueError("JSON 对象结束后不能有其他内容")
            return result
        raise ValueError("JSON 字段之间缺少逗号或对象缺少结束花括号")
    raise ValueError("JSON 对象缺少结束花括号")

def main(raw_input):
    uid = ""
    user_input = ""
    confirmation_token = ""
    request_time = ""
    error = ""
    try:
        payload = parse_flat_string_object(raw_input)
        uid_value = payload.get("uid", "")
        message_value = payload.get("user_input", "")
        token_value = payload.get("confirmation_token", "")
        time_value = payload.get("request_time", "")
        uid = uid_value.strip() if isinstance(uid_value, str) else ""
        user_input = message_value.strip() if isinstance(message_value, str) else ""
        confirmation_token = token_value.strip() if isinstance(token_value, str) else ""
        request_time = time_value.strip() if isinstance(time_value, str) else ""
        if uid == "":
            raise ValueError("缺少非空字符串字段 uid")
        if user_input == "":
            raise ValueError("缺少非空字符串字段 user_input")
        valid_time = (
            len(request_time) == 19
            and request_time[4] == '-' and request_time[7] == '-'
            and request_time[10] == ' '
            and request_time[13] == ':' and request_time[16] == ':'
            and (request_time[0:4] + request_time[5:7] + request_time[8:10]
                 + request_time[11:13] + request_time[14:16]
                 + request_time[17:19]).isdigit()
        )
        if not valid_time:
            raise ValueError("缺少 request_time，或格式不是 YYYY-MM-DD HH:mm:ss")
    except Exception as exc:
        error = str(exc) if str(exc) != "" else "单参数 JSON 解析失败"
    return {
        "uid": uid,
        "user_input": user_input,
        "confirmation_token": confirmation_token,
        "request_time": request_time,
        "input_valid": error == "",
        "input_error": error,
    }
```

Declare all six outputs with the exact names and types in the global constraints.

- [ ] **Step 3: Document N00B and N00C**

Set N00B to reference `N00A/input_valid`, compare it with the fixed Boolean value `true`, route true to N01, and route the default/false branch to N00C. Configure N00C with input `input_error=N00A/input_error`, streaming disabled, and an answer that explains the required JSON fields before connecting it to N30.

- [ ] **Step 4: Update node inventory and wiring summaries**

Increase code-node count by one, branch-node count by one, and message-node count by one. Add N00A, N00B, and N00C to the drag-and-name table without changing N01 through N30.

- [ ] **Step 5: Run entry-contract checks**

Run:

```powershell
rg -n "N00A|N00B|N00C|input_valid|input_error" docs/workflows/WF-01-user-profile.md
```

Expected: all three nodes and all parser outputs appear in the start-node, flow, inventory, and testing sections.

---

### Task 2: Rewire every downstream WF-01 reference

**Files:**
- Modify: `docs/workflows/WF-01-user-profile.md`

**Interfaces:**
- Consumes: the six N00A outputs defined in Task 1.
- Produces: an internally consistent tutorial in which N01, N04, N09, N11, N13, N17, N19, and N21 no longer depend on removed N00 fields.

- [ ] **Step 1: Update identity references**

Change each database/code reference as follows:

```text
N01 uid                 = N00A / uid
N09 uid                 = N00A / uid
N11 uid comparison      = N00A / uid
N13 uid inserted value  = N00A / uid
N19 uid comparison      = N00A / uid
N21 uid                 = N00A / uid
```

N13 must explicitly document `uid | 引用 | N00A / uid`; do not leave it conditional on whether the page displays the field.

- [ ] **Step 2: Update model-message references**

Rename the N04 input parameter from `AGENT_USER_INPUT` to `user_input`, set its source to `N00A/user_input`, and change the user prompt interpolation to:

```text
用户本轮输入：{{user_input}}
```

- [ ] **Step 3: Update token and time references**

Use:

```text
N09 request_time       = N00A / request_time
N17 incoming_token     = N00A / confirmation_token
N17 request_time       = N00A / request_time
```

- [ ] **Step 4: Prove removed references are absent**

Run this PowerShell check, which removes the explicit old-to-new migration table before searching active configuration text:

```powershell
$text = Get-Content -Raw docs/workflows/WF-01-user-profile.md
$active = [regex]::Replace($text, '### 5\.5[\s\S]*?(?=\r?\n## 6\.)', '')
if ($active -match 'N00\s*/\s*(uid|confirmation_token|request_time)|N00\.(uid|confirmation_token|request_time)') { throw 'active config still references removed N00 fields' }
```

Expected: no exception. Exact old references remain only in section 5.5 so the user can migrate an already-built canvas.

- [ ] **Step 5: Check all N00A consumers**

Run:

```powershell
rg -n "N00A\s*/|N00A\." docs/workflows/WF-01-user-profile.md
```

Expected: references appear for N01, N04, N09, N11, N13, N17, N19, N21, N00B, and N00C.

- [ ] **Step 6: Update shared and MAIN-facing contracts**

Add an explicit WF-01 exception to `SHARED-CONTRACTS.md`: WF-01 only exposes `AGENT_USER_INPUT:String`, and the value is the serialized inner envelope. Add the same rule beside `调用_WF01_用户建档` in `README.md`, and state that WF-02 through WF-12 require their own later migrations before the complete set can be treated as internally callable single-parameter workflows.

---

### Task 3: Update diagrams, test cases, and API/MAIN examples

**Files:**
- Modify: `docs/workflows/WF-01-user-profile.md`
- Modify: `docs/workflows/SHARED-CONTRACTS.md`
- Modify: `docs/workflows/README.md`
- Modify: `docs/workflows/images/WF-01-draft-round.png`
- Verify: `docs/workflows/images/WF-01-confirm-round.png`

**Interfaces:**
- Consumes: the entry and downstream contracts from Tasks 1 and 2.
- Produces: diagrams and copy-ready tests that expose only `AGENT_USER_INPUT` externally.

- [ ] **Step 1: Update the first Mermaid graph**

Use this entry sequence before the existing N01 node:

```mermaid
flowchart TD
    N00["N00 开始：仅 AGENT_USER_INPUT"] --> N00A["N00A 代码：解析单参数 JSON"]
    N00A --> N00B{"N00B 分支器：单参数有效?"}
    N00B -->|否| N00C["N00C 消息：输入格式错误"] --> N30["N30 结束"]
    N00B -->|是| N01["N01 数据库：读取画像和草稿"]
```

Retain every existing business edge after N01 and ensure all terminal messages reach the same N30.

- [ ] **Step 2: Replace multi-field debug inputs with six copy-ready JSON cases**

Each case must be pasted entirely into `AGENT_USER_INPUT`. Include first draft, modify, confirm, cancel, wrong token, and invalid input/missing uid. The confirm and wrong-token samples must tell the user to replace the sample token with the value returned by the preceding draft test.

- [ ] **Step 3: Add exact API/MAIN wrapping examples**

Show both the readable inner object and the outer one-parameter object:

```json
{
  "AGENT_USER_INPUT": "{\"uid\":\"test_user_001\",\"user_input\":\"确认保存\",\"confirmation_token\":\"profile_1_xxx\",\"request_time\":\"2026-07-19 16:55:00\"}"
}
```

State that the outer value is a String, not a nested platform parameter object.

- [ ] **Step 4: Render diagrams**

Run:

```powershell
python scripts/render_workflow_diagrams.py
```

Expected: the script reports `WF-01-user-profile.md -> docs\workflows\images\WF-01-draft-round.png` and regenerates the PNG from the edited Mermaid source.

- [ ] **Step 5: Inspect the rendered draft image**

Open `docs/workflows/images/WF-01-draft-round.png` and verify that N00A, N00B, and N00C are visible, the true edge reaches N01, and the false edge reaches N30 through N00C.

---

### Task 4: Validate and publish the documentation change

**Files:**
- Modify: `docs/workflows/WF-01-user-profile.md`
- Modify: `docs/workflows/images/WF-01-draft-round.png`
- Create: `docs/superpowers/plans/2026-07-19-wf01-single-parameter.md`

**Interfaces:**
- Consumes: all files from Tasks 1 through 3.
- Produces: a committed and pushed WF-01 single-parameter tutorial.

- [ ] **Step 1: Run repository workflow-guide validation**

Run:

```powershell
python scripts/validate_workflow_guides.py
```

Expected: exit code `0` with no validation errors.

- [ ] **Step 2: Run Markdown and Git checks**

Run:

```powershell
git diff --check
$text = Get-Content -Raw docs/workflows/WF-01-user-profile.md
$active = [regex]::Replace($text, '### 5\.5[\s\S]*?(?=\r?\n## 6\.)', '')
if ($active -match 'N00\s*/\s*(uid|confirmation_token|request_time)|N00\.(uid|confirmation_token|request_time)') { throw 'active config still references removed N00 fields' }
```

Expected: both checks exit without errors; old references are confined to the migration table.

- [ ] **Step 3: Review the complete diff against the design**

Run:

```powershell
git diff -- docs/workflows/WF-01-user-profile.md docs/workflows/images/WF-01-draft-round.png docs/superpowers/plans/2026-07-19-wf01-single-parameter.md
```

Verify N00 has one input, N00A always returns six keys, N00B blocks invalid input, N13 writes uid, all six tests use one field, and no branch is left without N30.

- [ ] **Step 4: Commit**

Run:

```powershell
git add docs/workflows/WF-01-user-profile.md docs/workflows/images/WF-01-draft-round.png docs/workflows/images/WF-01-confirm-round.png docs/superpowers/plans/2026-07-19-wf01-single-parameter.md
git commit -m "docs: convert WF01 to single parameter input"
```

Expected: one commit containing the guide, plan, and any changed rendered image.

- [ ] **Step 5: Push**

Run:

```powershell
git push origin main
```

Expected: the remote `main` branch advances to the new documentation commit.
