# MVP MAIN 工作流：逐节点搭建教程

## 1. 最终画布完成什么

MAIN 接收开始节点唯一输入 `AGENT_USER_INPUT`，从当前对话历史恢复 `state_json`，判断本轮应该进入 WF-01～WF-12 的哪一个模块，把用户输入和完整状态交给对应业务大模型，最后显示完整 JSON。

MVP 不创建 12 个独立工作流。12 个 WF 是同一个 MAIN 画布中的 12 个大模型节点。

## 2. 先新建工作流

1. 回到讯飞星辰工作流列表。
2. 点击新建工作流。
3. 名称填写：

```text
MVP-MAIN 大学人生规划模拟器
```

4. 简介填写：

```text
使用单一自然语言输入，在当前对话中依次运行用户画像、模拟、测试、路径、规划、任务和复盘的最小验证版。
```

5. 分类选择与你项目一致的分类。
6. 暂时不要发布，先在编辑器完成连续性门禁。

## 3. N00 开始节点

开始节点保留平台自带的一行：

| 变量名 | 类型 | 描述 | 必填 |
|---|---|---|---|
| `AGENT_USER_INPUT` | String | 用户本轮自然语言 | 是 |

不要添加 `uid`、`request_time`、`confirmation_token` 或 `state_json`。

## 4. N01 路由大模型

从左侧拖入“大模型”，重命名：

```text
N01 路由大模型：恢复状态并选择 WF
```

### 4.1 模型和输入

- 模型：`Spark4.0 Ultra`。
- 勾选“对话历史”。
- 对话轮数：建议 `20`；若平台允许更高可设 `30`。
- 输入添加一行：

| 参数名 | 参数值类型 | 引用 |
|---|---|---|
| `user_input` | 引用 | N00 开始 / `AGENT_USER_INPUT` |

### 4.2 系统提示词

复制下面全文：

```text
你是“大学人生规划模拟器”MVP 的总路由器。你只负责恢复上一轮完整状态、识别本轮动作并选择 WF-01～WF-12；你不得代替业务模块生成画像、计划或测试结果。

一、恢复 prior_state
1. 检查对话历史，从最近一条助手消息向前查找。
2. 找到包含 schema_version="mvp-1.0" 且同时包含 profile、virtual_university、survival_adventure、path_recommendation、parallel_lives、main_plan、semester_tasks、growth_review、resume_assets、decision_trial、habit_log、final_review 的完整 JSON，将它作为 prior_state。
3. 忽略单独的 workflow_finished、普通说明文字和不完整 JSON。
4. 如果历史中没有完整状态，必须使用下面这个对象作为 prior_state，不得自行缩减字段：
{"schema_version":"mvp-1.0","current_workflow":"WF-01","current_status":"collecting","completed_workflows":[],"last_user_intent":"","profile":{"status":"not_started","draft":{},"confirmed":{}},"virtual_university":{"status":"not_started","draft":{},"confirmed":{}},"survival_adventure":{"status":"not_started","draft":{},"confirmed":{}},"path_recommendation":{"status":"not_started","draft":{},"confirmed":{}},"parallel_lives":{"status":"not_started","draft":{},"confirmed":{}},"main_plan":{"status":"not_started","draft":{},"confirmed":{}},"semester_tasks":{"status":"not_started","draft":{},"confirmed":{}},"growth_review":{"status":"not_started","draft":{},"confirmed":{}},"resume_assets":{"status":"not_started","draft":{},"confirmed":{}},"decision_trial":{"status":"not_started","draft":{},"confirmed":{}},"habit_log":{"status":"not_started","draft":{},"confirmed":{}},"final_review":{"status":"not_started","draft":{},"confirmed":{}},"reply":"","next_workflow":"WF-01","warnings":[]}
5. 不得因为本轮输入较短而清空 prior_state。

二、识别 user_action
只允许：
- start：开始当前或指定模块；
- answer：回答当前模块的问题；
- confirm：确认当前模块草稿；
- modify：修改当前模块草稿；
- cancel：取消当前模块草稿；
- continue：进入默认下一模块；
- jump：明确跳到指定模块；
- unknown：无法判断。

“确认、没问题、就这样、保存、继续”在当前模块等待确认时优先识别为 confirm。
“修改、改成、补充、更正”识别为 modify。
“取消、不做了、放弃这份草稿”识别为 cancel。
只有当前模块已经 completed，用户再说“继续/下一步”，才识别为 continue。

三、选择 target_workflow
模块表：
WF-01 用户画像；WF-02 虚拟大学；WF-03 生存大冒险；
WF-04 五路径推荐；WF-05 平行人生；WF-06 主规划；
WF-07 学期任务；WF-08 成长复盘；WF-09 履历素材；
WF-10 决策与七天试错；WF-11 微习惯；WF-12 会话复盘。

规则：
1. prior_state.current_status=awaiting_confirmation 时，confirm/modify/cancel 必须继续路由到 prior_state.current_workflow，由业务节点处理草稿；路由器不得自行确认。
2. answer 必须留在 current_workflow。
3. continue 路由到 prior_state.next_workflow。
4. jump 路由到用户明确指定模块。
5. 没有历史状态时默认 WF-01。
6. WF-02～WF-11 至少需要 prior_state.profile.confirmed 非空；缺少时改为 WF-01，并说明需要先完成最小画像。
7. 用户同时提出多个目标时，选择依赖最靠前的一个。
8. 无法判断时保留 current_workflow；仍无法确定则使用 WF-01。

四、输出
只输出一个合法 JSON 对象，不要代码围栏，不要解释文字：
{
  "target_workflow": "WF-01",
  "route_reason": "",
  "user_action": "start",
  "requested_jump": "",
  "prior_state": {}
}

prior_state 必须是恢复后的完整对象，不得省略任何模块，不得改写任何业务结果。
```

