# 讯飞星辰数据库字段字典

本项目使用数据库 `university`，共 11 张表。最新字段导入模板位于 [import-templates](import-templates/)。

## 1. 系统字段和业务用户键

讯飞星辰新建表后会自动创建：

| 字段 | 来源 | 本项目用法 |
|---|---|---|
| `id` | 平台自动 | 单行定位、更新和调试 |
| `uid` | 平台自动 | 仅保留；当前页面没有把它暴露为可供 SQL 引用的可信终端用户身份 |
| `create_time` | 平台自动 | 记录创建顺序；调用方不再传 request_time |

每份导入模板的第一项业务字段都是：

| 字段 | 类型 | 规则 |
|---|---|---|
| `user_key` | String | MAIN 首轮生成并在同一对话保存；所有业务 SQL、更新范围和回读都必须使用 |

不要删除系统 `uid`，也不要把它映射成 `user_key`。二者并存，但只有 `user_key` 是当前产品明确可控的业务隔离键。

## 2. 类型与版本规则

- JSON、数组和长文本：`String`。
- 次数、天数和版本：`Integer`。
- Boolean 状态：为了兼容数据库字段，用 String 值 `true/false`。
- 截止时间：使用 `deadline_text:String` 保存用户原话，不要求入口提供系统时间。
- 创建顺序：平台 `create_time`。
- 业务顺序：每张表的 `record_version/state_version/assessment_version`。
- 不再创建外部 confirmation token 或 `updated_at` 业务字段。
- 关键状态优先追加版本；确需更新时按 `user_key + 业务键 + 状态/版本` 限定范围。

## DB-01 `user_profiles`：用户画像

表简介：`保存正式画像、待确认画像草稿和版本状态。`

| 字段名 | 类型 | 描述 | 默认值 | 必填 |
|---|---|---|---|---|
| `user_key` | String | 会话级业务用户键 | 空 | 是 |
| `profile_json` | String | 用户确认的正式画像 JSON | `{}` | 否 |
| `pending_profile_json` | String | 等待确认的画像草稿 JSON | `{}` | 否 |
| `pending_status` | String | `none/awaiting_confirmation/confirmed/cancelled` | `none` | 是 |
| `record_version` | Integer | 画像版本号 | `1` | 是 |
| `source_workflow` | String | 固定 `WF-01` | `WF-01` | 是 |

业务键：`user_key`。同一用户保留一条当前画像记录；更新前后使用 `record_version`，回读按版本和 `create_time` 排序。

## DB-02 `simulation_states`：WFB 多轮续接

表简介：`保存虚拟大学和生存大冒险的跨轮状态。`

| 字段名 | 类型 | 描述 | 默认值 | 必填 |
|---|---|---|---|---|
| `user_key` | String | 会话级业务用户键 | 空 | 是 |
| `state_id` | String | 状态实体标识 | 空 | 是 |
| `workflow_id` | String | `WF-02/WF-03` | 空 | 是 |
| `state_type` | String | `simulation/adventure` | 空 | 是 |
| `state_json` | String | 完整已结算状态 JSON | `{}` | 是 |
| `pending_item_json` | String | 待回答事件或问题 JSON | `{}` | 否 |
| `state_version` | Integer | 追加状态版本 | `1` | 是 |
| `current_index` | Integer | 当前事件/题目序号 | `0` | 是 |
| `completed` | String | `true/false` | `false` | 是 |

业务键：`user_key + workflow_id + state_id + state_version`。WF-02 与 WF-03 不能互相覆盖状态。

## DB-03 `route_assessments`：探索证据与五路径推荐

表简介：`汇总 WF-02/WF-03 探索证据和 WF-04 五路径推荐。`

| 字段名 | 类型 | 描述 | 默认值 | 必填 |
|---|---|---|---|---|
| `user_key` | String | 会话级业务用户键 | 空 | 是 |
| `assessment_id` | String | 评估业务标识 | 空 | 是 |
| `simulation_result_json` | String | WF-02 完成结果 | `{}` | 否 |
| `adventure_result_json` | String | WF-03 完成结果 | `{}` | 否 |
| `route_recommendation_json` | String | WF-04 五路径推荐 | `{}` | 否 |
| `evidence_sources` | String | 使用的 `WF-02/WF-03` 来源列表 | 空 | 否 |
| `evidence_gaps_json` | String | 缺失探索证据 | `[]` | 否 |
| `confidence_level` | String | `low/medium/high` | `low` | 是 |
| `trigger_reason` | String | 首次/重新评估原因 | 空 | 是 |
| `knowledge_version` | String | 知识库版本说明 | 空 | 否 |
| `assessment_version` | Integer | 评估版本 | `1` | 是 |

