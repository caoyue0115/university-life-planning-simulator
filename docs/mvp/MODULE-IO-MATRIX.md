# MVP WF-01～WF-12 输入输出总表

## 1. 只有 MAIN 有开始和结束

本 MVP 把 12 个 WF 作为同一画布中的 12 个大模型业务节点，因此不会给每个模块再放一套“开始/结束”。

统一开始：

| 变量 | 类型 | 来源 |
|---|---|---|
| `AGENT_USER_INPUT` | String | 用户本轮自然语言 |

每个业务模块统一输入：

| 变量 | 类型 | 来源 |
|---|---|---|
| `user_input` | String | 开始 / AGENT_USER_INPUT |
| `router_context` | String | 路由大模型 / output |

`router_context` 内部包含：

```json
{
  "target_workflow": "WF-01",
  "route_reason": "",
  "user_action": "start",
  "requested_jump": "",
  "prior_state": {}
}
```

每个业务模块统一输出：

| 变量 | 类型 | 内容 |
|---|---|---|
| `output` | String | 更新后的完整 `mvp-1.0 state_json` |

统一结束：

| 变量 | 类型 | 值 |
|---|---|---|
| `output` | 输入 | `workflow_finished` |

业务 JSON 由各分支自己的“消息”节点显示；固定结束值不承担业务数据传递。

## 2. 模块输入依赖和输出字段

| WF | 额外读取的 prior_state | 本轮主要更新 | 草稿完成后的状态 | 确认后的下一模块 |
|---|---|---|---|---|
| WF-01 | 无 | `profile` | awaiting_confirmation | WF-02 |
| WF-02 | `profile.confirmed` | `virtual_university` | awaiting_confirmation | WF-03 |
| WF-03 | `profile.confirmed` | `survival_adventure` | awaiting_confirmation | WF-04 |
| WF-04 | profile；最好有 WF-03 | `path_recommendation` | awaiting_confirmation | WF-05 |
| WF-05 | profile；最好有 WF-04 | `parallel_lives` | awaiting_confirmation | WF-06 |
| WF-06 | profile；最好有 WF-05 | `main_plan` | awaiting_confirmation | WF-07 |
| WF-07 | profile；最好有 WF-06 | `semester_tasks` | awaiting_confirmation | WF-08 |
| WF-08 | profile；最好有 WF-06/07 | `growth_review` | awaiting_confirmation | WF-09 |
| WF-09 | profile + 用户真实经历 | `resume_assets` | awaiting_confirmation | WF-10 |
| WF-10 | profile；可参考路径/规划 | `decision_trial` | awaiting_confirmation | WF-11 |
| WF-11 | profile | `habit_log` | awaiting_confirmation | WF-12 |
| WF-12 | 全部已有状态 | `final_review` | awaiting_confirmation | 推荐返回点 |

## 3. 统一确认输出变化

以任意模块 `module_name` 为例，确认前：

```json
{
  "module_name": {
    "status": "awaiting_confirmation",
    "draft": {"本轮结果":"..."},
    "confirmed": {}
  }
}
```

用户明确确认后：

```json
{
  "module_name": {
    "status": "completed",
    "draft": {},
    "confirmed": {"本轮结果":"..."}
  }
}
```

并同时更新：

```json
{
  "current_status": "completed",
  "completed_workflows": ["当前 WF"],
  "next_workflow": "默认下一 WF"
}
```

## 4. 为什么结束节点不直接引用 12 个 output

平台的参数引用是静态配置。一个结束节点无法可靠判断 12 条分支中本轮究竟执行了哪个 `output`。如果给结束节点同时添加 12 个引用，未执行分支可能造成空值校验或混乱。

因此 MVP 使用：

```text
业务大模型 → 对应消息节点显示 JSON → 固定结束节点
```

这与详细版 WF-01 当前“上方消息给业务答复、结束节点固定收口”的做法一致，也最容易调试。
