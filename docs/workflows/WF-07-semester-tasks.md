# WF-07 学期任务管理：逐节点搭建指南

> 本版严格使用 DB-06 模板已有字段，不再虚构 `pending_change` 或 `confirmation_token`。任务创建、更新、完成、延期、取消必须由用户本轮明确提出；主规划的保存/切换仍由 WF-06 两轮确认。当前结束节点返回 `workflow_finished`。

## 1. 数据表和开始输入

在 `university` 上传 [DB-06 semester_tasks](../database/import-templates/DB-06-semester-tasks.xlsx)。默认 `id/uid/create_time` 保留。

N00 开始输入：

| 变量 | 类型 | 必填 | 说明/调试值 |
|---|---|---:|---|
| `AGENT_USER_INPUT` | String | 是 | `创建本周完成项目需求分析的任务` |
| `uid` | String | 是 | `test_user_001` |
| `plan_id` | String | 创建时是 | 当前 active 主规划 ID |
| `semester` | String | 创建时是 | `2026秋` |
| `request_time` | String | 是 | `2026-07-19 17:00:00` |

## 2. 连线图

```mermaid
flowchart LR
    N00["N00 开始"] --> N01["N01 变量提取器：识别任务操作"]
    N01 --> N02{"N02 分支器：task_action"}
    N02 -->|query| N03["N03 数据库：查询任务"]
    N03 --> N04{"N04 分支器：查询成功？"}
    N04 -->|是| N05["N05 代码：整理任务列表"] --> N06["N06 消息：展示任务"]
    N04 -->|否| N25["N25 消息：查询失败"]
    N02 -->|create| N07["N07 大模型：生成任务草稿"]
    N07 --> N08["N08 变量提取器：提取任务字段"]
    N08 --> N09["N09 代码：校验并准备新增行"]
    N09 --> N10{"N10 分支器：新增字段有效？"}
    N10 -->|否| N24["N24 消息：字段不足"]
    N10 -->|是| N11["N11 数据库：新增任务"]
    N11 --> N12{"N12 分支器：新增成功？"}
    N12 -->|是| N13["N13 消息：创建成功"]
    N12 -->|否| N23["N23 消息：创建失败"]
    N02 -->|update/complete/postpone/cancel| N14["N14 数据库：读取目标任务"]
    N14 --> N15{"N15 分支器：读取成功？"}
    N15 -->|否| N26["N26 消息：目标读取失败"]
    N15 -->|是| N16["N16 代码：整理并生成新值"]
    N16 --> N17{"N17 分支器：目标和变更有效？"}
    N17 -->|否| N22["N22 消息：缺少任务或变更字段"]
    N17 -->|是| N18["N18 数据库：更新目标任务"]
    N18 --> N19{"N19 分支器：更新成功？"}
    N19 -->|是| N20["N20 数据库：回读任务"] --> N21["N21 代码：整理回读结果"]
    N21 --> N30{"N30 分支器：回读有记录？"}
    N30 -->|是| N31["N31 消息：操作成功"]
    N30 -->|否| N27
    N19 -->|否| N27["N27 消息：更新失败"]
    N02 -->|unknown| N28["N28 消息：说明支持操作"]
    N06 --> N29["N29 公共结束"]
    N13 --> N29
    N22 --> N29
    N23 --> N29
    N24 --> N29
    N25 --> N29
    N26 --> N29
    N27 --> N29
    N28 --> N29
    N31 --> N29
```

![WF-07 流程图 1](images/WF-07-semester-tasks-01.png)

N06、N13、N22～N28、N31 都连接 N29 结束。

## 3. N01/N02：识别操作

N01 模型 `Spark4.0 Ultra`，输入 `user_input=N00/AGENT_USER_INPUT`，输出：

| 变量 | 类型 | 描述 |
|---|---|---|
| `task_action` | String | 只能是 create、query、update、complete、postpone、cancel、unknown |
| `task_id` | String | 用户提到的任务 ID；未提及为空 |
| `task_text` | String | 新任务内容或修改后的任务内容 |
| `deadline_text` | String | 用户明确提出的新截止时间；未提及为空 |
| `priority` | String | 高/中/低；未提及为空 |
| `actual_evidence` | String | 完成任务时用户提供的成果证据 |
| `delay_reason` | String | 延期原因 |
| `query_scope` | String | 查询条件，如本周/未完成/全部 |

N02 为 `N01/task_action` 添加七条固定值分支；update、complete、postpone、cancel 四条都连 N14；默认连 N28。

## 4. 查询路径 N03～N06

N03 自定义 SQL，输入 `uid=N00/uid`：

