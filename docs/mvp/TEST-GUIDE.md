# MVP MAIN 完整调试教程

## 1. 调试前检查

在平台打开 `MVP-MAIN 大学人生规划模拟器`，逐项确认：

- N00 只有 `AGENT_USER_INPUT:String`。
- N01 已勾选对话历史，轮数至少 20。
- N04～N15 的业务大模型全部关闭对话历史。
- N01 输入 `user_input` 引用 N00/AGENT_USER_INPUT。
- N02 只有一行输入 `input=N01/output`。
- N02 输出只有 `target_workflow:String`。
- N03 的 12 个比较值使用固定值，不是引用。
- 每个业务大模型都有 `user_input` 与 `router_context` 两行输入。
- 每个业务大模型输出格式都是 text，变量名为 output。
- 每个消息节点关闭流式输出。
- 结束节点固定输出 `workflow_finished`。

开始完整测试前，点击调试面板的“重新开始新对话”，避免旧版 JSON 混入历史。

## 2. 第一阶段：JSON 基础门禁

### 测试 A：首轮路由

输入：

```text
我是大一计算机专业学生，想建立画像
```

依次打开运行结果：

1. N01/output 必须是合法 JSON。
2. `target_workflow` 必须为 `WF-01`。
3. `prior_state.schema_version` 必须为 `mvp-1.0`。
4. N02/target_workflow 必须为 `WF-01`，不能带解释文字。
5. N04/output 必须包含 12 个模块字段。
6. `profile.status` 应为 `awaiting_confirmation`。
7. `profile.draft` 应包含 `grade` 和 `major`。
8. `completed_workflows` 此时不能包含 WF-01。

如果消息显示“模型 JSON 无效”或变量提取失败：

