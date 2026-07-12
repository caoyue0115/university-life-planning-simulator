# 讯飞星辰数据库字段字典

## 1. 先理解三个系统字段

在讯飞星辰中新建任意数据表后，平台会自动创建以下字段，界面中通常无法删除：

| 字段 | 类型 | 用法 |
|---|---|---|
| `id` | Integer | 平台生成的记录主键。更新或删除单条记录时优先使用它。 |
| `uid` | String | 平台生成的用户唯一标识。所有用户数据查询都必须带上它。 |
| `create_time` | Time | 平台记录的创建时间。 |

11 份导入模板只包含下面列出的“业务字段”，不要再次添加 `id`、`uid`、`create_time`。

## 2. 字段类型约定

- JSON、数组、长文本：使用 `String`，写入前由工作流转成 JSON 字符串。
- 时间：使用 `Time`。
- 次数、天数、版本号：使用 `Integer`。
- 是否状态如果平台没有 Boolean：使用 `String`，值固定为 `true/false`。
- “必填”仅表示写入这类记录时必须提供；系统默认三字段由平台负责。

## DB-01 `user_profiles`：用户画像

数据表名称填写：`user_profiles`  
数据表简介填写：`保存正式用户画像、待确认画像草稿及确认令牌。`

| 字段名 | 类型 | 描述 | 默认值 | 必填 |
|---|---|---|---|---|
| `profile_json` | String | 已由用户确认的正式画像 JSON | `{}` | 否 |
| `pending_profile_json` | String | 等待用户确认的画像草稿 JSON | `{}` | 否 |
| `confirmation_token` | String | 当前待确认草稿的令牌 | 空 | 否 |
| `pending_status` | String | `none/awaiting_confirmation/confirmed/expired` | `none` | 是 |
| `record_version` | Integer | 画像记录版本号 | `1` | 是 |
| `updated_at` | Time | 最后修改时间 | 空 | 是 |

业务键：同一 `uid` 保留一条当前画像记录；历史版本需要保留时按 `uid + record_version` 查询。

## DB-02 `simulation_states`：模拟与测试续接状态

数据表名称填写：`simulation_states`  
数据表简介填写：`保存虚拟大学和生存大冒险的跨轮状态。`

| 字段名 | 类型 | 描述 | 默认值 | 必填 |
|---|---|---|---|---|
| `state_id` | String | 业务状态标识 | 空 | 是 |
| `workflow_id` | String | `WF-02` 或 `WF-03` | 空 | 是 |
| `state_type` | String | `simulation/adventure` | 空 | 是 |
| `state_json` | String | 完整续接状态 JSON | `{}` | 是 |
| `pending_item_json` | String | 待回答事件或问题 JSON | `{}` | 否 |
| `current_index` | Integer | 当前事件或题目序号 | `0` | 是 |
| `completed` | String | 是否完成，`true/false` | `false` | 是 |
| `updated_at` | Time | 最后更新时间 | 空 | 是 |

业务键：`uid + workflow_id + state_id`。

## DB-03 `route_assessments`：路径评估

数据表名称填写：`route_assessments`  
数据表简介填写：`保存生存测试结果和五路径推荐。`

| 字段名 | 类型 | 描述 | 默认值 | 必填 |
|---|---|---|---|---|
| `assessment_id` | String | 评估业务标识 | 空 | 是 |
| `adventure_result_json` | String | WF-03 测试结果 JSON | `{}` | 否 |
| `route_recommendation_json` | String | WF-04 五路径推荐 JSON | `{}` | 否 |
| `trigger_reason` | String | 首次评估或重新评估原因 | 空 | 是 |
| `knowledge_updated_at` | Time | 本次使用的知识更新时间 | 空 | 否 |
| `assessment_version` | Integer | 评估版本 | `1` | 是 |
| `updated_at` | Time | 最后更新时间 | 空 | 是 |

业务键：`uid + assessment_id`；历史评估不覆盖。

## DB-04 `parallel_versions`：平行人生

数据表名称填写：`parallel_versions`  
数据表简介填写：`保存平行人生版本及统一维度比较结果。`

