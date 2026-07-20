# 工作流共享协议

本文是 `MAIN-00` 和 WF-01～WF-09 的统一运行契约。所有页面配置以[平台 UI 配置契约](PLATFORM-UI-CONTRACT.md)为准；任何单份教程与本文冲突时，先停止搭建并按本文修正文档。

## 1. 运行拓扑

```text
讯飞星火/Desk 用户
→ MAIN-00（唯一公开入口）
→ Agent 智能决策节点
→ WF-01～WF-09（同账号、已发布的 MCP Server）
→ MAIN-00 最终回复
```

- MAIN-00 是唯一允许添加 Agent 智能决策和 MCP 工具的工作流。
- WF-01～WF-09 不得调用其他 Agent、工作流或 MCP，不做多层嵌套。
- MAIN 可以在一轮内连续调用多个工具；不设人为的 1 次或 2 次上限。
- 官方页面最多添加 30 个工具、最大推理轮次 100；本项目只使用 9 个工具。
- 子工具返回 `awaiting_confirmation`、`awaiting_user_input`、`needs_input`、失败或安全状态时，MAIN 必须停止继续调用并先回复用户。

## 2. 用户看到的输入

用户在发布后的 MAIN 对话框中只输入自然语言，例如：

```text
我是大一计算机学生，想先梳理一下自己的情况。
```

用户不需要也不得被要求输入：

- JSON；
- `uid` 或 `user_key`；
- `request_time`；
- `assessment_id`、`plan_id`、`task_id` 等业务键；
- confirmation token 或恢复码；
- 上一张工作流输出的完整 JSON。

## 3. 子工作流唯一开始参数

WF-01～WF-09 的开始节点只保留平台默认项：

```text
AGENT_USER_INPUT:String
```

不要点击“+ 添加”创建其他开始变量。MAIN 调用 MCP 工具时，把内部档案键和用户原话组成一个扁平 JSON 字符串，作为唯一参数的值：

```json
{
  "user_key": "uk_0123456789abcdef0123456789abcdef",
  "user_input": "用户本轮自然语言"
}
```

MCP 工具参数示意：

```json
{
  "AGENT_USER_INPUT": "{\"user_key\":\"uk_0123456789abcdef0123456789abcdef\",\"user_input\":\"用户本轮自然语言\"}"
}
```

外层和内层都只有字符串字段。自然语言中的双引号和反斜线由 MAIN 的工具调用序列化处理，用户不手写转义。

## 4. 首个代码节点的统一职责

每张业务工作流的 N00A 都必须在任何数据库节点之前完成：

1. 确认外层值是非空 String；
2. 解析顶层扁平 JSON；
3. 只接受 `user_key` 和 `user_input`；
4. 检查 `user_key` 以 `uk_` 开头；
5. 检查前缀后正好 32 个小写十六进制字符；
6. 检查 `user_input` 非空且不超过教程规定的长度；
7. 输出 `input_valid:Boolean`、`user_key:String`、`user_input:String`、`input_error:String`；
8. N00B 分支器只有 `input_valid=true` 才进入数据库或模型，默认路线返回 `validation_failed`。

代码节点不得信任用户自然语言中出现的“改用某个 user_key”。数据库只使用 N00A 从包装字符串确定性解析出的 `user_key`。

## 5. 同一对话与新对话

MAIN 首轮生成 `uk_` 加 32 位小写十六进制的随机样式键，并保存到变量存储器。后续轮次先读取它，不重新生成。

| 用户动作 | 结果 |
|---|---|
| 临时退出，再打开原对话 | 只要平台仍保留该会话变量，就继续同一 `user_key` 和业务档案 |
| 刷新页面后打开原对话 | 按同一原对话处理，先用发布环境实际验证 |
| 点击“新建对话” | 平台会清空会话变量，MAIN 生成新的 `user_key`，形成新档案 |
| 删除原对话 | 会话变量被清空；当前版本没有账号级恢复入口 |
| 平台主动清理历史 | 官方没有给出发布后变量的固定保留期限，不能承诺永久恢复 |

当前 UI 没有暴露可供 SQL 引用的终端账号 ID，因此 `user_key` 是会话级档案键，不是实名账号身份。对外介绍必须保留这个边界。

## 6. 数据库用户隔离

每张业务表都显式添加：

```text
user_key:String
```

平台自动创建的 `id`、`uid`、`create_time` 继续保留，但职责不同：