- 检查 N01 是否输出了 ```json 围栏；
- 检查 JSON 前后是否有解释；
- 检查键名是否使用双引号；
- 检查 N02 是否错误引用 N00，而不是 N01/output。

### 测试 B：确认仍由 WF-01 处理

不要重新开始对话。在同一个调试对话输入：

```text
确认，继续
```

预期：

- N01 能从历史找到上一轮完整状态；
- N01/target_workflow 仍为 `WF-01`；
- N01/user_action 为 `confirm`；
- N04 把 `profile.draft` 复制到 `profile.confirmed`；
- N04 输出 `profile.status=completed`；
- `completed_workflows` 包含且只包含一个 `WF-01`；
- `next_workflow=WF-02`。

如果 N01 直接路由到 WF-02，说明路由提示词没有遵守“确认由当前业务节点处理”。重新检查 N01 系统提示词第 3 部分规则 1。

### 测试 C：默认进入下一模块

仍在同一对话输入：

```text
继续
```

预期：

- N01/user_action=`continue`；
- N01/target_workflow=`WF-02`；
- N05 能看到非空 `profile.confirmed`；
- N05 生成虚拟大学事件 1；
- `virtual_university.status=collecting`；
- `profile.confirmed` 与上一轮完全一致。

这一步通过，才证明“路由器 → 不同业务分支”的状态连续性成立。

## 3. 连续性失败时怎么处理

出现以下任一情况就停止搭建其余模块：

- 第二轮 N01/prior_state 又变成空初始状态；
- 第三轮 N01 不知道 `next_workflow=WF-02`；
- WF-02 收到的画像为空；
- 进入新分支后其他模块字段被清空。

这不是业务提示词问题，而是平台没有把消息节点输出作为 N01 可见的全局对话历史。此时：

1. 不要增加数据库来掩盖问题，因为当前目标是验证无数据库 MVP。
2. 暂停 N02、N03 和 12 条分支。
3. 改用一个总控大模型节点，使每一轮都经过同一个节点。
4. 完成单节点验证后，再决定接回数据库还是恢复模块分支。

## 4. 第二阶段：WF-02 与 WF-03 多轮状态

### WF-02

1. 回答事件 1 的明确选项。
2. 确认 `event_index` 推进且 `choice_history` 增加一项。
3. 输入模糊回答“随便”，确认事件不推进。
4. 完成 3 个事件，确认状态变为 awaiting_confirmation。
5. 输入“确认”，确认 WF-02 completed，next_workflow=WF-03。
6. 再输入“继续”，进入 WF-03。

### WF-03

1. 回答三个场景题。
2. 每题后 answers 只增加一项。
3. 第三题后必须出现五路径定性信号、能力信号、优势、短板和待验证假设。
4. 确认后进入 WF-04。

## 5. 第三阶段：WF-04～WF-12 顺序测试

每个模块都使用相同节奏：

```text
输入“继续”
→ 生成或开始本模块
→ 按模块要求补充/回答
→ 获得 awaiting_confirmation 草稿
→ 输入“确认”
→ 本模块 completed
→ 再输入“继续”
→ 进入下一模块
```

### WF-04 五路径推荐

- routes 正好 5 项且路径不重复。
- 不出现成功率或录取概率。
- warnings 包含“无知识库 MVP”和“官方复核”。

### WF-05 平行人生

- 至少 2 个、最多 3 个版本。
- 每个版本使用同一个 common_start。
- 比较维度包含成本、风险、可逆性和挤出效应。

### WF-06 主规划

- 多版本未选择时先问用户选哪个。
- 确认草稿后才进入 main_plan.confirmed。
- 计划包含学期、月度、四周行动、成功标准、风险、替代方案和不做清单。

### WF-07 学期任务

- 首次生成 3～5 个任务。
- “完成 T01”但没给实际结果时不得标记 completed。
- 延期缺少日期或原因时不得更新。

### WF-08 成长复盘

- 明确事实、行为证据和模型推断分开。
- recommendation 只能为 continue、adjust、consider_switch。
- 确认复盘不能自动改写 main_plan.confirmed。

### WF-09 履历素材

- 输入“我参加过比赛”时先追问。
- 没有数字时 metrics 必须为空。
- 要求伪造经历时拒绝。

### WF-10 决策与试错

- “纠结考研还是就业”进入 decision_analysis。
- “想试七天科研”进入 seven_day_trial。
- 确认试错不等于主规划已改。

### WF-11 微习惯

- 计划和已完成记录分开。
- 支出金额保留原话。
- 疼痛、疾病或危险动作触发安全出口。

### WF-12 会话复盘

- completed_modules 只来自 completed_workflows。
- pending_drafts 单独列出。
- next_three_actions 不超过 3 项。
- 确认时说明状态只存在当前调试对话。

## 6. 主动跳转测试

重新开始一场新对话。

### 没有画像时跳转

输入：

```text
跳到 WF-04，直接给我路径推荐
```

预期 N01 路由到 WF-01，而不是 WF-04；route_reason 说明缺少最小画像。

### 有画像时跳转

先完成并确认 WF-01，然后输入：

```text
跳到 WF-10，我想比较考研和就业
```

预期进入 WF-10。WF-02～WF-09 不得被自动标记 completed。

### 待确认时跳转

让 WF-04 生成草稿但不要确认，输入：

```text
先跳到 WF-11
```

预期允许进入 WF-11，但 WF-04 仍保持 awaiting_confirmation；不得把 WF-04 加入 completed_workflows。

## 7. 修改、取消和重复确认

### 修改

WF-01 草稿生成后输入：

```text
把城市偏好改成杭州，其他保持不变
```

只有指定字段变化。其他模块完全不变。

### 取消草稿

输入：

```text
取消这份草稿
```

当前模块 draft 清空；已有 confirmed 保留。

### 重复确认

模块已经 completed 后再次输入“确认”：

- 不得在 completed_workflows 中重复添加；
- 没有新 draft 时不得伪造新确认；
- reply 应说明当前没有待确认草稿，并提示继续或修改。

## 8. 状态体积检查

每完成三个模块，复制最新业务节点 output 到文本编辑器观察长度。

建议：

- `reply` 控制在约 300 个汉字以内；
- 每个列表只保留最有用的 3～5 项；
- 不保存完整对话原文；
- 不重复保存相同画像到每个模块；
- 整体 JSON 尽量控制在约 30,000 字符以内。

如果越到后面输出被截断或 JSON 缺少结尾：

1. 缩短各模块数组；
2. 减少 N01 对话历史轮数，但不能少到丢失最近完整状态；
3. 优先切换到数据库正式版，不要继续依赖无限增长的对话 JSON。

## 9. 最终验收表

- [ ] 用户始终只填写 AGENT_USER_INPUT。
- [ ] 连续三轮门禁通过。
- [ ] N01 每轮恢复完整 prior_state。
- [ ] N02 只有一个输入参数。
- [ ] 12 个分支都能命中。
- [ ] 默认顺序正确。
- [ ] 明确跳转正确。
- [ ] 缺画像时先回 WF-01。
- [ ] 每个模块的 draft 与 confirmed 分离。
- [ ] 取消不会删除 confirmed。
- [ ] completed_workflows 无重复。
- [ ] 每轮都是合法、完整 JSON。
- [ ] 所有其他模块在本轮执行后仍然存在。
- [ ] WF-04 带时效与官方复核提醒。
- [ ] WF-09 不编造履历。
- [ ] WF-11 健康安全出口有效。
- [ ] WF-12 区分已确认与待确认结果。
- [ ] 结束节点正常运行且不覆盖消息 JSON。
