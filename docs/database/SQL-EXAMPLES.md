# 讯飞星辰数据库 SQL 复制手册

## 1. SQL 放在哪里

1. 回到工作流画布。
2. 点击目标“数据库”节点。
3. 右侧“模式”选择“自定义SQL”。
4. 选择正确的数据表。
5. 在“输入”区域添加 SQL 用到的参数。
6. 把本文件中的 SQL 粘贴到“SQL”文本框。

## 2. 参数写法

字符串参数：

```sql
WHERE uid = '{{uid}}'
```

Integer 参数：

```sql
WHERE record_version = {{record_version}}
```

不要把用户原话直接拼进 SQL。先让变量提取器或代码节点生成结构化参数，再引用参数。

## 3. 通用查询

### 3.1 按当前用户读取最新记录

输入参数：`uid`。

```sql
SELECT *
FROM {{table_name}}
WHERE uid = '{{uid}}'
ORDER BY create_time DESC
LIMIT 1;
```

注意：如果平台不允许把表名作为参数，请把 `{{table_name}}` 手动替换成真实表名，不能把表名放在单引号内。

### 3.2 按 uid 和业务键读取

以任务为例，输入参数为 `uid`、`task_id`：

```sql
SELECT *
FROM semester_tasks
WHERE uid = '{{uid}}'
  AND task_id = '{{task_id}}'
ORDER BY updated_at DESC
LIMIT 1;
```

### 3.3 查询当前主规划

```sql
SELECT *
FROM main_plans
WHERE uid = '{{uid}}'
  AND plan_status = 'active'
ORDER BY record_version DESC
LIMIT 1;
```

### 3.4 查询未过期的待确认画像

```sql
SELECT *
FROM user_profiles
WHERE uid = '{{uid}}'
  AND pending_status = 'awaiting_confirmation'
ORDER BY updated_at DESC
LIMIT 1;
```

## 4. WF-01 写入示例

如果平台支持表单模式的新增/更新，优先使用表单模式。下面 SQL 仅在自定义 SQL 支持写入时使用。

### 4.1 新增待确认画像记录

输入参数：`uid`、`pending_profile_json`、`confirmation_token`、`updated_at`。

```sql
INSERT INTO user_profiles (
  uid,
  pending_profile_json,
  confirmation_token,
  pending_status,
  record_version,
  updated_at
) VALUES (
  '{{uid}}',
  '{{pending_profile_json}}',
  '{{confirmation_token}}',
  'awaiting_confirmation',
  1,
  '{{updated_at}}'
);
```

JSON 字符串可能包含引号。必须使用平台参数绑定或平台提供的安全引用方式；如果平台只是文本替换并因此报错，改用“表单处理数据”，不要手工拼接或删除 JSON 内容。

### 4.2 确认后写入正式画像

输入参数：`uid`、`confirmation_token`、`profile_json`、`record_version`、`updated_at`。

```sql
UPDATE user_profiles
SET profile_json = '{{profile_json}}',
    pending_profile_json = '{}',
    confirmation_token = '',
    pending_status = 'confirmed',
    record_version = {{record_version}},
    updated_at = '{{updated_at}}'
WHERE uid = '{{uid}}'
  AND confirmation_token = '{{confirmation_token}}'
  AND pending_status = 'awaiting_confirmation';
```

### 4.3 回读验证

```sql
SELECT profile_json, pending_status, record_version
FROM user_profiles
WHERE uid = '{{uid}}'
  AND record_version = {{record_version}}
ORDER BY updated_at DESC
LIMIT 1;
```

只有回读结果的 `profile_json` 与刚写入内容一致，才能返回 `write_succeeded`。

## 5. 任务示例

### 5.1 查询某规划下的未完成任务

```sql
SELECT *
FROM semester_tasks
WHERE uid = '{{uid}}'
  AND plan_id = '{{plan_id}}'
  AND status IN ('pending', 'in_progress', 'postponed')
ORDER BY deadline ASC;
```

### 5.2 完成任务

```sql
UPDATE semester_tasks
SET status = 'completed',
    actual_evidence = '{{actual_evidence}}',
    updated_at = '{{updated_at}}'
WHERE uid = '{{uid}}'
  AND task_id = '{{task_id}}';
```

## 6. 七天试错示例

### 6.1 读取试错全部记录

```sql
SELECT *
FROM decision_trials
WHERE uid = '{{uid}}'
  AND trial_id = '{{trial_id}}'
ORDER BY day_number ASC, create_time ASC;
```

### 6.2 读取某一天记录

```sql
SELECT *
FROM decision_trials
WHERE uid = '{{uid}}'
  AND trial_id = '{{trial_id}}'
  AND record_type = 'daily_log'
  AND day_number = {{day_number}}
ORDER BY create_time DESC
LIMIT 1;
```

## 7. 会话复盘示例

```sql
SELECT *
FROM session_recaps
WHERE uid = '{{uid}}'
ORDER BY create_time DESC
LIMIT 1;
```

## 8. 空查询和失败处理

数据库节点后必须判断：

```text
isSuccess=false
→ 使用 message 生成失败说明
→ 不进入正式写入或成功回复

isSuccess=true 且 outputList=[]
→ 查询成功但没有历史数据
→ 使用空状态继续

isSuccess=true 且 outputList 有记录
→ 读取所需记录
```

## 9. 删除测试数据

仅用于你自己创建的 `test_user_001`：

```sql
DELETE FROM user_profiles
WHERE uid = 'test_user_001';
```

不要把删除 SQL 放进正式工作流。优先在数据库管理页面筛选并人工删除测试记录。
