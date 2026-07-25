# MVP 统一状态协议

## 1. 为什么必须有统一状态

MVP 暂时没有数据库。上一轮业务大模型输出的完整 JSON，就是下一轮的临时状态。路由节点从对话历史读取它，再把它放进 `router_context.prior_state` 交给本轮业务节点。

任何业务节点如果只返回自己的局部结果，下一轮都会丢失其他模块。因此 12 个业务节点都必须返回完整状态对象。

## 2. 首轮初始状态

路由节点找不到历史状态时，必须创建下面的完整对象：

```json
{
  "schema_version": "mvp-1.0",
  "current_workflow": "WF-01",
  "current_status": "collecting",
  "completed_workflows": [],
  "last_user_intent": "",
  "profile": {"status":"not_started","draft":{},"confirmed":{}},
  "virtual_university": {"status":"not_started","draft":{},"confirmed":{}},
  "survival_adventure": {"status":"not_started","draft":{},"confirmed":{}},
  "path_recommendation": {"status":"not_started","draft":{},"confirmed":{}},
  "parallel_lives": {"status":"not_started","draft":{},"confirmed":{}},
  "main_plan": {"status":"not_started","draft":{},"confirmed":{}},
  "semester_tasks": {"status":"not_started","draft":{},"confirmed":{}},
  "growth_review": {"status":"not_started","draft":{},"confirmed":{}},
  "resume_assets": {"status":"not_started","draft":{},"confirmed":{}},
  "decision_trial": {"status":"not_started","draft":{},"confirmed":{}},
  "habit_log": {"status":"not_started","draft":{},"confirmed":{}},
  "final_review": {"status":"not_started","draft":{},"confirmed":{}},
  "reply": "",
  "next_workflow": "WF-01",
  "warnings": []
}
```

## 3. 模块外壳

每个模块固定使用：

```json
{
  "status": "not_started",
  "draft": {},
  "confirmed": {}
}
```

合法状态：

| 状态 | 含义 |
|---|---|
| `not_started` | 尚未进入 |
| `collecting` | 正在问题目或补充信息 |
| `awaiting_confirmation` | 已有完整草稿，等待确认 |
| `completed` | 用户已明确确认 |
| `cancelled` | 用户取消了本轮草稿 |
| `error` | 无法生成可靠结果 |

## 4. 四种动作

### 4.1 生成或继续

- 只更新当前模块的 `draft`。
- 模块未完成时使用 `collecting`。
- 已形成完整结果时使用 `awaiting_confirmation`。
- 不得改动 `confirmed`。

### 4.2 修改

- 以现有 `draft` 为基础合并用户明确修改。
- 没有 `draft` 时，以 `confirmed` 为基础创建新草稿。
- 修改后回到 `awaiting_confirmation`。

### 4.3 确认

只有当前模块存在非空 `draft` 且状态为 `awaiting_confirmation` 时才允许确认：

```text
confirmed = draft
draft = {}
status = completed
```

同时把当前 WF 加入 `completed_workflows`。数组中不得重复。

### 4.4 取消

```text
draft = {}
status = cancelled
```

已有 `confirmed` 必须保留。取消草稿不等于删除历史确认结果。

## 5. 完整状态不可变规则

业务节点处理前，先深度复制 `router_context.prior_state`，再只修改：

- `current_workflow`
- `current_status`
- `last_user_intent`
- 当前模块字段
- `completed_workflows`
- `reply`
- `next_workflow`
- `warnings`

不得清空或重写其他模块。不得把缺失历史解释为用户删除数据。

## 6. JSON 输出规则

所有大模型节点都必须遵守：

1. 只输出一个 JSON 对象。
2. 不得加 ```json 代码围栏。
3. 不得在 JSON 前后解释。
4. Boolean 使用 `true/false`，不得使用 `"true"`。
5. 空对象使用 `{}`，空数组使用 `[]`，不得用空字符串代替。
6. 所有键使用双引号。
7. 输出必须包含全部 12 个模块字段。
8. `reply` 不得为空。

## 7. 前置数据规则

| 目标模块 | MVP 最低前置 |
|---|---|
| WF-01 | 无 |
| WF-02 | `profile.confirmed` 非空 |
| WF-03 | `profile.confirmed` 非空 |
| WF-04 | `profile.confirmed` 非空；最好有 WF-03 结果 |
| WF-05 | `profile.confirmed` 非空；最好有 WF-04 结果 |
| WF-06 | `profile.confirmed` 非空；最好有 WF-05 结果 |
| WF-07 | `profile.confirmed` 非空；最好有 WF-06 结果 |
| WF-08 | `profile.confirmed` 非空；最好有 WF-07 结果 |
| WF-09 | `profile.confirmed` 非空 |
| WF-10 | `profile.confirmed` 非空 |
| WF-11 | `profile.confirmed` 非空 |
| WF-12 | 无；有历史时总结历史 |

用户主动跳转但缺少画像时，路由到 WF-01，并在 `route_reason` 中说明“目标模块需要最小画像”。
