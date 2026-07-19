# WF-10 决策分析与七天试错：逐节点搭建指南

> 本工作流有五种操作：即时分析、创建七天试错、确认启动、每日记录、第七天复盘，另有停止和安全出口。每个模式单独成图，避免旧版总图交叉。七天试错是低风险实验，不得替代医疗、法律或财务专业意见。

## 1. 数据表与开始输入

在 `university` 上传 [DB-09 decision_trials](../database/import-templates/DB-09-decision-trials.xlsx)，保留 `id/uid/create_time`。

N00 开始输入：

| 变量 | 类型 | 必填 | 调试值 |
|---|---|---:|---|
| `AGENT_USER_INPUT` | String | 是 | `我该选实验室项目还是实习？` |
| `uid` | String | 是 | `test_user_001` |
| `trial_id` | String | 否 | 每日记录/复盘/停止时填写 |
| `confirmation_token` | String | 否 | 确认启动时填写 |
| `request_time` | String | 是 | `2026-07-19 20:00:00` |

## 2. 入口路由

```mermaid
flowchart LR
    N00["N00 开始"] --> N01["N01 变量提取器：识别模式和安全风险"]
    N01 --> N02{"N02 分支器：高风险请求？"}
    N02 -->|是| N63["N63 消息：停止并寻求帮助"]
    N02 -->|否| N03{"N03 分支器：trial_action"}
    N03 -->|analysis| N04["N04 大模型：即时决策分析"]
    N03 -->|create_trial| N11["N11 大模型：生成七天计划"]
    N03 -->|confirm_trial| N20["N20 数据库：读取 pending 计划"]
    N03 -->|daily_log| N30["N30 数据库：读取 active 计划"]
    N03 -->|day7_review| N44["N44 数据库：读取计划和日志"]
    N03 -->|stop| N59["N59 数据库：停止试错"]
    N03 -->|unknown| N64["N64 消息：说明支持模式"]
    N63 --> N65["N65 公共结束"]
    N64 --> N65
```

![WF-10 流程图 1](images/WF-10-decision-and-trial-01.png)

N01 输入 `user_input=N00/AGENT_USER_INPUT`、`trial_id=N00/trial_id`，输出：

| 变量 | 类型 | 描述 |
|---|---|---|
| `trial_action` | String | analysis/create_trial/confirm_trial/daily_log/day7_review/stop/unknown |
| `safety_risk` | Boolean | 自伤、伤人、违法、极端健康风险或要求替代专业诊疗时为 true |
| `decision_topic` | String | 决策主题 |
| `day_number` | Integer | 每日记录的第几天；无法判断为 0 |
| `action_reason` | String | 分类依据 |

N02 判断 `safety_risk == true`；N03 为 trial_action 添加七条固定值分支。

## 3. 即时分析 N04～N10

```mermaid
flowchart LR
    N04["N04 大模型：即时决策分析"] --> N05["N05 变量提取器：提取分析"]
    N05 --> N06["N06 代码：准备 analysis 行"] --> N07["N07 数据库：新增分析"]
    N07 --> N08{"N08 分支器：保存成功？"}
    N08 -->|是| N09["N09 消息：展示分析"]
    N08 -->|否| N10["N10 消息：分析未保存"]
    N09 --> N65["N65 公共结束"]
    N10 --> N65
```

![WF-10 流程图 2](images/WF-10-decision-and-trial-02.png)

N04 模型 `Spark4.0 Ultra`，关闭历史。输入 `user_input=N00/AGENT_USER_INPUT`、`topic=N01/decision_topic`。系统提示词：

```text
你是低风险大学决策教练。用目标、选项、约束、可逆性、最坏情况、机会成本、信息缺口和下一步小实验分析，不替用户决定，不给成功概率。只输出 JSON：
{"topic":"","options":[],"constraints":[],"tradeoffs":[],"reversibility":"","worst_case":"","missing_information":[],"next_small_step":"","reply":""}
```

N05 输出 `decision_json:String`、`reply:String`。N06 输入 uid/request_time/decision_json/reply：

