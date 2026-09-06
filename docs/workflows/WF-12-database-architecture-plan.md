# WF-12 会话复盘：数据库架构规划记录

> 分支：`wf03-wf12-architecture-planning`
>
> 业务底稿：用户提供的 WF-12 原系统提示词和模型截图。数据库化只迁移状态读写，并修正与当前持久化架构冲突的旧调试文案。
>
> 状态说明：本文件是已确认设计与交接配置，不代表已在星辰平台实际搭建运行。

## 一、业务与依赖基线

WF-12 必须同时读取公共路由状态、十个上游业务模块和自身历史。公共路由提供唯一可信的 `completed_workflows`；上游 status/draft/confirmed 用于区分已确认决定、待确认草稿和未完成模块。当前产品不创建 WF-05，因此有效模块是 WF-01～04、WF-06～12，共 11 个。

数据库化后的复盘会写入当前系统记录。不得沿用“只在调试对话中、关闭后必然丢失”的旧说法，也不得承诺永久保存或跨账号、跨环境共享。

## 二、规范业务结构

```json
{
  "completed_modules":[],
  "confirmed_decisions":[],
  "new_explicit_facts":[],
  "pending_drafts":[{"workflow":"WF-06","module_name":"主规划"}],
  "unresolved_questions":[],
  "next_three_actions":[],
  "recommended_return_point":"WF-06",
  "user_summary":"",
  "agent_notes":{
    "preference_changes":[],"route_changes":[],
    "task_changes":[],"inferences_to_verify":[]
  }
}
```

`completed_modules` 最多 11 项、`pending_drafts` 最多 10 项，二者是普通数组最多 5 项的明确例外；`next_three_actions` 最多 3 项，其余普通数组最多 5 项。pending_drafts 每项只含 workflow 和 module_name。

## 三、状态机与模块表

状态：`not_started`、`collecting`、`awaiting_confirmation`、`complete`、`cancelled`。生成复盘进入 awaiting_confirmation；确认后复制 draft 到 confirmed、清空 draft、追加 WF-12，next_workflow 等于 confirmed.recommended_return_point。

数据表：`wf12_final_review_records`

| 字段 | 类型 | 默认值 |
|---|---|---|
| `final_review_status` | String | `not_started` |
| `final_review_draft` | String | `{}` |
| `final_review_confirmed` | String | `{}` |
| `final_review_version` | Integer | `1` |
| `last_user_intent` | String | `未记录` |
| `warnings` | String | `[]` |

## 四、完整链路

```text
M03.WF-12
→ DB01画像 → DB02虚拟大学 → DB03生存大冒险 → DB04路径推荐
→ DB05主规划 → DB06学期任务 → DB07成长复盘 → DB08履历素材
→ DB09决策试错 → DB10微习惯 → DB11会话复盘状态
→ WF12_会话复盘状态是否存在
   ├─ 如果 → DB13读取当前会话复盘状态
   └─ 否则 → DB12初始化会话复盘状态 → DB13读取当前会话复盘状态
→ LLM → C01 → 解析是否成功
   ├─ 如果 → DB14更新会话复盘 → C02合并路由 → DB15更新路由
   └─ 否则 ─────────────────────────────────────────────────────┐
→ 写入 last_reply → 现有 N90 → 唯一结束节点                  │
```

## 五、逐节点完整配置

### 1～10. 上游状态查询

全部使用数据库 `university_planner`、查询上限 1、对应 version 大于数字 0；读取 status、draft、confirmed、version。draft 必须读取，因为 WF-12 要识别真正 awaiting_confirmation 的草稿；不得仅凭 version 判断完成。

| 节点 | 表 | 字段前缀 | 后接 |
|---|---|---|---|
| `WF12_DB01_读取画像状态` | `wf01_profile_records` | `profile_` | DB02 |
| `WF12_DB02_读取虚拟大学状态` | `wf02_virtual_university_records` | `simulation_` | DB03 |
| `WF12_DB03_读取生存大冒险状态` | `wf03_survival_adventure_records` | `adventure_` | DB04 |
| `WF12_DB04_读取路径推荐状态` | `wf04_path_recommendation_records` | `recommendation_` | DB05 |
| `WF12_DB05_读取主规划状态` | `wf06_main_plan_records` | `plan_` | DB06 |
| `WF12_DB06_读取学期任务状态` | `wf07_semester_task_records` | `task_` | DB07 |
| `WF12_DB07_读取成长复盘状态` | `wf08_growth_review_records` | `review_` | DB08 |
| `WF12_DB08_读取履历素材状态` | `wf09_resume_asset_records` | `asset_` | DB09 |
| `WF12_DB09_读取决策试错状态` | `wf10_decision_trial_records` | `trial_` | DB10 |
| `WF12_DB10_读取微习惯状态` | `wf11_habit_log_records` | `habit_` | DB11 |

