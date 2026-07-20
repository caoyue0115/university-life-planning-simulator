# 讯飞星辰数据库：从零建表、导入与调试

本教程对应最终 `MAIN-00 + WF-01～WF-09` 架构。数据库名称固定 `university`，共 11 张表。

## 1. 最终表清单

| 编号 | 表名 | 导入模板 | 主要使用者 |
|---|---|---|---|
| DB-01 | `user_profiles` | [DB-01-user-profiles.xlsx](import-templates/DB-01-user-profiles.xlsx) | WF-01/WF-02/WF-03/WF-04 |
| DB-02 | `simulation_states` | [DB-02-simulation-states.xlsx](import-templates/DB-02-simulation-states.xlsx) | WF-02/WF-03 |
| DB-03 | `route_assessments` | [DB-03-route-assessments.xlsx](import-templates/DB-03-route-assessments.xlsx) | WF-02/WF-03/WF-04 |
| DB-04 | `parallel_versions` | [DB-04-parallel-versions.xlsx](import-templates/DB-04-parallel-versions.xlsx) | WF-05 |
| DB-05 | `main_plans` | [DB-05-main-plans.xlsx](import-templates/DB-05-main-plans.xlsx) | WF-05/WF-06/WF-07 |
| DB-06 | `semester_tasks` | [DB-06-semester-tasks.xlsx](import-templates/DB-06-semester-tasks.xlsx) | WF-06/WF-07 |
| DB-07 | `growth_reviews` | [DB-07-growth-reviews.xlsx](import-templates/DB-07-growth-reviews.xlsx) | WF-07 |
| DB-08 | `resume_entries` | [DB-08-resume-entries.xlsx](import-templates/DB-08-resume-entries.xlsx) | WF-08 |
| DB-09 | `decision_trials` | [DB-09-decision-trials.xlsx](import-templates/DB-09-decision-trials.xlsx) | WF-09 |
| DB-10 | `action_logs` | [DB-10-action-logs.xlsx](import-templates/DB-10-action-logs.xlsx) | WF-06/WF-07 |
| DB-11 | `session_recaps` | [DB-11-session-recaps.xlsx](import-templates/DB-11-session-recaps.xlsx) | WF-07 |

不要创建旧的微习惯专用表。习惯、运动、支出、任务进展和成果证据统一写 `action_logs`。

## 2. 先理解四个身份/顺序字段

平台建表后自动创建三个字段：

- `id`：平台记录主键。
- `uid`：平台系统字段，保留但不用于本项目业务 SQL。
- `create_time`：平台自动创建时间，用于同版本排序。

导入模板显式创建：

- `user_key`：MAIN 生成的会话级业务用户键。

为什么必须有 `user_key`：工作流数据库节点只能引用之前节点里的变量，当前页面没有暴露一个可供 SQL 使用的可信终端账号 ID。所有业务读取范围都从子工作流 N00A 的解析结果引用 `user_key`。

## 3. 进入数据库页面

1. 登录讯飞星辰 Agent 开发平台。
2. 在工作台左侧找到“数据库”。
3. 点击“新建数据库”。
4. 数据库名称填写 `university`。
5. 简介填写：

```text
大学人生规划模拟器的画像、探索、规划、任务、证据、复盘、履历和七天试错业务数据。
```

6. 保存并进入数据库详情。

若账号里已经有 `university`，不要重复创建；先核对表结构是否还是旧版。

## 4. 创建第一张表 user_profiles

### 4.1 新建表

1. 在 `university` 中点击“新建数据表”。
2. 表名填写 `user_profiles`。
3. 简介填写：

```text
保存正式画像、待确认画像草稿和版本状态。
```

4. 创建后确认页面自动出现 `id/uid/create_time`。
5. 不手工删除、改名或再次创建这三个字段。

### 4.2 导入业务字段