```python
def main(uid, request_time, decision_json, reply):
    return {
        "trial_id": str(uid) + "-DECISION-" + str(request_time), "record_type": "analysis",
        "decision_json": str(decision_json), "trial_plan_json": "{}", "pending_json": "{}",
        "confirmation_token": "", "day_number": 0, "daily_log_json": "{}", "review_json": "{}",
        "trial_status": "completed", "updated_at": str(request_time), "reply": str(reply)
    }
```

输出 `day_number:Integer`，以及 `trial_id/record_type/decision_json/trial_plan_json/pending_json/confirmation_token/daily_log_json/review_json/trial_status/updated_at/reply:String`。N07 表单新增 DB-09，逐项映射 N06 所有表字段；页面强制 uid 时引用 N00/uid。N08 判断 isSuccess。N09 展示 reply；N10 展示 decision_json 并说明未保存及 N07/message。

## 4. 创建七天试错 N11～N19

```mermaid
flowchart LR
    N11["N11 大模型：生成七天计划"] --> N12["N12 变量提取器：提取计划"]
    N12 --> N13["N13 代码：校验并准备 pending 行"] --> N14{"N14 分支器：计划有效？"}
    N14 -->|否| N19["N19 消息：计划无效"]
    N14 -->|是| N15["N15 数据库：新增 pending 计划"] --> N16{"N16 分支器：保存成功？"}
    N16 -->|是| N17["N17 消息：展示计划和 token"]
    N16 -->|否| N18["N18 消息：计划未保存"]
    N17 --> N65["N65 公共结束"]
    N18 --> N65
    N19 --> N65
```

![WF-10 流程图 3](images/WF-10-decision-and-trial-03.png)

N11 输入 user_input/topic。系统提示词要求：每天 10～60 分钟、只收集验证决策所需证据、包含退出条件、安全边界和第七天复盘标准；只输出 `{"trial_plan":{},"reply":""}`。

N12 输出 `trial_plan_json:String`、`days:Array`、`success_evidence:Array`、`stop_conditions:Array`、`reply:String`。

N13 输入 uid/request_time 和 N12 输出：

```python
def main(uid, request_time, trial_plan_json, days, success_evidence, stop_conditions, reply):
    errors = []
    if not str(trial_plan_json).strip().startswith("{"): errors.append("计划 JSON 无效")
    if not isinstance(days, list) or len(days) != 7: errors.append("必须恰好 7 天")
    if not isinstance(success_evidence, list) or len(success_evidence) == 0: errors.append("缺少验证证据")
    if not isinstance(stop_conditions, list) or len(stop_conditions) == 0: errors.append("缺少停止条件")
    token = str(uid) + "-TRIAL-" + str(request_time)
    return {
        "plan_valid": len(errors) == 0, "plan_error": ";".join(errors),
        "trial_id": str(uid) + "-TRIAL-" + str(request_time), "record_type": "plan",
        "decision_json": "{}", "trial_plan_json": "{}", "pending_json": str(trial_plan_json),
        "confirmation_token": token, "day_number": 0, "daily_log_json": "{}", "review_json": "{}",
        "trial_status": "pending", "updated_at": str(request_time), "reply": str(reply)
    }
```

输出 `plan_valid:Boolean`、`day_number:Integer`，以及 `plan_error/trial_id/record_type/decision_json/trial_plan_json/pending_json/confirmation_token/daily_log_json/review_json/trial_status/updated_at/reply:String`。N14 判断 plan_valid。N15 表单新增 DB-09 全字段。N16 判断 isSuccess。N17 展示 pending_json、trial_id、token，要求明确回复“确认启动七天试错”；N18/N19 分别展示数据库 message/plan_error。

## 5. 确认启动 N20～N29

```mermaid
flowchart LR
    N20["N20 数据库：读取 pending 计划"] --> N21{"N21 分支器：SQL 成功？"}
    N21 -->|否| N29["N29 消息：pending 读取失败"]
    N21 -->|是| N22["N22 代码：整理并校验 token"] --> N23{"N23 分支器：确认有效？"}
    N23 -->|否| N28["N28 消息：确认无效"]
    N23 -->|是| N24["N24 数据库：激活计划"] --> N25{"N25 分支器：激活成功？"}
    N25 -->|是| N26["N26 消息：试错已启动"]
    N25 -->|否| N27["N27 消息：激活失败"]
    N26 --> N65["N65 公共结束"]
    N27 --> N65
    N28 --> N65
    N29 --> N65
```