| 字段名 | 类型 | 描述 | 默认值 | 必填 |
|---|---|---|---|---|
| `comparison_id` | String | 一次平行人生比较标识 | 空 | 是 |
| `versions_json` | String | 2～3 个平行版本 JSON | `[]` | 是 |
| `comparison_json` | String | 统一维度比较结果 JSON | `{}` | 是 |
| `shared_baseline_json` | String | 各版本共用的初始条件 | `{}` | 是 |
| `selected_version_name` | String | 用户当前选中的版本名 | 空 | 否 |
| `comparison_version` | Integer | 比较版本 | `1` | 是 |
| `updated_at` | Time | 最后更新时间 | 空 | 是 |

业务键：`uid + comparison_id`。

## DB-05 `main_plans`：主规划

数据表名称填写：`main_plans`  
数据表简介填写：`保存主规划、历史规划和待确认规划变更。`

| 字段名 | 类型 | 描述 | 默认值 | 必填 |
|---|---|---|---|---|
| `plan_id` | String | 主规划业务标识 | 空 | 是 |
| `plan_json` | String | 当前或历史规划 JSON | `{}` | 是 |
| `plan_status` | String | `pending/active/history/archived` | `pending` | 是 |
| `pending_plan_json` | String | 待确认规划 JSON | `{}` | 否 |
| `confirmation_token` | String | 待确认规划令牌 | 空 | 否 |
| `source_comparison_id` | String | 来源平行人生比较标识 | 空 | 否 |
| `change_reason` | String | 保存、切换或覆盖原因 | 空 | 否 |
| `record_version` | Integer | 规划版本 | `1` | 是 |
| `updated_at` | Time | 最后更新时间 | 空 | 是 |

业务键：`uid + plan_id + record_version`；当前主规划用 `plan_status=active` 查询。

## DB-06 `semester_tasks`：学期任务与行动

数据表名称填写：`semester_tasks`  
数据表简介填写：`保存学期、月度、每周任务和执行证据。`

| 字段名 | 类型 | 描述 | 默认值 | 必填 |
|---|---|---|---|---|
| `task_id` | String | 任务业务标识 | 空 | 是 |
| `plan_id` | String | 所属主规划标识 | 空 | 是 |
| `semester` | String | 所属学期 | 空 | 是 |
| `month` | String | 所属月份或月度阶段 | 空 | 否 |
| `week` | String | 所属周 | 空 | 否 |
| `task` | String | 任务内容 | 空 | 是 |
| `deadline` | Time | 截止时间 | 空 | 否 |
| `priority` | String | `高/中/低` | `中` | 是 |
| `status` | String | `pending/in_progress/completed/postponed/cancelled` | `pending` | 是 |
| `expected_evidence` | String | 预期成果证据 | 空 | 否 |
| `actual_evidence` | String | 实际成果证据 | 空 | 否 |
| `delay_reason` | String | 延期原因 | 空 | 否 |
| `action_log_json` | String | 行动和变更记录 JSON | `[]` | 否 |
| `updated_at` | Time | 最后更新时间 | 空 | 是 |

业务键：`uid + task_id`。

## DB-07 `growth_reviews`：成长复盘

数据表名称填写：`growth_reviews`  
数据表简介填写：`保存成长证据、动态修正建议和待确认动作。`

| 字段名 | 类型 | 描述 | 默认值 | 必填 |
|---|---|---|---|---|
| `review_id` | String | 复盘业务标识 | 空 | 是 |
| `plan_id` | String | 被复盘的主规划 | 空 | 否 |
| `review_json` | String | 成长复盘结果 JSON | `{}` | 是 |
| `recommendation_type` | String | `continue/adjust/consider_switch` | `continue` | 是 |
| `pending_change_json` | String | 待确认的规划或任务变更 | `{}` | 否 |
| `confirmation_token` | String | 待确认变更令牌 | 空 | 否 |
| `evidence_summary_json` | String | 行为证据汇总 JSON | `{}` | 是 |
| `updated_at` | Time | 最后更新时间 | 空 | 是 |

业务键：`uid + review_id`。

## DB-08 `resume_entries`：履历素材

数据表名称填写：`resume_entries`  
数据表简介填写：`保存履历事实、待确认草稿和正式履历条目。`

| 字段名 | 类型 | 描述 | 默认值 | 必填 |
|---|---|---|---|---|
| `entry_id` | String | 履历条目业务标识 | 空 | 是 |
| `entry_type` | String | 项目、科研、竞赛、实习、社团等 | 空 | 是 |
| `resume_entry_json` | String | 正式履历条目 JSON | `{}` | 否 |
| `pending_entry_json` | String | 待确认履历草稿 JSON | `{}` | 否 |
| `confirmation_token` | String | 待确认履历令牌 | 空 | 否 |
| `quality_status` | String | 可用、缺量化、缺证明、需打磨 | `需打磨` | 是 |
| `evidence_location` | String | 证明材料位置 | 空 | 否 |
| `record_status` | String | `pending/confirmed/archived` | `pending` | 是 |
| `updated_at` | Time | 最后更新时间 | 空 | 是 |