```sql
SELECT task_id, plan_id, semester, month, week, task, deadline,
       priority, status, expected_evidence, actual_evidence,
       delay_reason, action_log_json, updated_at
FROM semester_tasks
WHERE uid='{{uid}}'
ORDER BY updated_at DESC, create_time DESC
LIMIT 50;
```

N04：`N03/isSuccess == true`；是 → N05，否 → N25。

N05 输入 `outputList=N03/outputList`、`query_scope=N01/query_scope`：

```python
def main(outputList, query_scope):
    rows = outputList if isinstance(outputList, list) else []
    lines = []
    for row in rows:
        if isinstance(row, dict):
            lines.append(str(row.get("task_id", "")) + " | " + str(row.get("status", "")) + " | " + str(row.get("task", "")) + " | 截止:" + str(row.get("deadline", "")))
    text = "\n".join(lines) if len(lines) > 0 else "当前没有任务记录。"
    return {"task_list_text": text, "task_count": len(lines)}
```

输出 `task_list_text:String`、`task_count:Integer`。N06 输入 `tasks=N05/task_list_text`，回答 `任务列表：\n{{tasks}}`。

> 当前版本先展示最近 50 条。若以后要真正按“本周/未完成”筛选，再为 N03 增加对应 SQL 参数；不要让模型假装已经筛选。

## 5. 创建路径 N07～N13

N07 大模型输入 `user_input=N00/AGENT_USER_INPUT`、`plan_id=N00/plan_id`、`semester=N00/semester`。系统提示词：

```text
你是大学任务拆解助手。只根据用户明确目标生成一条可执行任务，不虚构截止日期和成果。任务必须短、可行动、可验收；未知截止时间留空。优先级只能高/中/低。
只输出 JSON：
{"task":"","month":"","week":"","deadline":"","priority":"中","expected_evidence":"","reply":""}
```

用户提示词：`用户要求：{{user_input}}\n主规划：{{plan_id}}\n学期：{{semester}}`。输出 `output:String`。

N08 输入 `input=N07/output`，输出 `task:String`、`month:String`、`week:String`、`deadline:String`、`priority:String`、`expected_evidence:String`、`reply:String`。

N09 输入 `uid=N00/uid`、`plan_id=N00/plan_id`、`semester=N00/semester`、`request_time=N00/request_time` 和 N08 全部输出：

```python
def main(uid, plan_id, semester, request_time, task, month, week, deadline, priority, expected_evidence, reply):
    allowed = ["高", "中", "低"]
    errors = []
    if not str(plan_id).strip(): errors.append("缺少 plan_id")
    if not str(semester).strip(): errors.append("缺少 semester")
    if not str(task).strip(): errors.append("缺少 task")
    if str(priority) not in allowed: errors.append("priority 无效")
    return {
        "create_valid": len(errors) == 0,
        "create_error": ";".join(errors),
        "task_id": str(uid) + "-TASK-" + str(request_time),
        "plan_id": str(plan_id),
        "semester": str(semester),
        "month": str(month),
        "week": str(week),
        "task": str(task),
        "deadline": str(deadline),
        "priority": str(priority),
        "status": "pending",
        "expected_evidence": str(expected_evidence),
        "actual_evidence": "",
        "delay_reason": "",
        "action_log_json": "[]",
        "updated_at": str(request_time),
        "reply": str(reply),
    }
```

输出区声明：`create_valid:Boolean`，以及 `create_error/task_id/plan_id/semester/month/week/task/deadline/priority/status/expected_evidence/actual_evidence/delay_reason/action_log_json/updated_at/reply:String`。N10：true → N11，false → N24。

N11 表单新增 `semester_tasks`，把 N09 的 `task_id/plan_id/semester/month/week/task/deadline/priority/status/expected_evidence/actual_evidence/delay_reason/action_log_json/updated_at` 全部逐行映射；页面强制 uid 时引用 N00/uid。

N12：`N11/isSuccess == true`；是 → N13，否 → N23。N13 输入 `reply=N09/reply`、`task_id=N09/task_id`，回答 `任务已创建：{{reply}}\n任务 ID：{{task_id}}`。

## 6. 更新类路径 N14～N21

N14 自定义 SQL，输入 `uid=N00/uid`、`task_id=N01/task_id`：

```sql
SELECT id, task_id, plan_id, semester, month, week, task, deadline,
       priority, status, expected_evidence, actual_evidence,
       delay_reason, action_log_json, updated_at
FROM semester_tasks
WHERE uid='{{uid}}' AND task_id='{{task_id}}'
ORDER BY updated_at DESC LIMIT 1;
```

N15：`N14/isSuccess == true`；是 → N16，否 → N26。