| 字段 | 来源 | 项目用途 |
|---|---|---|
| `id` | 平台自动 | 单行更新或调试定位 |
| `uid` | 平台自动 | 仅保留的系统字段；不作为本项目 SQL 身份条件 |
| `create_time` | 平台自动 | 记录创建顺序 |
| `user_key` | MAIN 生成并由 N00A 解析 | 所有业务查询、更新范围和回读的用户隔离键 |

正确读取：

```sql
SELECT id, user_key, record_version, create_time
FROM example_table
WHERE user_key='{{user_key}}'
ORDER BY record_version DESC, create_time DESC
LIMIT 1;
```

禁止写法：

```text
WHERE uid='{{uid}}'
WHERE user_key='{{AGENT_USER_INPUT}}'
不带 user_key 读取整张业务表
```

数据库节点输入的 `user_key` 必须引用当前节点上游 N00A 的同名输出；变量下拉框没有 N00A 时，说明节点没有连在有效上游链路上，应先修正连线。

## 7. 时间、版本与业务键

- 开始节点不接收时间。
- 插入顺序使用平台自动 `create_time`。
- 业务状态使用 Integer 版本字段，如 `record_version`、`state_version`、`assessment_version`。
- 新业务键由 `user_key + 固定实体名 + 顺序号` 组成，不依赖时间。
- 模型不得生成数据库主键、用户键或版本号；这些由代码节点根据回读状态计算。
- 关键记录优先追加版本。确需更新时，范围至少包含 `user_key`、业务键和当前状态/版本。
- 更新或正式确认后必须回读；不能只凭数据库节点 `isSuccess=true` 就声称内容一致。

## 8. 数据库固定输出的两层判断

自定义 SQL 和表单处理数据库节点固定输出：

```text
isSuccess:Boolean
message:String
outputList:Array<Object>
```

判断顺序固定为：

1. 分支器检查 `isSuccess == true`；默认/否进入 `read_failed` 或 `write_failed`。
2. 成功路线进入代码节点整理 `outputList`。
3. 代码节点输出 `has_record:Boolean`。
4. 下一分支器判断有记录或无记录。

`isSuccess=true && outputList=[]` 是“查询执行成功但没有记录”，不是数据库失败。教程和用户回复必须区分两者。

## 9. 变量提取器唯一输入

平台变量提取器只有一个固定输入：

```text
input｜引用｜上游节点/output
```

需要多个来源时使用：

```text
用户原话 + pending JSON + 历史状态
→ 文本处理节点：字符串拼接
→ output:String
→ 变量提取器：input 引用这个 output
```

推荐拼接规则：

```text
【用户本轮原话】
{{user_input}}

【当前待处理对象】
{{pending_json}}

【已有状态】
{{state_json}}
```

变量提取器输出多个字段是允许的；禁止的是为它添加多行输入。完整对象需要保存时输出 String，结构判断字段分别输出 Boolean/String/Integer/Array<String>。

## 10. 大模型与代码边界

### 10.1 大模型

- 负责自然语言意图、生成解释、生成业务草稿；
- 不负责 `isSuccess` 判断、版本号、用户键、SQL 范围；
- 状态机工作流关闭对话历史，只使用显式输入；
- 输出必须先进入变量提取器，再进入代码校验；
- 政策信息只能基于知识库结果，缺少来源时明确待核验。

### 10.2 代码

- 只使用 Python；
- 不写 `import`；
- `main()` 形参和页面输入参数名完全一致；
- 返回 dict；
- 所有分支返回同一组键；
- 页面输出区逐行声明所有返回键和类型；
- 不解析模型可能嵌套的任意 JSON；需要字段级校验时让变量提取器逐项输出；
- 只对 MAIN 包装的扁平两字段 JSON 使用教程提供的确定性解析器。

## 11. 决策与分支器

| 判断类型 | 使用节点 |
|---|---|
| 用户自然语言要做什么 | 决策节点或变量提取器 |
| `isSuccess == true` | 分支器 |
| `has_record == true` | 分支器 |
| `status` 是否等于枚举值 | 分支器 |
| 版本号、天数范围 | 代码校验后分支器 |

每个分支器都要配置默认/失败出口。任何未匹配值进入安全失败路线，不能停在画布上，也不能默认为成功。

## 12. 内部确认，不向用户显示 token

需要确认的对象：画像、主规划、重要规划切换、履历正式条目、七天试错启动、删除或不可逆覆盖。

确认依据是数据库中的最新 pending 状态和用户本轮明确意图，不是用户复制 token。确认成功必须满足：