![WF-10 流程图 4](images/WF-10-decision-and-trial-04.png)

N20 自定义 SQL，输入 uid 和 trial_id：

```sql
SELECT id, trial_id, pending_json, confirmation_token, trial_status
FROM decision_trials
WHERE uid='{{uid}}' AND trial_id='{{trial_id}}' AND record_type='plan' AND trial_status='pending'
ORDER BY updated_at DESC LIMIT 1;
```

N21 判断 isSuccess。N22 输入 outputList、input_token=N00/confirmation_token：

```python
def main(outputList, input_token):
    rows = outputList if isinstance(outputList, list) else []
    row = rows[0] if len(rows) > 0 and isinstance(rows[0], dict) else {}
    stored = str(row.get("confirmation_token", ""))
    valid = len(row) > 0 and str(input_token) != "" and str(input_token) == stored
    return {
        "confirm_valid": valid, "confirm_error": "" if valid else "pending 不存在或 token 不匹配",
        "record_id": int(row.get("id", 0)) if str(row.get("id", "0")).isdigit() else 0,
        "trial_plan_json": str(row.get("pending_json", "{}"))
    }
```

输出 confirm_valid:Boolean、confirm_error:String、record_id:Integer、trial_plan_json:String。N23 判断 confirm_valid。N24 表单更新 DB-09，范围 `id=N22/record_id AND uid=N00/uid`；更新 `trial_plan_json=N22/trial_plan_json`、`pending_json={}`、`confirmation_token=空`、`trial_status=active`、`updated_at=N00/request_time`。N25 判断 isSuccess；N26 显示“已启动”和 trial_id；N27/N28/N29 显示对应错误。

## 6. 每日记录 N30～N43

```mermaid
flowchart LR
    N30["N30 数据库：读取 active 计划"] --> N31{"N31 分支器：SQL 成功？"}
    N31 -->|否| N43["N43 消息：active 读取失败"]
    N31 -->|是| N32["N32 代码：整理 active 计划"] --> N33{"N33 分支器：找到计划？"}
    N33 -->|否| N42["N42 消息：没有 active 试错"]
    N33 -->|是| N34["N34 大模型：提取每日记录"] --> N35["N35 变量提取器：提取日志"]
    N35 --> N36["N36 代码：准备 daily_log 行"] --> N37{"N37 分支器：日志有效？"}
    N37 -->|否| N42
    N37 -->|是| N38["N38 数据库：新增日志"]
    N38 --> N39{"N39 分支器：保存成功？"}
    N39 -->|是| N40["N40 消息：记录成功"]
    N39 -->|否| N41["N41 消息：记录失败"]
    N40 --> N65["N65 公共结束"]
    N41 --> N65
    N42 --> N65
    N43 --> N65
```

![WF-10 流程图 5](images/WF-10-decision-and-trial-05.png)

N30 选择自定义 SQL，输入 `uid=N00/uid`、`trial_id=N00/trial_id`：

```sql
SELECT id, trial_id, trial_plan_json, trial_status, updated_at
FROM decision_trials
WHERE uid='{{uid}}' AND trial_id='{{trial_id}}'
  AND record_type='plan' AND trial_status='active'
ORDER BY updated_at DESC LIMIT 1;
```

N31 判断 `N30/isSuccess == true`。N32 输入 `outputList=N30/outputList`：

```python
def main(outputList):
    rows = outputList if isinstance(outputList, list) else []
    row = rows[0] if len(rows) > 0 and isinstance(rows[0], dict) else {}
    plan_text = str(row.get("trial_plan_json", ""))
    return {"has_active": len(row) > 0 and len(plan_text.strip()) > 2, "trial_plan_json": plan_text if plan_text else "{}"}
```

输出 `has_active:Boolean`、`trial_plan_json:String`。N33 判断 `has_active == true`。

N34 输入 user_input、day_number=N01/day_number、trial_plan_json。系统提示词只提取“实际做了什么、时长、证据、感受、阻碍、是否触发停止条件”，不得把计划写成已完成。N35 输出 `daily_log_json:String`、`day_number:Integer`、`reply:String`。

N36：