N16 输入 `outputList=N14/outputList`、N01 的 `task_action/task_text/deadline_text/priority/actual_evidence/delay_reason`、`request_time=N00/request_time`：

```python
def main(outputList, task_action, task_text, deadline_text, priority, actual_evidence, delay_reason, request_time):
    rows = outputList if isinstance(outputList, list) else []
    row = rows[0] if len(rows) > 0 and isinstance(rows[0], dict) else {}
    action = str(task_action)
    old_status = str(row.get("status", ""))
    new_status = old_status
    if action == "complete": new_status = "completed"
    if action == "postpone": new_status = "postponed"
    if action == "cancel": new_status = "cancelled"
    new_task = str(task_text).strip() if str(task_text).strip() else str(row.get("task", ""))
    new_deadline = str(deadline_text).strip() if str(deadline_text).strip() else str(row.get("deadline", ""))
    new_priority = str(priority).strip() if str(priority).strip() else str(row.get("priority", "中"))
    evidence = str(actual_evidence).strip() if str(actual_evidence).strip() else str(row.get("actual_evidence", ""))
    reason = str(delay_reason).strip() if str(delay_reason).strip() else str(row.get("delay_reason", ""))
    errors = []
    if len(row) == 0: errors.append("未找到 task_id")
    if action == "complete" and not evidence: errors.append("完成任务必须提供成果证据")
    if action == "postpone" and (not str(deadline_text).strip() or not reason): errors.append("延期必须提供新截止时间和原因")
    if action == "update" and not str(task_text).strip() and not str(deadline_text).strip() and not str(priority).strip(): errors.append("没有提供要修改的字段")
    return {
        "change_valid": len(errors) == 0,
        "change_error": ";".join(errors),
        "task_id": str(row.get("task_id", "")),
        "task": new_task,
        "deadline": new_deadline,
        "priority": new_priority,
        "status": new_status,
        "actual_evidence": evidence,
        "delay_reason": reason,
        "updated_at": str(request_time),
        "display_text": action + "：" + new_task,
    }
```

输出 `change_valid:Boolean`，以及 `change_error/task_id/task/deadline/priority/status/actual_evidence/delay_reason/updated_at/display_text:String`。N17：true → N18，false → N22。

N18 表单更新 `semester_tasks`。范围：`uid=N00/uid` AND `task_id=N16/task_id`。更新 `task/deadline/priority/status/actual_evidence/delay_reason/updated_at`，全部引用 N16。当前代码环境不能安全解析并追加 JSON，因此更新时不要添加 `action_log_json`，让数据库保留旧值；本次变更由 `updated_at` 和任务新状态体现，不能写入伪 JSON 文本。

N19：`N18/isSuccess == true`；是 → N20，否 → N27。

N20 自定义 SQL，输入 uid、task_id，查询与 N14 相同字段。为避免“写入节点成功但实际未改”这一误判，N21 的输入使用 N20/outputList：

```python
def main(outputList):
    rows = outputList if isinstance(outputList, list) else []
    row = rows[0] if len(rows) > 0 and isinstance(rows[0], dict) else {}
    return {"readback_ok": len(row) > 0, "task_result_text": str(row)}
```

把这个代码作为 N21（原消息前插入），输出 `readback_ok:Boolean`、`task_result_text:String`；再连接 N30 分支器 `readback_ok == true`：是 → N31 成功消息，否 → N27。为保持画布编号清晰，实际画布最后采用：N20 数据库回读 → N21 代码整理 → N30 分支器 → N31 消息。

## 7. 消息和结束

| 节点 | 回答内容 |
|---|---|
| N22 | 引用 N16/change_error：`任务变更信息不足：{{change_error}}` |
| N23 | 引用 N11/message：`任务草稿有效，但创建失败：{{message}}` |
| N24 | 引用 N09/create_error：`不能创建任务：{{create_error}}` |
| N25 | 引用 N03/message：`任务查询失败：{{message}}` |
| N26 | 引用 N14/message：`目标任务读取失败：{{message}}` |
| N27 | 引用 N18/message：`任务更新或回读失败，不能声称操作成功：{{message}}` |
| N28 | `请明确说“创建/查询/更新/完成/延期/取消任务”，并在变更时提供 task_id。` |
| N31 | 输入 `result=N21/task_result_text`：`任务操作成功并已回读：{{result}}` |

所有消息连接 N29 结束。N29 配置：`output｜输入｜workflow_finished`，回答内容“本轮处理已结束，请以上方消息节点的提示为准。”，流式关闭。

## 8. 调试指南：先从 WF-06 取得 active plan_id

### 8.1 上游准备

