# 工作流共享协议

本文是 WF-01～WF-12 的统一契约。页面操作以[平台 UI 配置契约](PLATFORM-UI-CONTRACT.md)为准：读取选“自定义 SQL”，新增/更新选“表单处理数据”，条件判断选“分支器”，代码节点只填 Python。

数据库用户隔离统一使用平台自动生成的 `uid`。外部调用若使用其他用户标识名称，必须在进入工作流时先映射成 `uid`；数据库模板不得再创建重复的用户标识字段。每张表的 `id`、`uid`、`create_time` 都由平台自动创建。

## 1. 开始输入

所有变量使用英文 `snake_case`。

| 变量 | 必需 | 来源 | 说明 |
|---|---:|---|---|
| `AGENT_USER_INPUT` | 是 | 开始节点的平台内置输入 | 用户本轮原话，不改名 |
| `uid` | 是 | 主 Agent/平台用户标识 | 数据隔离键；缺失时禁止读写正式数据 |
| `session_id` | 建议 | 主 Agent/会话标识 | 中断续接和排错 |
| `intent` | 否 | 主 Agent | 未提供时由工作流识别 |
| `context_json` | 否 | 上游工作流或共享状态 | JSON 字符串；不得把别的用户数据传入 |

开始节点不能新增输入时，把 `uid`、`session_id`、`intent`、`context_json` 由主 Agent 放入调用参数；若平台也不支持调用参数，则本轮只运行无写入的演示版，并返回 `missing_user_id`。

## 2. 统一结束输出

结束节点输出一个 `result_json`，结构如下：

```json
{
  "workflow_id": "WF-01",
  "version": "1.0",
  "status": "draft",
  "reply": "给用户看的简短回复",
  "data": {},
  "suggested_writes": [],
  "next_action": "confirm_profile",
  "error": null
}
```

| 字段 | 规则 |
|---|---|
| `status` | 只能使用下节定义的状态 |
| `reply` | 手机端可读，先结论后下一步；不能与真实写入结果矛盾 |
| `data` | 当前工作流的核心产物，如 `profile_json` |
| `suggested_writes` | 待确认写入项；纯模拟和临时建议不得直接写入 |
| `next_action` | 主 Agent 下一步路由，完成时可为 `none` |
| `error` | 无错误为 `null`；有错包含 `code`、`message`、`retryable` |

## 3. 状态机与确认规则

| 状态 | 精确定义 |
|---|---|
| `read_succeeded` | 已按当前 `uid` 读取所需状态；不代表生成或写入完成 |
| `read_failed` | 读取报错或无法证明用户隔离；停止正式数据处理 |
| `draft` | 已生成草稿，未请求确认、未写入 |
| `awaiting_confirmation` | 已展示将写内容，等待用户明确确认或修改 |
| `confirmed` | 本轮收到明确确认，但尚未证明写入成功 |
| `validation_failed` | 结构或业务校验失败；不得进入写入 |
| `validation_succeeded` | 结构与业务规则均通过；不代表已保存 |
| `needs_input` | 缺少继续执行所需的用户字段或选择；`next_action` 必须说明要补什么 |
| `error` | 非读写类、无法由当前流程恢复的执行错误；必须提供 `error.code` 和安全说明 |
| `write_succeeded` | 数据库/长期记忆写入节点成功，且后续检查确认成功 |
| `write_failed` | 写入报错、无成功标志、或回读不一致 |
| `awaiting_user_input` | 已保存可续接草稿、事件或问题，等待下一轮输入 |
| `completed` | 核心产物已生成并校验通过；要求持久化时还须证明写入成功 |

“好的”“继续”等模糊表达不得当作关键确认。确认内容至少含目标对象和动作，例如“确认保存这份画像”。保存用户画像、主规划、重要履历，覆盖/切换计划和删除记录都必须先确认。修改后产生新草稿，状态重新变为 `awaiting_confirmation`。

写入节点后必须接“分支器”检查数据库固定输出 `isSuccess`；成功分支需要严格等于 `true`。若还要核对业务字段，使用第二个“数据库”按 `uid + record_key` 回读并比较 `record_version`。无法回读时只能返回 `confirmed` 或 `write_failed`，不能说“保存成功”。

纯模拟可以写入 `simulation_state`、`adventure_state` 等续接状态并返回 `awaiting_user_input`；这不是关键规划确认。续接状态必须与 `main_plan`、`user_profile` 分键，模拟过程和结果均不得覆盖正式画像或主规划。

## 4. 错误结构与通用分支

```json
{"code":"missing_user_id","message":"缺少用户标识，本轮未保存。","retryable":true}
```

推荐错误码：`missing_input`、`missing_user_id`、`invalid_json`、`missing_required_field`、`knowledge_unavailable`、`write_failed`、`read_failed`、`unsafe_request`。错误分支仍需进入“结束”，保留可读 `reply` 和可执行 `next_action`。

大模型输出必须先经“变量提取器”提取，再经 Python“代码”节点补空值、校验枚举，最后进入“分支器/数据库”。解析失败允许大模型重试一次；仍失败返回 `invalid_json`，不得写入。

## 5. 共享存储键

逻辑实体建议使用：`user_profile`、`simulation_state`、`adventure_result`、`route_recommendation`、`parallel_versions`、`main_plan`、`semester_tasks`、`action_records`、`resume_entries`、`growth_reviews`、`decision_trials`、`habit_logs`、`session_recaps`。

每条正式记录至少包含：`uid`、`record_key`、`record_version`、`created_at`、`updated_at`、`source_workflow`、`data_json`。平台数据表自动字段为 `id`、`uid`、`create_time`；业务需要的 `created_at/updated_at` 由开始节点或主 Agent 传入。取不到时间就留空并在 `error` 中提示，不伪造时间。

数据库读取：模式选“自定义 SQL”，输入区声明 SQL 中的 `{{变量名}}`，固定输出为 `isSuccess/message/outputList`。数据库新增/更新：模式选“表单处理数据”，选择 `university / 表名`，再按“设置新增数据”或“设置数据范围 + 设置更新数据”逐字段引用。若目标操作无法配置，降级为“长期记忆检索/长期记忆写入”，记忆键使用 `uid:record_key`；若用户隔离能力无法确认，只可跑无写入版。

画像字段中的 `self_reported`（自评）、`agent_inferred`（Agent 推断）、`behavior_verified`（行为已验证）必须分开；推断不得冒充事实。政策类知识需带来源、更新时间和“请以学校/主管部门官方渠道为准”。

## 6. 通用调试门禁

1. 用两个不同 `uid` 测试，确认互不可读。
2. 让大模型返回缺字段或非 JSON，确认不会进入写入。
3. 模拟用户未确认，确认 `suggested_writes` 可返回但数据库不变化。
4. 模拟写入失败，确认状态为 `write_failed` 且回复不含“已保存”。
5. 检查娱乐模拟、临时建议与正式画像/主规划使用不同 `record_key`。
