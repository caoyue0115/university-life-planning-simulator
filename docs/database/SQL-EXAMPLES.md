# 讯飞星辰数据库 SQL 复制手册

读取统一使用数据库节点“自定义SQL”。新增和更新优先使用“表单处理数据”；本手册仍给出回读、故障定位和受限清理所需 SQL。

## 1. 参数配置规则

SQL 中出现 `{{user_key}}` 前，数据库节点输入区必须添加：

```text
参数名：user_key
类型：引用
值：N00A 代码：解析包装 / user_key
```

业务键参数同理引用上游代码或查询结果，不能要求用户在自然语言中复制。

## 2. 通用最新记录

```sql
SELECT id, user_key, record_version, create_time
FROM example_table
WHERE user_key='{{user_key}}'
ORDER BY record_version DESC, create_time DESC
LIMIT 1;
```

把 `example_table` 和版本字段替换成目标表。任何业务 SELECT 都保留 user_key 条件。

## 3. DB-01 画像

### 3.1 读取当前画像和 pending

```sql
SELECT id, user_key, profile_json, pending_profile_json,
       pending_status, record_version, source_workflow, create_time
FROM user_profiles
WHERE user_key='{{user_key}}'
ORDER BY record_version DESC, create_time DESC
LIMIT 1;
```

### 3.2 回读确认后的画像

```sql
SELECT id, user_key, profile_json, pending_status,
       record_version, create_time
FROM user_profiles
WHERE user_key='{{user_key}}'
  AND pending_status='confirmed'
ORDER BY record_version DESC, create_time DESC
LIMIT 1;
```

## 4. DB-02 探索状态

### 4.1 读取 WF-02 最新状态

```sql
SELECT id, user_key, state_id, state_json, pending_item_json,
       state_version, current_index, completed, create_time
FROM simulation_states
WHERE user_key='{{user_key}}'
  AND workflow_id='WF-02'
  AND state_type='simulation'
ORDER BY state_version DESC, create_time DESC
LIMIT 1;
```

### 4.2 读取 WF-03 最新状态

```sql
SELECT id, user_key, state_id, state_json, pending_item_json,
       state_version, current_index, completed, create_time
FROM simulation_states
WHERE user_key='{{user_key}}'
  AND workflow_id='WF-03'
  AND state_type='adventure'
ORDER BY state_version DESC, create_time DESC
LIMIT 1;
```

### 4.3 读取两种已完成探索

```sql
SELECT id, user_key, workflow_id, state_json,
       state_version, current_index, create_time
FROM simulation_states
WHERE user_key='{{user_key}}'
  AND completed='true'
ORDER BY create_time DESC;
```

WF-04 的整理代码分别选择最新 WF-02 和 WF-03 行，不能假设两者都存在。

## 5. DB-03 五路径评估

```sql
SELECT id, user_key, assessment_id, simulation_result_json,
       adventure_result_json, route_recommendation_json,
       evidence_sources, evidence_gaps_json, confidence_level,
       knowledge_version, assessment_version, create_time
FROM route_assessments
WHERE user_key='{{user_key}}'
ORDER BY assessment_version DESC, create_time DESC
LIMIT 1;
```

## 6. DB-04/DB-05 方向和主规划

### 6.1 最新方向比较

```sql
SELECT id, user_key, comparison_id, versions_json,
       comparison_json, selected_version_name,
       comparison_status, record_version, create_time
FROM parallel_versions
WHERE user_key='{{user_key}}'
ORDER BY record_version DESC, create_time DESC
LIMIT 1;
```

### 6.2 当前 active 主规划

```sql
SELECT id, user_key, plan_id, plan_json,
       source_comparison_id, change_reason,
       record_version, create_time
FROM main_plans
WHERE user_key='{{user_key}}'
  AND plan_status='active'
ORDER BY record_version DESC, create_time DESC
LIMIT 1;
```

### 6.3 最新 pending 主规划

```sql
SELECT id, user_key, plan_id, pending_plan_json,
       source_comparison_id, record_version, create_time
FROM main_plans
WHERE user_key='{{user_key}}'
  AND plan_status='pending'
ORDER BY record_version DESC, create_time DESC
LIMIT 1;
```

## 7. DB-06/DB-10 任务和行动

### 7.1 当前任务列表

```sql
SELECT id, user_key, task_id, plan_id, task_type,
       semester, period_label, task, deadline_text,
       priority, status, expected_evidence, latest_evidence,
       delay_reason, record_version, create_time
FROM semester_tasks
WHERE user_key='{{user_key}}'
  AND status IN ('pending','in_progress','postponed')
ORDER BY priority DESC, create_time DESC;
```

