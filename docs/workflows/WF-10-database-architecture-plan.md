# WF-10 决策分析与七天试错：数据库架构规划记录

> 分支：`wf03-wf12-architecture-planning`
>
> 业务底稿：用户提供的 WF-10 原系统提示词和模型截图。数据库化只迁移状态读写；“福利”统一为“收益”，“审判”统一为“试错”。
>
> 状态说明：本文件是已确认设计与交接配置，不代表已在星辰平台实际搭建运行。

## 一、业务与依赖基线

WF-10 在同一大模型中完成 decision_analysis、seven_day_trial、日志追加、修改、取消和确认。三个上游均为可选增强，不是硬门槛：

| 来源 | 用途 | 禁止事项 |
|---|---|---|
| WF-01 `profile_confirmed` | 年级、专业、资源和偏好背景 | 不得编造缺失画像 |
| WF-04 `recommendation_confirmed` | 主备路径与风险参考 | 不得替用户决定 |
| WF-06 `plan_confirmed` | 当前目标、行动限制和计划背景 | 确认试错不得自动改主规划 |

任一上游为空都继续运行。涉及违法、危险、医疗或重大财务风险时停止设计试错行动并给出安全提醒。

## 二、规范业务结构

```json
{
  "模式":"decision_analysis|seven_day_trial",
  "decision_topic":"",
  "options":[],
  "分析":{
    "收益":[],"风险":[],"time_cost":[],"economic_cost":[],
    "opportunity_cost":[],"可逆性":[],"worst_case":[],"exit_conditions":[]
  },
  "试错":{
    "假设":"","investment_limit":"","daily_minimum_actions":[],
    "daily_logs":[],"day7_review":{},"recommended_decision":""
  },
  "摘要":""
}
```

daily_logs 每项固定包含 `day`、`精力`、`兴趣`、`完成度`、`困难`、`证据`。普通数组最多 5 项；daily_logs 例外允许 7 项，day 为 1～7 且唯一。日志少于七天时不得生成 day7_review 或 recommended_decision。

## 三、状态机与模块表

状态：`not_started`、`collecting`、`awaiting_confirmation`、`complete`、`cancelled`。确认成功时 draft 复制到 confirmed、draft 清空、完成标记追加 WF-10、next_workflow=WF-12。确认试错计划不等于主规划已更改。

数据表：`wf10_decision_trial_records`

| 字段 | 类型 | 默认值 |
|---|---|---|
| `trial_status` | String | `not_started` |
| `trial_draft` | String | `{}` |
| `trial_confirmed` | String | `{}` |
| `trial_version` | Integer | `1` |
| `last_user_intent` | String | `未记录` |
| `warnings` | String | `[]` |

业务结构全部保存在 draft/confirmed JSON，不增加其他列。reply 继续走共享 `last_reply`。

## 四、完整链路

```text
M03.WF-10
→ WF10_DB01_读取画像状态
→ WF10_DB02_读取路径推荐状态
→ WF10_DB03_读取主规划状态
→ WF10_DB04_读取决策试错状态
→ WF10_决策试错状态是否存在
   ├─ 如果 → WF10_DB06_读取当前决策试错状态
   └─ 否则 → WF10_DB05_初始化决策试错状态 → WF10_DB06_读取当前决策试错状态
→ WF10_LLM_决策分析与七天试错
→ WF10_C01_解析模型输出
→ WF10_解析是否成功
   ├─ 如果 → WF10_DB07_更新决策试错状态 → WF10_C02_合并路由状态 → WF10_DB08_更新路由状态
   └─ 否则 ───────────────────────────────────────────────────────────────┐
→ WF10_写入_last_reply → 现有 N90 → 唯一结束节点                      │
```

## 五、逐节点完整配置

### 1. `WF10_DB01_读取画像状态`

MAIN WF-10 出口接入。数据库 `university_planner`，表 `wf01_profile_records`，查询数据，上限 1，范围 `profile_version > 0`；只取 `profile_status`、`profile_confirmed`、`profile_version`，不取 draft。无画像继续。后接 DB02。

### 2. `WF10_DB02_读取路径推荐状态`

数据库 `university_planner`，表 `wf04_path_recommendation_records`，查询数据，上限 1，范围 `recommendation_version > 0`；只取 `recommendation_status`、`recommendation_confirmed`、`recommendation_version`，不取 draft。无推荐继续。后接 DB03。

### 3. `WF10_DB03_读取主规划状态`

数据库 `university_planner`，表 `wf06_main_plan_records`，查询数据，上限 1，范围 `plan_version > 0`；只取 `plan_status`、`plan_confirmed`、`plan_version`，不取 draft。无规划继续。后接 DB04。

### 4. `WF10_DB04_读取决策试错状态`

数据库 `university_planner`，表 `wf10_decision_trial_records`，查询数据，上限 1，范围 `trial_version > 0`；读取六字段。该节点只作存在性探测，后接分支器。

### 5. `WF10_决策试错状态是否存在`