业务键：`uid + entry_id`。

## DB-09 `decision_trials`：决策与七天试错

数据表名称填写：`decision_trials`  
数据表简介填写：`保存决策分析、七天试错计划和每日记录。`

| 字段名 | 类型 | 描述 | 默认值 | 必填 |
|---|---|---|---|---|
| `trial_id` | String | 试错或决策业务标识 | 空 | 是 |
| `record_type` | String | `analysis/plan/daily_log/day7_review` | 空 | 是 |
| `decision_json` | String | 即时决策分析 JSON | `{}` | 否 |
| `trial_plan_json` | String | 正式七天计划 JSON | `{}` | 否 |
| `pending_json` | String | 待确认计划或复盘 JSON | `{}` | 否 |
| `confirmation_token` | String | 待确认令牌 | 空 | 否 |
| `day_number` | Integer | 第几天，1～7 | `0` | 否 |
| `daily_log_json` | String | 单日记录 JSON | `{}` | 否 |
| `review_json` | String | 第七天复盘 JSON | `{}` | 否 |
| `trial_status` | String | `pending/active/completed/stopped` | `pending` | 是 |
| `updated_at` | Time | 最后更新时间 | 空 | 是 |

业务键：`uid + trial_id + record_type + day_number`。

## DB-10 `habit_logs`：微习惯与生活记录

数据表名称填写：`habit_logs`  
数据表简介填写：`保存习惯、记账、入门健身和安全提示记录。`

| 字段名 | 类型 | 描述 | 默认值 | 必填 |
|---|---|---|---|---|
| `log_id` | String | 生活记录业务标识 | 空 | 是 |
| `log_type` | String | `habit/expense/fitness/safety` | 空 | 是 |
| `habit_name` | String | 习惯名称 | 空 | 否 |
| `log_date` | Time | 记录日期 | 空 | 是 |
| `amount` | String | 支出金额；平台无 Decimal 时使用 String | 空 | 否 |
| `category` | String | 支出或活动类别 | 空 | 否 |
| `duration_minutes` | Integer | 持续分钟数 | `0` | 否 |
| `completed` | String | `true/false` | `true` | 是 |
| `note` | String | 说明、休息日或补签原因 | 空 | 否 |
| `safety_flag` | String | `none/stop_and_seek_help` | `none` | 是 |
| `log_json` | String | 完整记录 JSON | `{}` | 否 |
| `updated_at` | Time | 最后更新时间 | 空 | 是 |

业务键：`uid + log_id`。

## DB-11 `session_recaps`：会话复盘

数据表名称填写：`session_recaps`  
数据表简介填写：`保存会话新增事实、状态变化、未决问题和下次入口。`

| 字段名 | 类型 | 描述 | 默认值 | 必填 |
|---|---|---|---|---|
| `session_id` | String | 会话业务标识 | 空 | 是 |
| `user_recap_json` | String | 给用户看的复盘 JSON | `{}` | 是 |
| `agent_recap_json` | String | 给 Agent 续接的复盘 JSON | `{}` | 是 |
| `new_facts_json` | String | 本轮新增且允许保存的事实 | `[]` | 否 |
| `state_changes_json` | String | 本轮成功发生的状态变化 | `[]` | 否 |
| `open_questions_json` | String | 未决问题 JSON | `[]` | 否 |
| `next_entry` | String | 下次会话建议入口 | 空 | 是 |
| `recap_version` | Integer | 复盘版本 | `1` | 是 |
| `updated_at` | Time | 最后更新时间 | 空 | 是 |

业务键：`uid + session_id`。

## 3. 通用数据规则

1. 所有查询条件必须包含系统字段 `uid`。
2. 查询单个业务对象时同时带业务键，例如 `uid + task_id`。
3. 正式数据和待确认草稿必须放在不同字段或不同状态记录中。
4. `isSuccess=true` 且 `outputList=[]` 表示查询成功但没有数据，不是数据库错误。
5. 更新单条记录优先使用系统 `id`；只有拿不到 `id` 时才用 `uid + 业务键`。
6. JSON 字段写入数据库前必须完成结构校验。