1. 点击字段导入或页面等价入口。
2. 选择 [DB-01-user-profiles.xlsx](import-templates/DB-01-user-profiles.xlsx)。
3. 检查预览第一行是：`user_key / String / MAIN 生成的会话级业务用户键 / 空 / 是`。
4. 检查不存在 `confirmation_token` 和 `updated_at`。
5. 确认导入。
6. 保存表结构。

导入完成后，业务字段正好六项：

```text
user_key
profile_json
pending_profile_json
pending_status
record_version
source_workflow
```

## 5. 依次创建其余十张表

对每张表重复“新建表 → 保留系统字段 → 导入对应模板 → 检查 user_key → 保存”。

建议按 DB 编号顺序创建。DB-10 特别检查：

```text
表名 = action_logs
模板 = DB-10-action-logs.xlsx
```

不要把旧 `DB-10-habit-logs.xlsx` 导入后再改表名；新旧字段不同，直接使用新模板。

## 6. 旧表迁移方式

如果平台内已经搭过旧表，不要在正式数据上直接删字段。开发阶段推荐：

1. 先导出或截图需要保留的测试记录。
2. 新建带后缀的临时表，例如 `simulation_states_v2`。
3. 导入新模板并完成工作流调试。
4. 若旧表只有测试数据，确认无用后在平台手工删除旧表并把 v2 表按最终名称重建。
5. 若已有需要保留的真实数据，先增加 `user_key` 并写迁移计划，不把系统 `uid` 直接复制成业务 `user_key`。

本仓库不提供跨用户旧数据自动迁移，因为旧平台 `uid` 与当前 MAIN 会话档案没有可验证映射。

## 7. 在工作流中添加读取节点

以读取当前画像为例：

1. 先连接 `N00 开始 → N00A 解析 → N00B 输入有效 → 数据库`。
2. 点击数据库节点。
3. 模式选择“自定义SQL”。
4. 选择数据库 `university`。
5. 输入区点击“+ 添加”。
6. 参数名填写 `user_key`。
7. 类型选择“引用”。
8. 值选择 `N00A / user_key`。
9. SQL 粘贴：

```sql
SELECT id, user_key, profile_json, pending_profile_json,
       pending_status, record_version, create_time
FROM user_profiles
WHERE user_key='{{user_key}}'
ORDER BY record_version DESC, create_time DESC
LIMIT 1;
```

固定输出：

```text
isSuccess Boolean
message String
outputList Array<Object>
```

## 8. 读取后必须做两次判断

### 8.1 第一次：SQL 是否执行成功

数据库后连接分支器：

- 引用 `数据库/isSuccess`。
- 等于。
- 固定值 `true`。
- 是 → 整理 outputList。
- 默认/否 → 读取失败结果。

### 8.2 第二次：是否有记录

整理代码：

```python
def main(outputList):
    rows = outputList if isinstance(outputList, list) else []
    row = rows[0] if len(rows) > 0 and isinstance(rows[0], dict) else {}
    return {
        "has_record": len(row) > 0,
        "record_id": int(row.get("id", 0)) if str(row.get("id", "0")).isdigit() else 0,
        "record_version": int(row.get("record_version", 0)) if str(row.get("record_version", "0")).isdigit() else 0,
    }
```

再用分支器判断 `has_record == true`。第一次运行通常是 `isSuccess=true` 且 `has_record=false`，这条路线必须正常初始化，不能显示数据库错误。

## 9. 新增数据节点

以新增一条行动日志为例：

1. 数据库模式选择“表单处理数据”。
2. 数据表选择 `university / action_logs`。
3. 处理模式选择“新增数据”。
4. 在“设置新增数据”逐行添加：

| 表字段 | 类型 | 引用值 |
|---|---|---|
| `user_key` | 引用 | N00A/user_key |
| `log_id` | 引用 | 准备代码/log_id |
| `task_id` | 引用 | 准备代码/task_id |
| `log_type` | 引用 | 准备代码/log_type |
| `content_json` | 引用 | 准备代码/content_json |
| `evidence_text` | 引用 | 准备代码/evidence_text |
| `day_number` | 引用 | 准备代码/day_number |
| `completed` | 引用 | 准备代码/completed_text |
| `safety_flag` | 引用 | 准备代码/safety_flag |
| `record_version` | 引用 | 准备代码/record_version |