分支器引用 DB04 整个 `outputList`，判断数组长度大于数字 0。如果直接到 DB06；否则到 DB05，随后到 DB06。不能判断 status 或把字符串“0”作为比较值。

### 6. `WF10_DB05_初始化决策试错状态`

数据库新增 `wf10_decision_trial_records`：`trial_status=not_started`、`trial_draft={}`、`trial_confirmed={}`、`trial_version=1`（Integer）、`last_user_intent=未记录`、`warnings=[]`。只接否则出口，不填系统字段，后接 DB06。

### 7. `WF10_DB06_读取当前决策试错状态`

复制 DB04 并改名，配置完全一致。分支器如果出口与 DB05 初始化出口均汇入本节点。大模型只引用 DB06，不引用 DB04。

### 8. `WF10_LLM_决策分析与七天试错`

Kimi-K2.5，关闭对话历史，输出格式 text，唯一输出 `output:String`。

| 输入 | 引用来源 |
|---|---|
| `user_input` | `开始.AGENT_USER_INPUT` |
| `router_context` | `N01 路由大模型.output` |
| `profile_state_rows` | DB01.outputList |
| `recommendation_state_rows` | DB02.outputList |
| `plan_state_rows` | DB03.outputList |
| `trial_state_rows` | DB06.outputList |

完整提示词：[WF-10 数据库版大模型提示词](prompts/WF-10-database-llm-prompts.md)。必须整体复制，不再传完整 prior_state。

### 9. `WF10_C01_解析模型输出`

输入 `model_output:String=LLM.output`、`user_input:String=开始.AGENT_USER_INPUT`。

输出：`parse_ok:Boolean`、`error_message:String`、`reply:String`、`current_workflow:String`、`current_status:String`、`last_user_intent:String`、`trial_status:String`、`trial_draft_json:String`、`trial_confirmed_json:String`、`next_workflow:String`、`completed_workflow_add:String`、`warnings_json:String`。

完整代码：[WF-10 C01](code/WF-10-C01-parse-model-output.py)。代码校验十字段、模式、八类分析、七天日志、状态和路由；失败返回安全 reply 且不写库。

测试覆盖：模式未定 collecting、完整两选项分析、完整试错计划、七日日志、正式确认、单选项、缺投入上限、提前七日复盘、错误模式及错误路由，全部符合预期。

### 10. `WF10_解析是否成功`

分支器引用 C01.parse_ok，等于 Boolean `true`。如果接 DB07；否则直接接共享回复节点。失败路径不得经过任何数据库。

### 11. `WF10_DB07_更新决策试错状态`

更新 `wf10_decision_trial_records`，范围 `trial_version > 0`：

| 字段 | 引用 |
|---|---|
| `trial_status` | C01.trial_status |
| `trial_draft` | C01.trial_draft_json |
| `trial_confirmed` | C01.trial_confirmed_json |
| `last_user_intent` | C01.last_user_intent |
| `warnings` | C01.warnings_json |

不更新 trial_version、公共路由或 reply。后接 C02。

### 12. `WF10_C02_合并路由状态`

输入 `route_state_rows=MAIN DB03.outputList`、`completed_workflow_add=C01.completed_workflow_add`。输出 `merge_ok:Boolean`、`error_message:String`、`completed_workflows_json:String`、`state_version_next:Integer`。

完整代码：[WF-10 C02](code/WF-10-C02-merge-route-state.py)。保留并去重历史完成列表，只允许追加 WF-10，版本加一，异常直接中断；不增加成功保护分支器。正常追加、重复、空追加、空记录和错误标记测试均符合预期。

### 13. `WF10_DB08_更新路由状态`

更新 `agent_runtime_states`，范围 `schema_version = mvp-1.1`：

| 字段 | 引用 |
|---|---|
| `current_workflow` | C01.current_workflow |
| `current_status` | C01.current_status |
| `next_workflow` | C01.next_workflow |
| `completed_workflows` | C02.completed_workflows_json |
| `state_version` | C02.state_version_next |

不更新 schema_version、profile_status、业务字段或 reply。后接共享回复节点。

### 14. `WF10_写入_last_reply`

变量存储器只写：`last_reply = WF10_C01_解析模型输出.reply`。成功入口来自 DB08；失败入口来自解析分支器否则。随后接现有 N90 和唯一结束节点，不修改公共节点。

## 六、实施检查清单

- [ ] 三个上游只读 confirmed 且均非硬门槛。
- [ ] 自身存在性探测与统一重读分离。
- [ ] 六字段表名称和类型完全一致。
- [ ] 大模型六输入、单一 String 输出、对话历史关闭。
- [ ] C01/C02 使用独立文件并完成节点自身输入测试。
- [ ] C01 失败路径不写任何数据库。
- [ ] 模块表只更新五个业务字段；公共表只更新五个路由字段。
- [ ] 成功和失败均写共享 last_reply，再进入现有 N90。
- [ ] 没有第二个结束节点，没有自动修改主规划。
