# WF-08 成长复盘：数据库架构规划记录

> 分支：`wf03-wf12-architecture-planning`
>
> 工作方式：一次只讨论并确认一个节点。当前阶段冻结可实现的表结构、输入输出、代码、分支和连线，但暂不要求在讯飞星辰平台创建数据表或完成变量绑定。
>
> 资料基线：以用户本次提供的 WF-08 系统提示词和大模型节点截图为唯一业务底稿；数据库化只迁移状态读写方式，不擅自删改原业务规则。

## 阅读与执行方式

本文供后续负责讯飞星辰平台配置的同学直接执行。每个节点确认后，必须记录：节点名称、前后连线、节点设置、数据范围或输入、字段或输出、业务作用、禁止事项与易错点、完成检查。

文档状态必须区分：

- **已确认设计**：已经与用户讨论通过，可以按文档实施。
- **草案待确认**：仅供讨论，不能直接建表或绑定变量。
- **平台已验证**：已经在讯飞星辰实际运行并通过测试。

除非明确标记“平台已验证”，不得把规划描述成已经在画布完成。

## 一、已确认的业务基线

WF-08 根据 WF-06 已确认主规划、WF-07 已确认任务和用户本轮陈述完成成长复盘，给出三种推荐之一：

- `continue`：证据支持继续当前方向；
- `adjust`：方向可保留，但行动或节奏需要调整；
- `consider_switch`：出现重要冲突，需要进一步比较，但不能直接替用户切换。

WF-08 只保存复盘结果，不直接修改 WF-06 主规划或 WF-07 任务。确认一份 adjust 或 consider_switch 复盘，也不等于执行了调整或切换。

## 二、上游信息与证据边界

| 优先级 | 数据来源 | 处理方式 |
|---:|---|---|
| 1 | WF-06 `plan_confirmed` | 对照原规划判断变化及影响 |
| 2 | WF-07 `task_confirmed` | 提取任务状态、实际证据和延期原因 |
| 3 | 用户本轮原话 | 补充数据库中没有记录的新事实 |

固定规则：

1. 没有任务记录，但用户提供具体事实时仍可复盘。
2. 任务记录缺失且用户输入空泛时进入 collecting，每轮最多询问三个事实：做了什么、结果如何、哪里卡住。
3. 没有主规划或任务都不能强制退回 WF-06/WF-07，也不能编造数据。
4. 不得修改任何上游 confirmed 数据。

## 三、事实、证据和推断必须分开

| 字段 | 允许保存的内容 |
|---|---|
| `explicit_new_facts` | 用户本轮明确陈述的事实 |
| `behavior_evidence` | 已确认任务中的行为和实际证据 |
| `agent_inferences` | 模型根据事实和证据作出的推断 |
| `changes_since_plan` | 与已确认主规划相比发生的变化 |

“我觉得”“可能”“也许”等内容不能直接作为已验证事实；没有证据的判断必须放入推断或待验证问题。

## 四、draft 与 confirmed 结构基线

```json
{
  "explicit_new_facts":[],
  "behavior_evidence":[],
  "agent_inferences":[],
  "changes_since_plan":[],
  "impact_on_plan":[],
  "推荐":"continue|adjust|consider_switch",
  "recommended_adjustments":[],
  "opportunity_costs":[],
  "questions_to_verify":[],
  "摘要":""
}
```

固定解释：

1. 原结构曾写“继续|调整|consider_switch”，而生成规则要求 `continue|adjust|consider_switch`；数据库版统一使用三个英文枚举值。
2. 字段名继续保留中文键 `推荐`，不擅自改名。
3. 原文中的“历史 confirm 数据”解释为历史 `confirmed` 数据。
4. `adjust` 只形成建议，不直接修改 WF-07。
5. `consider_switch` 只形成进一步比较建议，不直接修改 WF-06。
6. 普通数组最多 5 项，warnings 最多 3 项且去重。

## 五、已确认的状态机

模块状态统一使用：

- `not_started`
- `collecting`
- `awaiting_confirmation`
- `complete`
- `cancelled`
- 明确澄清时允许 `current_status="clarification_needed"`

确认成功时：

```text
review_draft → review_confirmed
review_draft = {}
review_status = complete
completed_workflow_add = WF-08
next_workflow = WF-12
```

modify 必须按用户纠正的事实重新分析，不得篡改用户未纠正的事实。cancel 清空 draft、保留 confirmed，不修改主规划或任务。

## 六、当前大模型节点基线

| 配置项 | 当前值 |
|---|---|
| 当前输入 | `user_input`、`router_context` |
| 当前输出格式 | text |
| 当前唯一输出 | `output`，String |
| 当前模型 | Kimi-K2.5 |
| 对话历史 | 关闭 |

数据库化后预计增加：

- `plan_state_rows`
- `task_state_rows`
- `review_state_rows`

输出仍保持单一 `output:String`。正式迁移时以用户提供的原提示词为底稿做最小修改，保留事实、证据、推断分离、三种推荐、机会成本、待验证问题、确认、修改和取消规则，只把完整 prior state 改为数据库输入与增量输出。

## 七、WF-08 模块表字段基线

建议表名：`wf08_growth_review_records`

| 字段 | 类型 | 默认值 | 用途 |
|---|---|---|---|
| `review_status` | String | `not_started` | WF-08 当前模块状态 |
| `review_draft` | String | `{}` | 收集或待确认的复盘对象 |
| `review_confirmed` | String | `{}` | 用户已确认的复盘对象 |
| `review_version` | Integer | `1` | 模块记录版本 |
| `last_user_intent` | String | `未记录` | 用户本轮原话 |
| `warnings` | String | `[]` | 本模块警告数组的 JSON 字符串 |

六个字段是后续读取、初始化、统一重新读取、大模型输入、C01 输出和模块写回的固定合同。所有复盘事实、证据、推断、影响、建议、机会成本和待验证问题都保存在 draft 或 confirmed JSON 中，不另加数据库列。

回复不写数据库，继续通过共享 `last_reply`、现有 N90 和唯一结束节点返回。

当前状态：业务基线、证据边界、状态机、结构解释和六字段模块表已经讨论确认并归档；讯飞星辰平台尚未实际建表。

## 八、预期主链路骨架

```text
M03 MAIN 总分支器的 WF-08 出口
→ 读取 WF-06 已确认主规划
→ 读取 WF-07 已确认任务
→ 读取 WF-08 复盘状态
→ 判断记录是否存在
→ 必要时初始化
→ 统一重新读取 WF-08 当前状态
→ WF-08 大模型
→ C01 解析模型输出
→ 解析是否成功
→ 更新 WF-08 模块表
→ C02 合并公共路由状态
→ 更新公共路由表
→ 写入共享 last_reply
→ 现有 N90
→ 唯一结束节点
```

本节只冻结总体方向，不代表所有节点配置已经确认。后续仍按“一次一个节点、用户确认后立即归档推送”的方式推进。

## 九、逐节点确认记录

尚未归档具体节点。第 1 个节点将在用户确认配置后写入本节。

## 十、下一步

下一次只讨论第 1 个节点：`WF08_DB01_读取主规划状态`。该节点确认前不提前归档具体配置。