### 4.3 用户提示词

```text
用户本轮输入：
{{user_input}}

请恢复上一轮完整状态并选择本轮唯一的 target_workflow。
```

### 4.4 输出

- 输出格式：`text`。
- 变量名保持平台默认 `output`。
- 描述填写：`包含 target_workflow、user_action 和完整 prior_state 的路由 JSON`。

## 5. N02 变量提取器

拖入“变量提取器”，重命名：

```text
N02 变量提取器：只提取 target_workflow
```

### 5.1 模型和输入

- 模型：`Spark4.0 Ultra`。
- 输入区域只能有一行：

| 参数名 | 参数值类型 | 引用 |
|---|---|---|
| `input` | 引用 | N01 / `output` |

不要把 `user_input` 和 `prior_state` 分成多行输入。它们已经包含在 N01 的单个 JSON 字符串中。

### 5.2 输出

点击“+ 添加”，只配置：

| 变量名 | 类型 | 描述 |
|---|---|---|
| `target_workflow` | String | 只允许 WF-01 至 WF-12 |

## 6. N03 MAIN 总分支器

拖入“分支器”，重命名：

```text
N03 MAIN 总分支器：进入 WF-01～WF-12
```

点击“+ 添加分支”，配置 12 条。每条都使用：

- 引用变量：N02 / `target_workflow`
- 选择条件：等于
- 比较类型：输入或固定值，不选引用
- 比较值：下表对应值

| 分支 | 比较值 | 连接 |
|---|---|---|
| 1 | `WF-01` | N04 WF-01 |
| 2 | `WF-02` | N05 WF-02 |
| 3 | `WF-03` | N06 WF-03 |
| 4 | `WF-04` | N07 WF-04 |
| 5 | `WF-05` | N08 WF-05 |
| 6 | `WF-06` | N09 WF-06 |
| 7 | `WF-07` | N10 WF-07 |
| 8 | `WF-08` | N11 WF-08 |
| 9 | `WF-09` | N12 WF-09 |
| 10 | `WF-10` | N13 WF-10 |
| 11 | `WF-11` | N14 WF-11 |
| 12 | `WF-12` | N15 WF-12 |

默认分支连接澄清消息，不能随便进入某一个 WF。

## 7. N04～N15 业务大模型的共同配置

每个节点都按对应提示词文件配置。共同输入固定为两行：

| 参数名 | 参数值类型 | 引用 |
|---|---|---|
| `user_input` | 引用 | N00 / `AGENT_USER_INPUT` |
| `router_context` | 引用 | N01 / `output` |

模型统一先用 `Spark4.0 Ultra`。12 个业务节点全部关闭“对话历史”。它们只能相信 N01 本轮传来的 `router_context.prior_state`，避免某个分支节点使用自己的旧历史覆盖最新状态。整个 MAIN 只有 N01 路由大模型开启对话历史。

业务节点输出统一：

- 输出格式：`text`
- 输出变量：`output`
- 描述：`更新后的完整 mvp-1.0 state_json`

节点与提示词文件：

| 节点 | 提示词 |
|---|---|
| N04 WF-01 | [WF-01](prompts/WF-01-user-profile.md) |
| N05 WF-02 | [WF-02](prompts/WF-02-virtual-university.md) |
| N06 WF-03 | [WF-03](prompts/WF-03-survival-adventure.md) |
| N07 WF-04 | [WF-04](prompts/WF-04-path-recommendation.md) |
| N08 WF-05 | [WF-05](prompts/WF-05-parallel-lives.md) |
| N09 WF-06 | [WF-06](prompts/WF-06-main-plan.md) |
| N10 WF-07 | [WF-07](prompts/WF-07-semester-tasks.md) |
| N11 WF-08 | [WF-08](prompts/WF-08-growth-review.md) |
| N12 WF-09 | [WF-09](prompts/WF-09-resume-entry.md) |
| N13 WF-10 | [WF-10](prompts/WF-10-decision-trial.md) |
| N14 WF-11 | [WF-11](prompts/WF-11-micro-habits.md) |
| N15 WF-12 | [WF-12](prompts/WF-12-session-recap.md) |

## 8. 结果消息节点

每个业务大模型后各放一个“消息”节点。不要尝试让一个消息节点静态引用 12 个上游输出。

以 WF-01 为例：

1. 输入添加：

| 参数名 | 参数值类型 | 引用 |
|---|---|---|
| `result` | 引用 | N04 / `output` |

2. 回答内容：

```text
{{result}}
```

3. 关闭流式输出。

WF-02～WF-12 分别引用各自业务大模型的 `output`。

默认分支消息内容：

```text
我暂时没有判断出你想进入哪个模块。你可以说“建立画像”“继续下一步”，或明确说“跳到 WF-04 路径推荐”。
```

## 9. 结束节点

所有消息节点连接同一个结束节点。

- 回答模式：`返回设定格式配置的回答`
- 输出参数名：`output`
- 参数值类型：`输入`
- 值：`workflow_finished`
- 思考内容：留空
- 回答内容：留空
- 流式输出：关闭

用户看到的主要内容来自上方消息节点；`workflow_finished` 只是让工作流合法结束。

## 10. 不要马上复制全部节点

先只建立 WF-01、WF-02 两条分支，并完成[连续性门禁](TEST-GUIDE.md)。确认路由节点第二轮能看到上一轮完整 JSON 后，再复制业务节点和消息节点扩展到 WF-12。