1. 当前 `user_key` 查到对应 pending；
2. pending 状态和对象类型正确；
3. 用户明确说出对象和动作；
4. 写入范围包含 `user_key` 和业务键；
5. 写后回读一致。

明确确认示例：

```text
确认保存这份画像
确认采用这个主规划
确认保存这条履历
确认启动七天试错
```

以下表达不足以触发关键写入：

```text
好的
继续
就这样
可以吧
```

模糊表达返回 `needs_input`，并告诉用户可直接说哪一句，不把 token 暴露出来。

## 13. 子工作流结果契约

WF-01～WF-09 的唯一结束输出：

```text
result_json:String
```

结构固定为五个顶层 String 字段：

```json
{
  "workflow_id": "WF-01",
  "status": "awaiting_confirmation",
  "reply": "画像草稿已生成，请检查后回复：确认保存这份画像，或直接说明要修改什么。",
  "next_action": "confirm_or_modify_profile",
  "error_code": "none"
}
```

允许状态：

| 状态 | 含义 | MAIN 是否可继续调用其他工具 |
|---|---|---:|
| `needs_input` | 缺少必要事实或明确选择 | 否 |
| `awaiting_user_input` | 多轮事件/问题已保存，等待下一轮 | 否 |
| `awaiting_confirmation` | 草稿已保存，等待明确确认或修改 | 否 |
| `completed` | 无需持久化的当前目标完成 | 可以，若用户原请求还有明确后续 |
| `write_succeeded` | 写入并回读一致 | 可以，若用户原请求还有明确后续 |
| `write_failed` | 写入或回读失败 | 否 |
| `read_failed` | 数据库读取失败 | 否 |
| `validation_failed` | 输入、模型或业务结构无效 | 否 |
| `unsafe_request` | 高风险或不允许的请求 | 否 |

`reply` 只放用户需要看到的内容；完整业务对象写数据库，不通过 MCP 输出整份大 JSON。

## 14. MAIN 连续调用规则

MAIN 的 Agent 智能决策可以根据同一请求连续调用多个 MCP 工具，例如：

```text
“我完成了这周的项目任务，成果链接是……，顺便帮我复盘。”
→ WF-06 记录任务行动
→ WF-07 基于已写入证据复盘
→ MAIN 汇总回复
```

但以下请求必须分轮：

```text
“帮我建立画像，再直接生成正式主规划。”
→ WF-01 先生成画像草稿并返回 awaiting_confirmation
→ MAIN 停止，等待用户确认
→ 下一轮确认成功后再继续后续工具
```

停止条件：任务完成、缺输入、等待确认、等待多轮回答、失败、安全边界、继续调用无新增价值、接近超时。

## 15. 失败与异常路线

统一错误码：

- `invalid_envelope`
- `invalid_user_key`
- `missing_user_input`
- `read_failed`
- `write_failed`
- `readback_mismatch`
- `invalid_model_output`
- `missing_prerequisite`
- `ambiguous_confirmation`
- `unsafe_request`
- `tool_unavailable`

所有异常路线都要先整理五字段 `result_json`，再进入结束节点。错误回复不能包含数据库 SQL、其他记录、内部 user_key、模型思考过程或平台密钥。

## 16. 发布与调试门禁

每张业务工作流完成以下检查后才发布为 MCP Server：

1. 开始节点只有 `AGENT_USER_INPUT:String`。
2. 格式错误在首次数据库读取前结束。
3. 所有 SQL 都含 `user_key` 条件。
4. 每个变量提取器只有一个 input。
5. 每个代码块可编译、无 import、形参与页面输入一致。
6. 每个分支器的命中路线和默认路线都实际跑过。
7. 写入失败时回复不含“已保存”。
8. 回读不一致时状态为 `write_failed`。
9. 结束输出是紧凑 `result_json`，不是 `workflow_finished`。
10. 子工作流画布没有 Agent 智能决策、工作流节点或 MCP 调用。

MAIN 发布到星火/Desk 前再完成：

1. 九个 MCP 工具都来自当前账号已发布列表。
2. 工具说明写清适用场景、前置条件和停止状态。
3. 同一原对话连续三轮保持相同档案。
4. 新建对话生成不同档案。
5. 一轮单工具测试通过。
6. 一轮双工具连续调用测试通过。
7. 等待确认时没有越过边界继续调用。
8. 在“发布管理 → 详情 → Trace”核对真实工具调用顺序。
