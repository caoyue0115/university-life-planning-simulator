# WF-01～WF-12 数据库节点映射

本表是各工作流数据库配置的总索引。具体点击和 SQL 放在各 WF 文件的“数据库与输入输出配置教程”章节。

## 公共输入输出

| 名称 | 来源/含义 |
|---|---|
| `uid` | 平台系统用户标识；调试时临时使用 `test_user_001` |
| `AGENT_USER_INPUT` | 开始节点的用户原话 |
| `isSuccess` | SQL 或表单操作是否执行成功 |
| `message` | 失败原因或平台执行说明 |
| `outputList` | 查询返回的记录数组；空数组表示没有记录 |

## 节点映射

| WF | 数据库节点 | 表 | 操作 | 必要输入 | 主要输出/用途 |
|---|---|---|---|---|---|
| WF-01 / N01 | 读取正式画像及待确认草稿 | `user_profiles` | 自定义 SQL 查询 | `N00.uid` | `isSuccess,message,outputList` |
| WF-01 / N11 | 更新待确认画像 | `user_profiles` | 表单处理数据：更新 | `N00.uid,N05.profile_json,N09.confirmation_token` | `isSuccess,message,outputList` |
| WF-01 / N13 | 新建待确认画像 | `user_profiles` | 表单处理数据：新增 | `N00.uid,N05.profile_json,N09.confirmation_token` | `isSuccess,message,outputList` |
| WF-01 / N19 | 确认并写入正式画像 | `user_profiles` | 表单处理数据：更新 | `N00.uid,N03.pending_profile_json,N17.next_record_version` | `isSuccess,message,outputList` |
| WF-01 / N21 | 回读正式画像 | `user_profiles` | 自定义 SQL 查询 | `N00.uid` | `isSuccess,message,outputList`，交给 N23 核验 |
| WF-02 | 读取模拟状态 | `simulation_states` | 查询 | `uid,workflow_id=WF-02` | `state_json,pending_item_json` |
| WF-02 | 保存待回答事件 | `simulation_states` | 插入或更新 | `uid,state_id,pending_item_json` | 下一轮续接 |
| WF-02 | 更新模拟状态 | `simulation_states` | 更新 | `uid,state_id,state_json` | 保存结算结果 |
| WF-03 | 读取测试状态 | `simulation_states` | 查询 | `uid,workflow_id=WF-03` | 当前题目、序号和答案 |
| WF-03 | 保存题目/答案状态 | `simulation_states` | 插入或更新 | `uid,state_id,state_json` | 下一轮续接 |
| WF-03 | 保存测试结果 | `route_assessments` | 插入 | `uid,assessment_id,adventure_result_json` | 供 WF-04 使用 |
| WF-04 | 读取画像 | `user_profiles` | 查询 | `uid` | `profile_json` |
| WF-04 | 读取测试结果 | `route_assessments` | 查询 | `uid,assessment_id` | `adventure_result_json` |
| WF-04 | 保存路径推荐 | `route_assessments` | 更新或插入 | `uid,assessment_id,route_recommendation_json` | 推荐历史 |
| WF-05 | 读取画像与推荐 | `user_profiles`、`route_assessments` | 查询 | `uid` | 平行版本共同基线 |
| WF-05 | 保存平行版本 | `parallel_versions` | 插入 | `uid,comparison_id,versions_json` | 供 WF-06 使用 |
| WF-06 | 读取比较和当前主规划 | `parallel_versions`、`main_plans` | 查询 | `uid,comparison_id` | 新旧规划对比 |
| WF-06 | 保存待确认规划 | `main_plans` | 插入 | `uid,plan_id,pending_plan_json,confirmation_token` | 跨轮确认 |
| WF-06 | 写历史规划 | `main_plans` | 更新 | `uid,旧 plan_id` | `plan_status=history` |
| WF-06 | 写当前主规划 | `main_plans` | 插入或更新 | `uid,plan_id,plan_json` | `plan_status=active` |
| WF-06 | 回读主规划 | `main_plans` | 查询 | `uid,plan_id,record_version` | 验证正式写入 |
| WF-07 | 读取主规划和任务 | `main_plans`、`semester_tasks` | 查询 | `uid,plan_id` | 当前任务列表 |
| WF-07 | 保存待确认任务变更 | `semester_tasks` | 插入事件或临时状态 | `uid,task_id,action_log_json` | 跨轮确认 |
| WF-07 | 创建/更新任务 | `semester_tasks` | 插入或更新 | `uid,task_id` 及任务字段 | 最新任务记录 |
| WF-07 | 回读任务 | `semester_tasks` | 查询 | `uid,task_id` | 验证任务变更 |
| WF-08 | 读取主规划、任务、履历和习惯 | 多表 | 查询 | `uid` | 成长证据汇总 |
| WF-08 | 保存成长复盘 | `growth_reviews` | 插入 | `uid,review_id,review_json` | 动态修正历史 |
| WF-08 | 保存待确认变更 | `growth_reviews` | 更新 | `uid,review_id,pending_change_json` | 转交 WF-06/07 |
| WF-09 | 读取同类履历和任务证据 | `resume_entries`、`semester_tasks` | 查询 | `uid,entry_type/task_id` | 防重复、补事实 |
| WF-09 | 保存待确认履历 | `resume_entries` | 插入 | `uid,entry_id,pending_entry_json,confirmation_token` | 跨轮确认 |
| WF-09 | 写正式履历 | `resume_entries` | 更新 | `uid,entry_id,resume_entry_json` | 正式素材 |
| WF-09 | 回读履历 | `resume_entries` | 查询 | `uid,entry_id` | 验证写入 |
| WF-10 | 读取试错状态 | `decision_trials` | 查询 | `uid,trial_id` | 计划、日志和复盘 |
| WF-10 | 保存待确认计划/复盘 | `decision_trials` | 插入 | `uid,trial_id,pending_json,confirmation_token` | 跨轮确认 |
| WF-10 | 写正式计划/每日记录/复盘 | `decision_trials` | 插入或更新 | `uid,trial_id,record_type` | 完整七天记录 |
| WF-11 | 读取近期生活记录 | `habit_logs` | 查询 | `uid,log_type` | 连续记录和周汇总 |
| WF-11 | 保存待确认记账 | `habit_logs` | 插入临时记录 | `uid,log_id,log_json` | 金额确认 |
| WF-11 | 写习惯/记账/健身记录 | `habit_logs` | 插入或更新 | `uid,log_id` | 生活记录 |
| WF-12 | 读取最近复盘 | `session_recaps` | 查询 | `uid` | 避免重复、生成下次入口 |
| WF-12 | 写会话复盘 | `session_recaps` | 插入 | `uid,session_id` 及复盘字段 | 下次会话续接 |

## 三种数据库结果必须这样处理

| `isSuccess` | `outputList` | 含义 | 应做什么 |
|---|---|---|---|
| `false` | 任意 | SQL/表单操作失败 | 读取 `message`，进入失败分支，不声称已保存 |
| `true` | `[]` | 操作成功但没有记录 | 按新用户或无历史状态继续 |
| `true` | 有记录 | 正常读到数据 | 使用第一条或按教程汇总多条 |