缺失任一记录按未完成处理，不能阻断复盘。所有查询只读，不修改上游数据。

### 11. `WF12_DB11_读取会话复盘状态`

查询 `wf12_final_review_records`，上限 1，范围 `final_review_version > 0`，读取六字段。只作存在性探测，后接分支器。

### 12. `WF12_会话复盘状态是否存在`

引用 DB11 整个 outputList，判断数组长度大于数字 0。如果接 DB13；否则接 DB12 后再到 DB13。不得判断 status 或使用字符串“0”。

### 13. `WF12_DB12_初始化会话复盘状态`

新增 `wf12_final_review_records`：`final_review_status=not_started`、draft/confirmed 为 `{}` 字符串、`final_review_version=1` Integer、`last_user_intent=未记录`、`warnings=[]`。不填系统字段，后接 DB13。

### 14. `WF12_DB13_读取当前会话复盘状态`

复制 DB11 并改名。分支器如果出口与 DB12 均汇入本节点；LLM 只引用 DB13。

### 15. `WF12_LLM_会话复盘`

Kimi-K2.5，关闭对话历史，输出 text，唯一输出 `output:String`。输入如下：

- `user_input=开始.AGENT_USER_INPUT`
- `router_context=N01路由大模型.output`
- `route_state_rows=MAIN DB03.outputList`
- `profile_state_rows` 至 `habit_state_rows` 分别引用 DB01～DB10
- `final_review_state_rows=DB13.outputList`

完整提示词：[WF-12 数据库版大模型提示词](prompts/WF-12-database-llm-prompts.md)。必须整体复制。

### 16. `WF12_C01_解析模型输出`

输入 model_output、user_input、route_state_rows 和 DB01～DB10 的十组状态结果。输出：`parse_ok:Boolean`、`error_message:String`、`reply:String`、`current_workflow:String`、`current_status:String`、`last_user_intent:String`、`final_review_status:String`、`final_review_draft_json:String`、`final_review_confirmed_json:String`、`next_workflow:String`、`completed_workflow_add:String`、`warnings_json:String`。

完整代码：[WF-12 C01](code/WF-12-C01-parse-model-output.py)。它交叉校验公共完成列表和真实待确认状态，检查十一模块菜单、容量、状态与返回点；失败只返回安全回复。

### 17. `WF12_解析是否成功`

判断 C01.parse_ok 等于 Boolean true。如果接 DB14；否则直接接共享回复节点，失败路径不写数据库。

### 18. `WF12_DB14_更新会话复盘状态`

更新 `wf12_final_review_records`，范围 `final_review_version > 0`：

| 字段 | 引用 |
|---|---|
| `final_review_status` | C01.final_review_status |
| `final_review_draft` | C01.final_review_draft_json |
| `final_review_confirmed` | C01.final_review_confirmed_json |
| `last_user_intent` | C01.last_user_intent |
| `warnings` | C01.warnings_json |

不更新 version、公共路由或 reply，后接 C02。

### 19. `WF12_C02_合并路由状态`

输入 `route_state_rows=MAIN DB03.outputList`、`completed_workflow_add=C01.completed_workflow_add`；输出 merge_ok、error_message、completed_workflows_json、state_version_next。完整代码：[WF-12 C02](code/WF-12-C02-merge-route-state.py)。只允许追加 WF-12，去重并递增版本，异常直接中断，不加 merge_ok 分支器。

### 20. `WF12_DB15_更新路由状态`

更新 `agent_runtime_states`，范围 `schema_version=mvp-1.1`：current_workflow、current_status、next_workflow 引用 C01；completed_workflows、state_version 引用 C02。不得更新 schema_version、profile_status、业务字段或 reply。

### 21. `WF12_写入_last_reply`

变量存储器只写 `last_reply=WF12_C01_解析模型输出.reply`。成功入口来自 DB15，失败入口来自解析分支器否则；随后接现有 N90 和唯一结束节点。

## 六、实施检查清单

- [ ] 十个上游全部只读 status/draft/confirmed/version，缺失不阻断。
- [ ] completed_modules 只来自公共 completed_workflows。
- [ ] pending_drafts 与真实 awaiting_confirmation 状态逐项一致。
- [ ] 菜单列出全部 11 个有效模块，不出现 WF-05。
- [ ] 自身存在性探测、初始化和统一重读分离。
- [ ] 六字段表不增加临时列；模型单一 String 输出且关闭历史。
- [ ] C01/C02 独立文件通过正常、异常测试。
- [ ] 解析失败不写数据库；成功和失败均进入共享回复链路。
- [ ] 确认后的 next_workflow 等于 recommended_return_point。
- [ ] 不再输出与数据库持久化事实冲突的旧调试文案。
