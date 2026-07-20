# MAIN/WF 数据库节点映射

## 1. 公共输入输出

所有 WF-01～WF-09：

```text
开始：AGENT_USER_INPUT:String
N00A：user_key:String、user_input:String、input_valid:Boolean、input_error:String
结束：result_json:String
```

所有数据库节点输入中的 `user_key` 只能引用当前工作流 N00A 或其原样透传输出。平台自动 `uid` 不作为业务参数。

## 2. 表与工作流关系

| 表 | 读取者 | 写入者 | 关键范围/排序 |
|---|---|---|---|
| DB-01 `user_profiles` | WF-01/WF-02/WF-03/WF-04 | WF-01 | user_key；record_version/create_time |
| DB-02 `simulation_states` | WF-02/WF-03/WF-04 | WF-02/WF-03 | user_key + workflow_id；state_version/create_time |
| DB-03 `route_assessments` | WF-04/WF-05 | WF-02/WF-03/WF-04 | user_key；assessment_version/create_time |
| DB-04 `parallel_versions` | WF-05 | WF-05 | user_key + comparison_id；record_version |
| DB-05 `main_plans` | WF-05/WF-06/WF-07 | WF-05 | user_key + plan_id + plan_status；record_version |
| DB-06 `semester_tasks` | WF-06/WF-07 | WF-06 | user_key + task_id；record_version |
| DB-07 `growth_reviews` | WF-07 | WF-07 | user_key + review_id；record_version |
| DB-08 `resume_entries` | WF-08 | WF-08 | user_key + entry_id + record_status；record_version |
| DB-09 `decision_trials` | WF-09 | WF-09 | user_key + trial_id + trial_status；record_version |
| DB-10 `action_logs` | WF-06/WF-07 | WF-06 | user_key + task_id/log_id；create_time |
| DB-11 `session_recaps` | WF-07 | WF-07 | user_key + recap_id；record_version |

MAIN-00 不直接读写业务表。它只生成/恢复 `user_key` 并调用 MCP 工具；业务前置判断由对应工具自己读取。

## 3. 各工作流数据库节点

### WF-01 用户画像

1. 读 DB-01 最新记录。
2. 无记录时新增 pending。
3. 有记录时更新 pending/修改草稿。
4. 明确确认时按 user_key + id + pending_status 更新正式画像。
5. 回读 confirmed 画像、版本和内容。

### WF-02 虚拟大学

1. 读 DB-01 confirmed 画像。
2. 读 DB-02 最新 WF-02 状态。
3. 首次生成事件或结算一个 pending 事件。
4. 向 DB-02 追加新 state_version。
5. 完成时把 simulation_result_json 写/追加到 DB-03。

### WF-03 生存大冒险

1. 读 DB-01 confirmed 画像。
2. 读 DB-02 最新 WF-03 状态。
3. 首次生成题目或结算一个 pending 问题。
4. 向 DB-02 追加新 state_version。
5. 完成时把 adventure_result_json 写/追加到 DB-03。

### WF-04 五路径推荐

1. 读 DB-01 confirmed 画像。
2. 读 DB-02 两种已完成探索或读 DB-03 已汇总证据。
3. 判断只有 WF-02、只有 WF-03、两者都有或两者都无。
4. 检索 KB-01，生成推荐。
5. 新增 DB-03 评估版本并回读。

### WF-05 方向与主规划

1. 读 DB-01 confirmed 画像。
2. 读 DB-03 最新推荐。
3. 读 DB-04 最新方向比较。
4. 读 DB-05 当前 pending/active 规划。
5. 比较/生成时写 DB-04 和 DB-05 pending。
6. 明确确认时归档旧 active、激活 pending、回读新 active。

### WF-06 任务与行动

1. 读 DB-05 active 主规划。
2. 查询/定位 DB-06 任务。
3. 创建或更新任务版本。
4. 记录行动时新增 DB-10。
5. 完成任务必须先有 evidence，再更新 DB-06 并回读。

### WF-07 复盘与收束

1. 读 DB-05 active 主规划。
2. 读 DB-06 当前/近期任务。
3. 读 DB-10 近期行动和证据。
4. 写 DB-07 复盘。
5. 写 DB-11 会话收束。
6. 分别检查写入并回读；不直接改主规划。

### WF-08 履历证据

1. 读 DB-08 最新 pending 和正式条目。
2. 新真实经历写 pending。
3. 修改/取消按 user_key + entry_id。
4. 明确确认后写正式状态并回读。

### WF-09 决策试错

1. 即时分析可不写数据库。
2. 创建/确认/日志/复盘/停止时读 DB-09 当前状态。
3. 每次持久化新增一个 record_version。
4. active、completed、stopped 都按 user_key + trial_id 回读。

## 4. 固定的数据库判断模板

读取：

```text
数据库自定义 SQL
→ 分支器：isSuccess == true？
   ├─ 默认/否：read_failed
   └─ 是：代码整理 outputList
        → 分支器：has_record == true？
```

写入：

```text
数据库新增/更新
→ 分支器：isSuccess == true？
   ├─ 默认/否：write_failed
   └─ 是：自定义 SQL 回读
        → 分支器：回读 isSuccess？
             → 代码比较业务键/状态/版本/内容
             → 一致才 write_succeeded
```

## 5. 必测数据库场景

每张工作流教程至少包含：

1. SQL 成功空数组。
2. SQL 执行失败。
3. 有记录且属于当前 user_key。
4. 另一个 user_key 的记录不可见。
5. 写入 isSuccess=false。
6. 写入成功但回读失败。
7. 回读成功但内容/版本不一致。
8. 临时改错配置后恢复准确表名、字段和引用。
