# WF-11 微习惯与生活记录：数据库架构规划记录

> 分支：`wf03-wf12-architecture-planning`
>
> 业务底稿：用户提供的 WF-11 原系统提示词和模型截图。数据库化只迁移状态读写；将损坏或含混的键名统一为可实现结构。
>
> 状态说明：本文件是已确认设计与交接配置，不代表已在星辰平台实际搭建运行。

## 一、业务与依赖基线

WF-11 处理微习惯计划、完成记录、历史回顾、修改、取消和确认。它只读取本模块历史，不读取画像、规划或任务表：当前事实来自 `user_input`，历史模式来自 `habit_confirmed.records`，健康安全判断来自用户本轮陈述。其他业务模块不是生成或校验微习惯记录所需证据，因而不设置上游门槛。

公共路由记录仍在成功路径末尾由 C02 读取并合并；这与“无需读取其他业务模块”不冲突。不得编造完成、金额、类别、连续天数或通知能力。

## 二、规范业务结构

```json
{
  "行动":"plan|record|review",
  "habit_type":"走路|冥想|阅读|记账|健身|素材整理|其他",
  "记录":{
    "描述":"","duration_or_amount":"","类别":"",
    "completed":false,"user_note":""
  },
  "minimum_next_action":"",
  "recent_pattern":"",
  "supportive_feedback":"",
  "摘要":""
}
```

原“审查”统一为 `review`，原“唱片”统一为“记录”，原“完成/complete”统一为 Boolean `completed`；“开销”统一为“记账”，“组织”统一为“素材整理”。confirmed 使用 `{"records":[],"摘要":""}`，最多保留 5 条，达到上限时必须询问替换对象。

健康风险出现时停止常规训练或饮食建议，加入安全警告并建议停止相关活动、寻求合格专业人员帮助；不得生成可能加重风险的计划。

## 三、状态机与模块表

状态：`not_started`、`collecting`、`awaiting_confirmation`、`complete`、`cancelled`。确认成功时 draft 追加到 confirmed.records、draft 清空、完成标记追加 WF-11、next_workflow=WF-12。

数据表：`wf11_habit_log_records`

| 字段 | 类型 | 默认值 |
|---|---|---|
| `habit_status` | String | `not_started` |
| `habit_draft` | String | `{}` |
| `habit_confirmed` | String | `{}` |
| `habit_version` | Integer | `1` |
| `last_user_intent` | String | `未记录` |
| `warnings` | String | `[]` |

业务结构全部保存在 draft/confirmed JSON，不增加其他列。reply 走共享 `last_reply`。

## 四、完整链路

```text
M03.WF-11
→ WF11_DB01_读取微习惯状态
→ WF11_微习惯状态是否存在
   ├─ 如果 → WF11_DB03_读取当前微习惯状态
   └─ 否则 → WF11_DB02_初始化微习惯状态 → WF11_DB03_读取当前微习惯状态
→ WF11_LLM_微习惯与生活记录
→ WF11_C01_解析模型输出
→ WF11_解析是否成功
   ├─ 如果 → WF11_DB04_更新微习惯状态 → WF11_C02_合并路由状态 → WF11_DB05_更新路由状态
   └─ 否则 ─────────────────────────────────────────────────────────┐
→ WF11_写入_last_reply → 现有 N90 → 唯一结束节点                 │
```

## 五、逐节点完整配置

### 1. `WF11_DB01_读取微习惯状态`

MAIN WF-11 出口接入。数据库 `university_planner`，表 `wf11_habit_log_records`，查询数据，上限 1，范围 `habit_version > 0`；读取 `habit_status`、`habit_draft`、`habit_confirmed`、`habit_version`、`last_user_intent`、`warnings` 六字段。只作存在性探测，后接分支器。

### 2. `WF11_微习惯状态是否存在`

分支器引用 DB01 整个 `outputList`，判断数组长度大于数字 0。如果直接到 DB03；否则到 DB02，随后到 DB03。不能判断 status，也不能把比较值写成字符串“0”。

### 3. `WF11_DB02_初始化微习惯状态`

数据库 `university_planner`，表 `wf11_habit_log_records`，新增数据：`habit_status=not_started`、`habit_draft={}`、`habit_confirmed={}`、`habit_version=1`（Integer）、`last_user_intent=未记录`、`warnings=[]`。只接否则出口，不填系统字段，后接 DB03。