### 7.2 指定任务最新版本

```sql
SELECT id, user_key, task_id, plan_id, task_type,
       task, status, expected_evidence, latest_evidence,
       record_version, create_time
FROM semester_tasks
WHERE user_key='{{user_key}}'
  AND task_id='{{task_id}}'
ORDER BY record_version DESC, create_time DESC
LIMIT 1;
```

### 7.3 指定任务行动日志

```sql
SELECT id, user_key, log_id, task_id, log_type,
       content_json, evidence_text, day_number,
       completed, safety_flag, record_version, create_time
FROM action_logs
WHERE user_key='{{user_key}}'
  AND task_id='{{task_id}}'
ORDER BY create_time DESC;
```

### 7.4 最近全部行动证据

```sql
SELECT id, user_key, log_id, task_id, log_type,
       content_json, evidence_text, completed,
       safety_flag, record_version, create_time
FROM action_logs
WHERE user_key='{{user_key}}'
ORDER BY create_time DESC
LIMIT 50;
```

## 8. DB-07 复盘

```sql
SELECT id, user_key, review_id, plan_id,
       review_json, recommendation_type,
       evidence_summary_json, evidence_gaps_json,
       pending_change_json, record_version, create_time
FROM growth_reviews
WHERE user_key='{{user_key}}'
ORDER BY record_version DESC, create_time DESC
LIMIT 1;
```

## 9. DB-08 履历

### 9.1 最新 pending 履历

```sql
SELECT id, user_key, entry_id, entry_type,
       pending_entry_json, quality_status,
       evidence_location, record_version, create_time
FROM resume_entries
WHERE user_key='{{user_key}}'
  AND record_status='pending'
ORDER BY record_version DESC, create_time DESC
LIMIT 1;
```

### 9.2 正式履历列表

```sql
SELECT id, user_key, entry_id, entry_type,
       resume_entry_json, quality_status,
       evidence_location, record_version, create_time
FROM resume_entries
WHERE user_key='{{user_key}}'
  AND record_status='confirmed'
ORDER BY create_time DESC;
```

## 10. DB-09 七天试错

### 10.1 当前 pending/active 计划

```sql
SELECT id, user_key, trial_id, record_type,
       decision_json, trial_plan_json, pending_json,
       day_number, trial_status, record_version, create_time
FROM decision_trials
WHERE user_key='{{user_key}}'
  AND trial_status IN ('pending','active')
ORDER BY record_version DESC, create_time DESC
LIMIT 1;
```

### 10.2 某次试错全部记录

```sql
SELECT id, user_key, trial_id, record_type,
       trial_plan_json, daily_log_json, review_json,
       day_number, trial_status, record_version, create_time
FROM decision_trials
WHERE user_key='{{user_key}}'
  AND trial_id='{{trial_id}}'
ORDER BY record_version ASC, create_time ASC;
```

## 11. DB-11 会话收束

```sql
SELECT id, user_key, recap_id, user_recap_json,
       agent_recap_json, new_facts_json,
       state_changes_json, open_questions_json,
       next_action, record_version, create_time
FROM session_recaps
WHERE user_key='{{user_key}}'
ORDER BY record_version DESC, create_time DESC
LIMIT 1;
```

## 12. 更新范围示例

正式更新在平台“表单处理数据”中配置，不直接粘贴 SQL。等价范围必须同时包含业务用户和实体：

```sql
UPDATE user_profiles
SET pending_status='confirmed', record_version={{next_version}}
WHERE user_key='{{user_key}}'
  AND id={{record_id}}
  AND pending_status='awaiting_confirmation';
```

教程实际配置还会更新画像 JSON 并清空 pending。此 SQL 只用于理解范围，不能省略 user_key。

## 13. 删除测试数据

只允许删除明确测试档案和具体实体：

```sql
DELETE FROM simulation_states
WHERE user_key='{{user_key}}'
  AND workflow_id='WF-02';
```

不要执行无 user_key 的 DELETE，不要把数据库名或整张正式表作为批量清理目标。

## 14. 空查询和失败

| 数据库输出 | 含义 | 处理 |
|---|---|---|
| `isSuccess=true, outputList=[]` | SQL 正常、没有记录 | 进入首次/缺前置路线 |
| `isSuccess=true, outputList=[...]` | SQL 正常、有记录 | 整理并继续 |
| `isSuccess=false` | SQL 执行失败 | 返回 read_failed，不生成或写入 |

所有工作流都先检查 `isSuccess`，再检查 outputList。