```python
def main(uid, trial_id, request_time, day_number, daily_log_json, reply):
    try: day = int(day_number)
    except: day = 0
    valid_day = 1 <= day <= 7
    return {
        "log_valid": valid_day, "log_error": "" if valid_day else "day_number 必须为 1～7",
        "trial_id": str(trial_id), "record_type": "daily_log", "decision_json": "{}", "trial_plan_json": "{}",
        "pending_json": "{}", "confirmation_token": "", "day_number": day,
        "daily_log_json": str(daily_log_json), "review_json": "{}", "trial_status": "active",
        "updated_at": str(request_time), "reply": str(reply)
    }
```

N36 输出 `log_valid:Boolean`、`day_number:Integer`，以及 `log_error/trial_id/record_type/decision_json/trial_plan_json/pending_json/confirmation_token/daily_log_json/review_json/trial_status/updated_at/reply:String`。N37 判断 `N36/log_valid == true`；false → N42（消息中显示 N36/log_error），true → N38。N38 表单新增 DB-09 全字段，N39 判断 `N38/isSuccess == true`，N40/N41 分别展示成功或 N38/message。

## 7. 第七天复盘 N44～N58

```mermaid
flowchart LR
    N44["N44 数据库：读取计划和日志"] --> N45{"N45 分支器：SQL 成功？"}
    N45 -->|否| N58["N58 消息：复盘读取失败"]
    N45 -->|是| N46["N46 代码：整理 7 天证据"] --> N47{"N47 分支器：证据足够？"}
    N47 -->|否| N57["N57 消息：缺少日志"]
    N47 -->|是| N48["N48 大模型：生成第七天复盘"] --> N49["N49 变量提取器：提取复盘"]
    N49 --> N50["N50 代码：准备 review 行"] --> N51["N51 数据库：新增 day7_review"]
    N51 --> N52{"N52 分支器：复盘保存成功？"}
    N52 -->|否| N56["N56 消息：复盘未保存"]
    N52 -->|是| N53["N53 数据库：把计划标记 completed"] --> N54{"N54 分支器：状态更新成功？"}
    N54 -->|是| N55["N55 消息：展示完整复盘"]
    N54 -->|否| N56
    N55 --> N65["N65 公共结束"]
    N56 --> N65
    N57 --> N65
    N58 --> N65
```

![WF-10 流程图 6](images/WF-10-decision-and-trial-06.png)

N44 自定义 SQL，输入 uid、trial_id：

```sql
SELECT id, trial_id, record_type, trial_plan_json, day_number,
       daily_log_json, trial_status, updated_at
FROM decision_trials
WHERE uid='{{uid}}' AND trial_id='{{trial_id}}'
  AND record_type IN ('plan','daily_log')
ORDER BY day_number ASC, updated_at ASC;
```

N45 判断 `N44/isSuccess == true`。

N46 输入 `outputList=N44/outputList`：

```python
def main(outputList):
    rows = outputList if isinstance(outputList, list) else []
    plan_json = "{}"
    logs = []
    for row in rows:
        if isinstance(row, dict) and row.get("record_type") == "plan":
            plan_json = str(row.get("trial_plan_json", "{}"))
        if isinstance(row, dict) and row.get("record_type") == "daily_log" and len(str(row.get("daily_log_json", "")).strip()) > 2:
            logs.append(row)
    return {
        "plan_json": plan_json,
        "daily_logs": logs,
        "log_count": len(logs),
        "review_ready": len(logs) >= 3 and len(plan_json.strip()) > 2,
    }
```

输出 `plan_json:String`、`daily_logs:Array<Object>`、`log_count:Integer`、`review_ready:Boolean`。N47 判断 `review_ready == true`。

N48 要求依据真实日志比较预期与实际、有效证据、反例、成本、是否继续/调整/停止，输出 `{"review":{},"recommendation":"continue|adjust|stop","reply":""}`。N49 输出 `review_json:String`、`recommendation:String`、`reply:String`。

N50 输入 `uid=N00/uid`、`trial_id=N00/trial_id`、`request_time=N00/request_time`、`review_json=N49/review_json`、`reply=N49/reply`：

```python
def main(uid, trial_id, request_time, review_json, reply):
    return {
        "trial_id": str(trial_id), "record_type": "day7_review",
        "decision_json": "{}", "trial_plan_json": "{}", "pending_json": "{}",
        "confirmation_token": "", "day_number": 7, "daily_log_json": "{}",
        "review_json": str(review_json), "trial_status": "completed",
        "updated_at": str(request_time), "reply": str(reply)
    }
```