业务键：`user_key + assessment_id + assessment_version`。WF-04 读取同一用户最新的两种证据，允许仅有一种。

## DB-04 `parallel_versions`：方向比较

表简介：`保存候选方向的平行版本和统一维度比较。`

| 字段名 | 类型 | 描述 | 默认值 | 必填 |
|---|---|---|---|---|
| `user_key` | String | 会话级业务用户键 | 空 | 是 |
| `comparison_id` | String | 一次方向比较标识 | 空 | 是 |
| `versions_json` | String | 2～3 个方向版本 | `[]` | 是 |
| `comparison_json` | String | 统一维度比较结果 | `{}` | 是 |
| `shared_baseline_json` | String | 共同初始条件 | `{}` | 是 |
| `selected_version_name` | String | 用户选中的版本名 | 空 | 否 |
| `comparison_status` | String | `draft/selected/archived` | `draft` | 是 |
| `record_version` | Integer | 方向比较版本 | `1` | 是 |

业务键：`user_key + comparison_id + record_version`。

## DB-05 `main_plans`：主规划

表简介：`保存主规划草稿、当前 active 规划和历史版本。`

| 字段名 | 类型 | 描述 | 默认值 | 必填 |
|---|---|---|---|---|
| `user_key` | String | 会话级业务用户键 | 空 | 是 |
| `plan_id` | String | 主规划业务标识 | 空 | 是 |
| `plan_json` | String | 正式/历史规划 JSON | `{}` | 是 |
| `pending_plan_json` | String | 待确认规划 JSON | `{}` | 否 |
| `plan_status` | String | `pending/active/history/cancelled` | `pending` | 是 |
| `source_comparison_id` | String | 来源方向比较标识 | 空 | 否 |
| `change_reason` | String | 创建、切换或修改原因 | 空 | 否 |
| `record_version` | Integer | 主规划版本 | `1` | 是 |

业务键：`user_key + plan_id + record_version`。当前规划查询额外限定 `plan_status='active'`。

## DB-06 `semester_tasks`：任务定义和当前状态

表简介：`保存学期任务、优先级、状态和最近证据。`

| 字段名 | 类型 | 描述 | 默认值 | 必填 |
|---|---|---|---|---|
| `user_key` | String | 会话级业务用户键 | 空 | 是 |
| `task_id` | String | 任务业务标识 | 空 | 是 |
| `plan_id` | String | 所属 active 主规划 | 空 | 是 |
| `task_type` | String | `academic/project/research/career/habit/fitness/finance/life` | `academic` | 是 |
| `semester` | String | 所属学期 | 空 | 是 |
| `period_label` | String | 月份、周次或阶段 | 空 | 否 |
| `task` | String | 任务内容 | 空 | 是 |
| `deadline_text` | String | 用户表达的截止日期/检查点 | 空 | 否 |
| `priority` | String | `高/中/低` | `中` | 是 |
| `status` | String | `pending/in_progress/completed/postponed/cancelled` | `pending` | 是 |
| `expected_evidence` | String | 预期成果证据 | 空 | 否 |
| `latest_evidence` | String | 最近已验证证据 | 空 | 否 |
| `delay_reason` | String | 延期原因 | 空 | 否 |
| `record_version` | Integer | 任务版本 | `1` | 是 |

业务键：`user_key + task_id + record_version`。完整进展历史写 DB-10，不把不断增长的日志数组塞回任务行。

## DB-07 `growth_reviews`：成长复盘

表简介：`保存基于规划、任务和行动证据的成长复盘。`

| 字段名 | 类型 | 描述 | 默认值 | 必填 |
|---|---|---|---|---|
| `user_key` | String | 会话级业务用户键 | 空 | 是 |
| `review_id` | String | 复盘业务标识 | 空 | 是 |
| `plan_id` | String | 被复盘主规划 | 空 | 否 |
| `review_json` | String | 完整复盘 JSON | `{}` | 是 |
| `recommendation_type` | String | `continue/adjust/consider_switch` | `continue` | 是 |
| `evidence_summary_json` | String | 已验证证据摘要 | `{}` | 是 |
| `evidence_gaps_json` | String | 证据缺口 | `[]` | 否 |
| `pending_change_json` | String | 建议后续确认的变更 | `{}` | 否 |
| `record_version` | Integer | 复盘版本 | `1` | 是 |

业务键：`user_key + review_id + record_version`。WF-07 不直接覆盖 DB-05。

## DB-08 `resume_entries`：履历证据

表简介：`保存真实经历的待确认草稿和正式履历条目。`