1. 使用测试 uid `debug_wf07_001` 完成 WF-05 比较和 WF-06 两轮确认。
2. 在 DB-05 `main_plans` 中筛选该 uid，只应有一条 `plan_status=active`。
3. 复制该行 `plan_id`，不要使用 pending 或 history 行的 plan_id。
4. 在 DB-06 `semester_tasks` 筛选该 uid，首次测试最好为空；记录测试前行数。

WF-07 不会查询 DB-05 验证 plan_id，因此开始节点传错值仍可能创建一条无法归属的任务。手工测试时必须先完成上述核验。

### 测试 1：空任务列表查询

```text
AGENT_USER_INPUT = 查询我的全部任务
uid = debug_wf07_001
plan_id = WF-06 当前 active plan_id
semester = 2026秋
request_time = 2026-07-19 17:00:00
```

预期 N01/task_action=query → N02 query → N03 → N04（是）→ N05 → N06 → N29。若 outputList 为空，N05 应输出“当前没有任务记录”，不是 N25 查询失败。

### 测试 2：创建任务

```text
AGENT_USER_INPUT = 创建任务：本周完成项目需求分析，优先级高，成果是需求文档
request_time = 2026-07-19 17:05:00
```

预期 N02 create → N07→N08→N09/create_valid=true→N10（是）→N11→N12（是）→N13→N29。DB-06 新增一行，`plan_id` 等于 active plan_id，`status=pending`，`task/priority/expected_evidence` 非空。复制 N13 展示的 `task_id`。

### 测试 3：缺少创建必填输入

临时把 N00/plan_id 留空后创建任务。预期 N09/create_valid=false → N10（否）→ N24，不执行 N11。恢复 active plan_id。再把 semester 留空重复一次，应得到同样门禁。

### 测试 4：查询已有任务

恢复完整输入并查询。N06 应列出测试 2 的 task_id、pending 状态、任务内容和截止信息。对照 DB-06，列表不得混入其他 uid 的记录。

### 测试 5：更新任务但缺 task_id

```text
AGENT_USER_INPUT = 把任务优先级改为中
```

若输入中没有 task_id，N14 查询会空数组，N16/change_valid=false，N17（否）→N22；DB-06 不变化。随后使用明确文本“把任务 debug... 的优先级改为中”重试。

### 测试 6：完成任务必须提供成果证据

先输入 `完成任务 <task_id>`，不提供成果。预期 N16 报“完成任务必须提供成果证据”→N22。再输入：

```text
完成任务 <task_id>，成果证据：需求文档已保存到项目仓库 docs/requirements.md
```

预期 N18 更新成功 → N20 回读 → N21/readback_ok=true → N30（是）→N31。DB-06 对应行 `status=completed`、`actual_evidence` 非空。

### 测试 7：延期必须同时提供日期和原因

新建另一条 pending 任务。只说“延期任务 <task_id>”应到 N22。再提供“延期到 2026-08-01，因为课程考试周冲突”，应更新为 `status=postponed`，同时保存新 deadline 和 delay_reason，并由 N20/N21 回读。

### 测试 8：取消只改状态、不删记录

对另一条 pending 任务输入 `取消任务 <task_id>`。预期更新后回读成功，原记录仍存在但 `status=cancelled`；数据库行不能被删除。

### 测试 9：未知操作

输入“帮我看看吧”且不包含创建、查询、更新、完成、延期、取消意图。预期 N01/task_action=unknown → N02 unknown → N28 → N29，所有数据库写节点不执行。

### 测试 10：查询、创建、更新和回读故障

每次只破坏一个节点并在测试后恢复：

1. N03 表名改错：N04（否）→N25；恢复 `semester_tasks`。
2. N11 清空 `task_id`：N12（否）→N23；恢复 `task_id=N09/task_id`。
3. N14 表名改错：N15（否）→N26；恢复表名。
4. N18 清空 uid 或 task_id 更新范围：N19（否）→N27；恢复两个 AND 条件。
5. N20 表名改错或让回读空数组：N21/readback_ok=false →N30（否）→N27；恢复查询。

### 8.2 最终留证

保存空列表、创建成功、缺证据、完成回读、延期和取消消息截图。DB-06 至少保留一条 completed、一条 postponed、一条 cancelled 记录，并记录 active `plan_id` 与各 task_id。确认所有临时错误已恢复。

## 9. 验收清单

- [ ] 不存在模板外的 pending_change/token 字段。
- [ ] 任务写操作必须由本轮明确动作触发。
- [ ] 完成有成果证据，延期有新日期和原因。
- [ ] 写入后回读，失败不说成功。
- [ ] 所有代码无 import，输出声明完整；所有分支有终点。
