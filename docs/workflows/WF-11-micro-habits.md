# WF-11 微习惯与生活记录：逐节点搭建指南

> WF-11 记录真实发生的习惯、支出和运动，不生成不存在的完成记录。高风险健康/安全输入直接停止，不默认把敏感求助内容写进数据库。

## 1. 数据表和输入

在 `university` 上传 [DB-10 habit_logs](../database/import-templates/DB-10-habit-logs.xlsx)，保留 `id/uid/create_time`。

N00 开始：

| 变量 | 类型 | 必填 | 调试值 |
|---|---|---:|---|
| `AGENT_USER_INPUT` | String | 是 | `今天背了20分钟单词` |
| `uid` | String | 是 | `test_user_001` |
| `request_time` | String | 是 | `2026-07-19 21:00:00` |

## 2. 完整流程图

```mermaid
flowchart LR
    N00["N00 开始"] --> N01["N01 变量提取器：分类并提取记录"]
    N01 --> N02{"N02 分支器：高风险？"}
    N02 -->|是| N14["N14 消息：停止并寻求帮助"]
    N02 -->|否| N03["N03 代码：校验并准备记录"]
    N03 --> N04{"N04 分支器：记录有效？"}
    N04 -->|否| N12["N12 消息：补充必要字段"]
    N04 -->|是| N05["N05 数据库：读取同类近期记录"]
    N05 --> N06{"N06 分支器：查询成功？"}
    N06 -->|否| N13["N13 消息：历史读取失败"]
    N06 -->|是| N07["N07 代码：生成反馈并准备写入"]
    N07 --> N08["N08 数据库：新增生活记录"]
    N08 --> N09{"N09 分支器：保存成功？"}
    N09 -->|是| N10["N10 消息：记录成功"]
    N09 -->|否| N11["N11 消息：记录失败"]
    N10 --> N15["N15 公共结束"]
    N11 --> N15
    N12 --> N15
    N13 --> N15
    N14 --> N15
```

![WF-11 流程图 1](images/WF-11-micro-habits-01.png)

N10～N14 全部连接 N15 结束。

## 3. N01 变量提取器：分类和提取

模型 `Spark4.0 Ultra`。输入 `user_input=N00/AGENT_USER_INPUT`。输出：

| 变量 | 类型 | 描述 |
|---|---|---|
| `log_type` | String | habit、expense、fitness、unknown 之一 |
| `habit_name` | String | 习惯名称 |
| `amount` | String | 支出金额，只保留用户原话中的数值 |
| `category` | String | 支出或活动类别 |
| `duration_minutes` | Integer | 用户明确提供的分钟数；未提供为 0 |
| `completed` | Boolean | 用户明确说已完成才为 true；计划做/想做为 false |
| `note` | String | 用户原始补充说明 |
| `safety_risk` | Boolean | 自伤、伤人、严重健康症状、极端节食/过度运动或违法风险时 true |
| `missing_fields` | Array | 当前类型缺少的必要字段 |

N02 引用 `safety_risk == true`。是 → N14，否 → N03。

## 4. N03/N04：校验并准备基础记录

N03 输入 uid/request_time 和 N01 全部输出：

```python
def main(uid, request_time, log_type, habit_name, amount, category, duration_minutes, completed, note, missing_fields):
    allowed = ["habit", "expense", "fitness"]
    errors = []
    try: minutes = int(duration_minutes)
    except: minutes = 0
    if str(log_type) not in allowed: errors.append("无法识别记录类型")
    if str(log_type) == "habit" and not str(habit_name).strip(): errors.append("缺少习惯名称")
    if str(log_type) == "expense" and not str(amount).strip(): errors.append("缺少支出金额")
    if str(log_type) == "fitness" and minutes <= 0: errors.append("缺少有效运动分钟数")
    completed_text = "true" if completed is True else "false"
    return {
        "record_valid": len(errors) == 0,
        "record_error": ";".join(errors),
        "log_id": str(uid) + "-LOG-" + str(request_time),
        "log_type": str(log_type),
        "habit_name": str(habit_name),
        "log_date": str(request_time),
        "amount": str(amount),
        "category": str(category),
        "duration_minutes": minutes,
        "completed": completed_text,
        "note": str(note),
        "safety_flag": "none",
        "log_json": "{}",
        "updated_at": str(request_time),
    }
```

输出区声明 `record_valid:Boolean`、`duration_minutes:Integer`，以及 `record_error/log_id/log_type/habit_name/log_date/amount/category/completed/note/safety_flag/log_json/updated_at:String`。N04：`record_valid == true`；是 → N05，否 → N12。

## 5. N05/N06：读取同类近期记录

N05 自定义 SQL，输入 `uid=N00/uid`、`log_type=N03/log_type`：

```sql
SELECT log_id, log_type, habit_name, log_date, amount, category,
       duration_minutes, completed, note, updated_at
FROM habit_logs
WHERE uid='{{uid}}' AND log_type='{{log_type}}'
ORDER BY log_date DESC, create_time DESC
LIMIT 20;
```

N06：`N05/isSuccess == true`；是 → N07，否 → N13。空数组是第一次记录，仍走“是”。

## 6. N07 代码：生成反馈并准备写入

输入 `outputList=N05/outputList` 以及 N03 的所有数据库字段：