输出区声明 `day_number:Integer`，以及 `trial_id/record_type/decision_json/trial_plan_json/pending_json/confirmation_token/daily_log_json/review_json/trial_status/updated_at/reply:String`。N51 选择表单新增 DB-09，逐字段映射 N50 的 `trial_id/record_type/decision_json/trial_plan_json/pending_json/confirmation_token/day_number/daily_log_json/review_json/trial_status/updated_at`；页面强制 uid 时引用 N00/uid。N52 判断 `N51/isSuccess == true`。

N53 表单更新 DB-09：范围 uid+trial_id+record_type 固定 `plan`；更新 trial_status=`completed`、updated_at=request_time。N54 判断 isSuccess。N55 展示 reply+review_json，并说明若要改主规划需进入 WF-06。

## 8. 停止、安全、结束

停止路径使用 N59 数据库：表单更新 DB-09，范围 uid+trial_id+record_type=plan；更新 trial_status=stopped、updated_at=request_time。N60 判断 isSuccess；成功到 N61“试错已停止，已有日志保留”，失败到 N62 并显示 message。

```mermaid
flowchart LR
    N59["N59 数据库：停止试错"] --> N60{"N60 分支器：停止成功？"}
    N60 -->|是| N61["N61 消息：试错已停止"] --> N65["N65 公共结束"]
    N60 -->|否| N62["N62 消息：停止失败"] --> N65
```

![WF-10 流程图 7](images/WF-10-decision-and-trial-07.png)

N63 安全消息：`这个请求可能涉及人身安全、严重健康或违法风险。我不能把它当作普通七天试错。请立即停止相关行动，并联系可信任的人或当地专业/紧急支持。`

N64：说明支持“即时分析、创建试错、确认启动、每日记录、第七天复盘、停止试错”，并要求 trial_id。

所有消息连接 N65。N65 配置 `output｜输入｜workflow_finished`，回答内容“本轮处理已结束，请以上方消息节点的提示为准。”，流式关闭。

## 9. 调试指南：按一个 trial_id 跑完整生命周期

### 9.1 前置说明

WF-10 没有强制上游工作流，使用独立 uid `debug_wf10_001` 即可。它会在同一张 DB-09 `decision_trials` 中保存 analysis、plan、daily_log、day7_review 多种 record_type。调试时必须同时看 `trial_id + record_type`，不能只按 uid 判断。

每轮都使用更晚的 request_time。创建试错后，后续确认、日志、复盘和停止必须填写 N17 返回的同一个 trial_id。

### 测试 1：即时分析，不进入确认

```text
AGENT_USER_INPUT = 请分析我应该选择实验室项目还是暑期实习，但先不要替我决定
uid = debug_wf10_001
trial_id = 空
confirmation_token = 空
request_time = 2026-07-19 20:00:00
```

预期 N01/trial_action=analysis→N02（否）→N03 analysis→N04～N07→N08（是）→N09→N65。DB-09 新增 `record_type=analysis`、`trial_status=completed`，不生成 pending token。

### 测试 2：创建七天试错 pending

```text
AGENT_USER_INPUT = 为实验室项目和实习的选择创建一个七天低风险试错计划
request_time = 2026-07-19 20:05:00
```

预期 N03=create_trial→N11→N12→N13/plan_valid=true→N14（是）→N15→N16（是）→N17→N65。检查 N12/days 恰好 7 项，success_evidence 和 stop_conditions 都非空。

DB-09 新增 `record_type=plan`、`trial_status=pending`，`pending_json` 非空、`trial_plan_json={}`、token 非空。复制 N17 的 trial_id 和 token。

### 测试 3：计划结构不完整

临时让 N12/days 只有 6 项，或让 stop_conditions 为空。预期 N13/plan_valid=false→N14（否）→N19，不执行 N15。恢复 N12 输出映射后重新生成有效计划。

### 测试 4：错误 token 与正确启动

先输入：

```text
AGENT_USER_INPUT = 确认启动七天试错
trial_id = N17 返回值
confirmation_token = wrong-token
request_time = 2026-07-19 20:10:00
```