不要添加 `id/uid/create_time`。数据库后检查 `isSuccess`。

## 10. 更新数据节点

只有确实需要改变当前实体状态时才更新。以确认画像为例：

“设置数据范围”使用 AND：

| 表字段 | 条件 | 比较类型 | 值 |
|---|---|---|---|
| `user_key` | 等于 | 引用 | N00A/user_key |
| `id` | 等于 | 引用 | 整理状态/record_id |
| `pending_status` | 等于 | 固定值 | `awaiting_confirmation` |

“设置更新数据”：

| 字段 | 值 |
|---|---|
| `profile_json` | 已校验 pending JSON |
| `pending_profile_json` | `{}` |
| `pending_status` | `confirmed` |
| `record_version` | 当前版本 + 1 |

更新后再按同一 `user_key` 回读并比较正式 JSON、状态和版本。

## 11. 版本号怎么计算

模型不生成版本号。整理最新记录后输出：

```python
def main(outputList):
    rows = outputList if isinstance(outputList, list) else []
    row = rows[0] if len(rows) > 0 and isinstance(rows[0], dict) else {}
    try:
        current_version = int(row.get("record_version", 0))
    except:
        current_version = 0
    return {
        "current_version": current_version,
        "next_version": current_version + 1,
    }
```

不同表把字段名替换为 `state_version` 或 `assessment_version`。业务键可组合 `user_key + 固定前缀 + next_version`，不使用调用方时间。

## 12. 调试 DB-01

### 12.1 新用户空查询

用子工作流唯一输入：

```json
{"user_key":"uk_11111111111111111111111111111111","user_input":"建立画像"}
```

预期：SQL `isSuccess=true`、`outputList=[]`，之后初始化画像草稿。

### 12.2 有记录查询

先通过 WF-01 写入该 user_key 的 pending 或 confirmed 记录，再运行相同输入。预期 outputList 只含该档案最新行。

### 12.3 SQL 失败

临时把表名改成 `user_profiles_wrong`。预期 `isSuccess=false`，进入 read_failed，不能当成无记录。测试后恢复 `user_profiles`。

### 12.4 两个档案隔离

分别使用：

```text
uk_11111111111111111111111111111111
uk_22222222222222222222222222222222
```

为两者写不同画像。分别查询时 outputList 只能出现自己的记录。调试截图不要对最终用户展示完整 key。

## 13. 调试新增和回读

1. 记录新增前目标表行数。
2. 运行正常新增。
3. 检查数据库节点 `isSuccess=true`。
4. 运行回读 SQL。
5. 检查 user_key、业务键、状态和版本完全一致。
6. 临时改错表名制造写入失败。
7. 确认回复不含“已保存”。
8. 恢复正确表名。

## 14. 测试数据清理

只清理明确的测试 `user_key`，不要清空整张表。平台 UI 支持筛选后删除时，先按完整 user_key 筛选并核对行数；若使用删除 SQL，必须同时写 user_key 和具体业务键。

清理前保存需要的 Trace 和截图。正式发布数据不在本教程中批量删除。

## 15. 验收清单

- [ ] 数据库名为 `university`。
- [ ] 正好 11 张最终表。
- [ ] DB-10 是 `action_logs`。
- [ ] 所有表保留系统 id/uid/create_time。
- [ ] 所有模板第一项业务字段是 user_key。
- [ ] 没有 confirmation_token 和 updated_at 业务字段。
- [ ] 工作流开始节点不接收 request_time。
- [ ] 所有读取按 user_key 过滤。
- [ ] 空记录和 SQL 失败分别测试。
- [ ] 所有关键写入检查 isSuccess 并回读。
- [ ] 两个测试档案互不可读。