```python
def main(outputList, log_id, log_type, habit_name, log_date, amount, category, duration_minutes, completed, note, safety_flag, log_json, updated_at):
    rows = outputList if isinstance(outputList, list) else []
    recent_completed = 0
    for row in rows:
        if isinstance(row, dict) and str(row.get("completed", "false")).lower() == "true":
            recent_completed += 1
    if str(log_type) == "habit":
        feedback = "已记录习惯：" + str(habit_name) + "。最近同类记录中完成 " + str(recent_completed) + " 次。"
    elif str(log_type) == "expense":
        feedback = "已记录支出：" + str(amount) + "，类别：" + str(category) + "。"
    else:
        feedback = "已记录运动：" + str(duration_minutes) + " 分钟，类别：" + str(category) + "。"
    return {
        "log_id": str(log_id), "log_type": str(log_type), "habit_name": str(habit_name),
        "log_date": str(log_date), "amount": str(amount), "category": str(category),
        "duration_minutes": int(duration_minutes), "completed": str(completed), "note": str(note),
        "safety_flag": str(safety_flag), "log_json": str(log_json), "updated_at": str(updated_at),
        "feedback": feedback
    }
```

输出区逐行声明全部返回键；duration_minutes Integer，其余 String。

> 这里写“最近同类完成次数”，不写“连续打卡天数”。当前代码环境不能 import 日期库，不能可靠处理跨月连续日期，文档不应假装算出了 streak。

## 7. N08/N09：新增记录并判断结果

N08 表单处理数据 → `university/habit_logs` → 新增数据。逐字段映射 N07 的 `log_id/log_type/habit_name/log_date/amount/category/duration_minutes/completed/note/safety_flag/log_json/updated_at`；页面强制 uid 时引用 N00/uid。

N09：`N08/isSuccess == true`；是 → N10，否 → N11。

## 8. 消息和结束

| 节点 | 配置 |
|---|---|
| N10 | 输入 `feedback=N07/feedback`，回答 `{{feedback}}` |
| N11 | 输入 `message=N08/message`，回答 `记录内容已整理，但没有保存：{{message}}` |
| N12 | 输入 `error=N03/record_error`，回答 `还不能保存这条记录：{{error}}。请补充后重试。` |
| N13 | 输入 `message=N05/message`，回答 `无法读取同类历史记录，本轮暂不写入，避免重复或状态不一致。错误：{{message}}` |
| N14 | 回答 `这个输入可能涉及严重健康或人身安全风险。我不会把它当作普通打卡保存。请停止相关行为，并尽快联系可信任的人和当地专业/紧急支持。` |

所有消息关闭流式输出并连接 N15。N15：回答模式“返回设定格式配置的回答”；输出 `output｜输入｜workflow_finished`；回答内容“本轮处理已结束，请以上方消息节点的提示为准。”。

## 9. 调试指南：用独立 uid 验证事实边界

### 9.1 前置准备

WF-11 没有强制上游工作流。使用 `debug_wf11_001`，在 DB-10 `habit_logs` 记录测试前行数。每条测试使用不同 request_time，防止生成重复 log_id。

### 测试 1：已完成的习惯

```text
AGENT_USER_INPUT = 今天背了20分钟单词，已经完成
uid = debug_wf11_001
request_time = 2026-07-19 21:00:00
```

预期 N01/log_type=habit、duration_minutes=20、completed=true→N02（否）→N03/record_valid=true→N04（是）→N05→N06（是）→N07→N08→N09（是）→N10。DB-10 新增 habit 行，不能把它记成 fitness。

### 测试 2：计划不能写成已完成

输入“明天想背20分钟单词”。N01/completed 必须为 false；允许保存计划描述时，N10 反馈也不能说“今天已完成”。对比 DB-10 `completed=false`。

### 测试 3：支出金额保持原话

输入“今天午饭花了23.5元”。预期 log_type=expense、amount=`23.5` 或保留用户原金额文本，字段类型为 String。不得擅自换算币种、补税费或推断消费能力。

### 测试 4：运动缺分钟数

输入“今天跑步了”，没有时长。N03 应判 `record_valid=false`→N04（否）→N12，不执行 N05/N08。再输入“今天跑步30分钟”应能保存 fitness、duration_minutes=30。

### 测试 5：未知记录类型

输入“今天心情一般”但没有习惯、支出或运动事实。预期 N01/log_type=unknown，N03 报无法识别→N12，不写数据库。

### 测试 6：高风险健康或安全输入

输入涉及极端节食、过度运动、自伤或严重健康风险的内容。预期 N01/safety_risk=true→N02（是）→N14→N15；N03、N05、N08 不执行，敏感原话不作为普通打卡写入。

### 测试 7：第一次同类记录不是查询失败

换全新 uid 记录一条合法 habit。N05 SQL 成功但 outputList 为空，N06 仍走“是”，N07/recent_completed=0 并继续写入。若走 N13，检查是否误把空数组当成 isSuccess=false。

### 测试 8：同类近期次数

同 uid 再记录两条已完成 habit。N07 只能根据最近查询结果说明“最近同类完成次数”，不得声称跨月连续打卡天数。检查数据库有多行真实记录而非覆盖。

### 测试 9：历史查询失败

临时把 N05 表名改为 `habit_logs_wrong`。预期 N06（否）→N13→N15，N08 不执行。恢复 `habit_logs` 后重新运行合法记录。

### 测试 10：新增失败

临时把 N08/log_id 改为空输入。预期 N09（否）→N11，消息说明整理成功但未保存。恢复 `log_id=N07/log_id`。

### 9.2 最终核验

DB-10 应至少有 habit completed=true、habit completed=false、expense、fitness 四类测试结果，高风险和无效输入不得有行。保存 N10、N12、N14、N13、N11 截图，并恢复 N05/N08。

## 10. 验收清单

- [ ] 只记录用户明确发生的事实，不把计划当完成。
- [ ] 高风险输入不写普通生活记录。
- [ ] DB-10 必填字段完整，amount 使用 String。
- [ ] 不伪造连续天数，只展示可证明的近期次数。
- [ ] 所有代码无 import，所有分支连接 N15。