| 字段名 | 类型 | 描述 | 默认值 | 必填 |
|---|---|---|---|---|
| `user_key` | String | 会话级业务用户键 | 空 | 是 |
| `entry_id` | String | 履历条目业务标识 | 空 | 是 |
| `entry_type` | String | 项目/科研/竞赛/实习/社团等 | 空 | 是 |
| `resume_entry_json` | String | 正式履历 JSON | `{}` | 否 |
| `pending_entry_json` | String | 待确认履历 JSON | `{}` | 否 |
| `quality_status` | String | `可用/缺量化/缺证明/需打磨` | `需打磨` | 是 |
| `evidence_location` | String | 证明材料位置 | 空 | 否 |
| `record_status` | String | `pending/confirmed/cancelled/archived` | `pending` | 是 |
| `record_version` | Integer | 履历版本 | `1` | 是 |

业务键：`user_key + entry_id + record_version`。

## DB-09 `decision_trials`：决策与七天试错

表简介：`保存七天试错计划、每日记录、复盘和状态版本。`

| 字段名 | 类型 | 描述 | 默认值 | 必填 |
|---|---|---|---|---|
| `user_key` | String | 会话级业务用户键 | 空 | 是 |
| `trial_id` | String | 试错业务标识 | 空 | 是 |
| `record_type` | String | `analysis/plan/daily_log/day7_review` | 空 | 是 |
| `decision_json` | String | 即时决策分析 | `{}` | 否 |
| `trial_plan_json` | String | 正式七天计划 | `{}` | 否 |
| `pending_json` | String | 待确认计划/复盘 | `{}` | 否 |
| `day_number` | Integer | 第 1～7 天；不适用为 0 | `0` | 否 |
| `daily_log_json` | String | 单日记录 | `{}` | 否 |
| `review_json` | String | 第七天复盘 | `{}` | 否 |
| `trial_status` | String | `pending/active/completed/stopped` | `pending` | 是 |
| `record_version` | Integer | 试错记录版本 | `1` | 是 |

业务键：`user_key + trial_id + record_version`。

## DB-10 `action_logs`：行动、习惯和证据日志

表简介：`统一保存任务进展、成果证据、习惯、运动、支出和安全记录。`

| 字段名 | 类型 | 描述 | 默认值 | 必填 |
|---|---|---|---|---|
| `user_key` | String | 会话级业务用户键 | 空 | 是 |
| `log_id` | String | 行动日志标识 | 空 | 是 |
| `task_id` | String | 关联任务；独立生活记录可空 | 空 | 否 |
| `log_type` | String | `progress/evidence/habit/fitness/expense/safety` | 空 | 是 |
| `content_json` | String | 本次事实 JSON | `{}` | 是 |
| `evidence_text` | String | 成果位置、反馈或证据 | 空 | 否 |
| `day_number` | Integer | 周期内第几天；不适用为 0 | `0` | 否 |
| `completed` | String | 本次动作 `true/false` | `false` | 是 |
| `safety_flag` | String | `none/stop_and_seek_help` | `none` | 是 |
| `record_version` | Integer | 行动日志版本 | `1` | 是 |

业务键：`user_key + log_id + record_version`。旧独立微习惯能力并入 WF-06，不能再创建 `habit_logs`。

## DB-11 `session_recaps`：会话收束

表简介：`保存 WF-07 生成的用户复盘和 Agent 续接摘要。`

| 字段名 | 类型 | 描述 | 默认值 | 必填 |
|---|---|---|---|---|
| `user_key` | String | 会话级业务用户键 | 空 | 是 |
| `recap_id` | String | 会话收束业务标识 | 空 | 是 |
| `user_recap_json` | String | 用户可读复盘 | `{}` | 是 |
| `agent_recap_json` | String | 后续续接摘要 | `{}` | 是 |
| `new_facts_json` | String | 新增且允许保存的事实 | `[]` | 否 |
| `state_changes_json` | String | 已证明成功的状态变化 | `[]` | 否 |
| `open_questions_json` | String | 未决问题 | `[]` | 否 |
| `next_action` | String | 下次建议自然语言入口 | 空 | 是 |
| `record_version` | Integer | 收束版本 | `1` | 是 |

业务键：`user_key + recap_id + record_version`。

## 3. 通用数据门禁

1. 所有读取和更新范围必须引用上游 `user_key`。
2. SQL 成功空数组不是失败。
3. 写入节点先检查 `isSuccess`，关键写入再回读。
4. 版本号由代码根据当前最新记录计算，不由模型生成。
5. `create_time` 由平台生成，不在新增字段列表填写。
6. pending、正式状态、娱乐模拟和事实证据分别存储，不能互相覆盖。
7. 用户自述、Agent 推断和行为证据在 JSON 内分开。
8. 不把 user_key、SQL、平台 uid 或内部错误堆栈展示给用户。