### 4. `WF11_DB03_读取当前微习惯状态`

复制 DB01 并改名，配置完全一致。分支器如果出口与 DB02 初始化出口均汇入本节点。大模型只引用 DB03，不引用 DB01。

### 5. `WF11_LLM_微习惯与生活记录`

Kimi-K2.5，关闭对话历史，输出格式 text，唯一输出 `output:String`。

| 输入 | 引用来源 |
|---|---|
| `user_input` | `开始.AGENT_USER_INPUT` |
| `router_context` | `N01 路由大模型.output` |
| `habit_state_rows` | DB03.outputList |

完整提示词：[WF-11 数据库版大模型提示词](prompts/WF-11-database-llm-prompts.md)。必须整体复制，不再传完整 prior_state。

### 6. `WF11_C01_解析模型输出`

输入 `model_output:String=LLM.output`、`user_input:String=开始.AGENT_USER_INPUT`。

输出：`parse_ok:Boolean`、`error_message:String`、`reply:String`、`current_workflow:String`、`current_status:String`、`last_user_intent:String`、`habit_status:String`、`habit_draft_json:String`、`habit_confirmed_json:String`、`next_workflow:String`、`completed_workflow_add:String`、`warnings_json:String`。

完整代码：[WF-11 C01](code/WF-11-C01-parse-model-output.py)。代码校验十字段、规范键名、行动与完成布尔值、运动时长/记账金额、confirmed 容量、状态和路由；失败返回安全 reply 且不写库。

测试覆盖 collecting、plan、record、review、正式确认，以及旧键名、错误完成值、缺少时长/金额、超容量和错误路由等异常。

### 7. `WF11_解析是否成功`

分支器引用 C01.parse_ok，等于 Boolean `true`。如果接 DB04；否则直接接共享回复节点。失败路径不得经过任何数据库。

### 8. `WF11_DB04_更新微习惯状态`

更新 `wf11_habit_log_records`，范围 `habit_version > 0`：

| 字段 | 引用 |
|---|---|
| `habit_status` | C01.habit_status |
| `habit_draft` | C01.habit_draft_json |
| `habit_confirmed` | C01.habit_confirmed_json |
| `last_user_intent` | C01.last_user_intent |
| `warnings` | C01.warnings_json |

不更新 habit_version、公共路由或 reply。后接 C02。

### 9. `WF11_C02_合并路由状态`

输入 `route_state_rows=MAIN DB03.outputList`、`completed_workflow_add=C01.completed_workflow_add`。输出 `merge_ok:Boolean`、`error_message:String`、`completed_workflows_json:String`、`state_version_next:Integer`。

完整代码：[WF-11 C02](code/WF-11-C02-merge-route-state.py)。保留并去重历史完成列表，只允许追加 WF-11，版本加一，异常直接中断；不增加成功保护分支器。

### 10. `WF11_DB05_更新路由状态`

更新 `agent_runtime_states`，范围 `schema_version = mvp-1.1`：

| 字段 | 引用 |
|---|---|
| `current_workflow` | C01.current_workflow |
| `current_status` | C01.current_status |
| `next_workflow` | C01.next_workflow |
| `completed_workflows` | C02.completed_workflows_json |
| `state_version` | C02.state_version_next |

不更新 schema_version、profile_status、业务字段或 reply。后接共享回复节点。

### 11. `WF11_写入_last_reply`

变量存储器只写：`last_reply = WF11_C01_解析模型输出.reply`。成功入口来自 DB05；失败入口来自解析分支器否则。随后接现有 N90 和唯一结束节点，不修改公共节点。

## 六、实施检查清单

- [ ] 只读取自身业务状态；不把公共路由合并误认为业务上游依赖。
- [ ] 自身存在性探测与统一重读分离。
- [ ] 六字段表名称和类型完全一致，不新增临时列。
- [ ] 大模型三输入、单一 String 输出、对话历史关闭。
- [ ] 计划、记录、回顾和健康安全边界完整保留。
- [ ] C01/C02 使用独立文件并通过正常、异常测试。
- [ ] C01 失败路径不写任何数据库。
- [ ] 模块表只更新五个业务字段；公共表只更新五个路由字段。
- [ ] 成功和失败均写共享 last_reply，再进入现有 N90。
- [ ] 没有第二个结束节点，不声称提醒或真实连续天数持久化。