预期 N20 SQL 成功→N22/confirm_valid=false→N23（否）→N28。plan 行仍 pending。

再改成正确 token 和新时间，预期 N23（是）→N24→N25（是）→N26。DB-09 同一 plan 行变 active，`trial_plan_json` 获得正式计划，pending_json 清空，token 清空。

### 测试 5：确认读取和激活失败

1. 临时把 N20 表名改错：N21（否）→N29；恢复 `decision_trials`。
2. 使用不存在的 trial_id：N20/isSuccess=true 但空数组，N22 confirm_valid=false→N28。
3. 对有效 pending 临时破坏 N24 id+uid 范围：N25（否）→N27；恢复范围。

### 测试 6：没有 active 计划时写日志

使用不存在的 trial_id，输入“记录第1天：完成了30分钟岗位信息整理”。预期 N30 SQL 成功空数组→N32/has_active=false→N33（否）→N42，N38 不执行。

### 测试 7：有效每日记录

使用已激活 trial_id：

```text
AGENT_USER_INPUT = 记录第1天：我花了30分钟比较两个选项的实际任务，证据是整理了一页对比表，没有触发停止条件
trial_id = 已激活 trial_id
request_time = 2026-07-19 20:15:00
```

预期 N30→N31（是）→N32→N33（是）→N34→N35→N36/log_valid=true→N37（是）→N38→N39（是）→N40。DB-09 新增 `record_type=daily_log`、`day_number=1`，只保存实际发生内容。

### 测试 8：日志天数越界和写入失败

输入“记录第8天……”应使 N36/log_valid=false→N37（否）→N42，不写 DB。再临时清空 N38/trial_id 测试写入失败：N39（否）→N41；恢复 `trial_id=N36/trial_id`。

### 测试 9：不足三条日志时复盘

只有 1～2 条 daily_log 时输入“进行第七天复盘”。预期 N44→N45（是）→N46/log_count<3→N47（否）→N57。N48、N51、N53 都不执行。

### 测试 10：日志足够后完成复盘

按测试 7 方法至少写入 day1、day2、day3 三条不同事实日志，再发起复盘。预期 N47（是）→N48→N49→N50→N51→N52（是）→N53→N54（是）→N55。DB-09 新增 `record_type=day7_review`，同时原 plan 行 `trial_status=completed`。N55 若建议改主规划，只能提示进入 WF-06。

### 测试 11：复盘写入或计划关闭失败

1. 临时清空 N51/trial_id：N52（否）→N56；恢复映射。
2. 在复盘已保存后临时破坏 N53 的 uid+trial_id+record_type=plan 范围：N54（否）→N56，不能说完整结束；恢复范围并人工核验 DB 状态。
3. 临时改错 N44 表名：N45（否）→N58；恢复表名。

### 测试 12：主动停止

新建并激活另一条计划，写入一条日志后输入“停止这个试错 <trial_id>”。预期 N59→N60（是）→N61。plan 状态变 stopped，已有 daily_log 行仍保留，不删除历史。

### 测试 13：安全出口

输入包含明确自伤、伤人、违法或严重健康风险的试错请求。预期 N01/safety_risk=true→N02（是）→N63→N65；N03 和所有普通模型、数据库节点都不执行。安全消息应建议停止并寻求可信任或专业支持。

### 测试 14：未知模式

输入“随便处理一下”，且不构成明确模式。预期 N03=unknown→N64，说明支持的操作和缺少的 trial_id，不写数据库。

### 9.2 最终数据库核验

对完整生命周期 trial_id，DB-09 至少应有：一条 completed/stopped 的 plan、三条以上 daily_log、需要时一条 day7_review。保存 N17、N28、N26、N40、N57、N55、N61、N63 截图，并确认 N20、N24、N38、N44、N51、N53 的临时错误都已恢复。

## 10. 验收清单

- [ ] 五种模式和 stop/unknown/safety 均有独立终点。
- [ ] pending 计划只有 token 确认后才 active。
- [ ] 日志只记录事实，不把计划当完成。
- [ ] 复盘保存后同时关闭 active 计划。
- [ ] 所有数据库新增填满 DB-09 必填字段。
- [ ] 所有代码无 import，输出区声明完整，所有消息连接 N65。
