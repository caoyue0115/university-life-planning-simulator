# WF-01 单参数入口改造设计

## 目标

把 WF-01 从四个开始参数改成只有一个平台系统参数 `AGENT_USER_INPUT:String`，使它能够作为单参数工作流被 MAIN 或 API 稳定调用，同时保留用户识别、画像草稿、确认 token、数据库回读和错误分支的完整能力。

## 当前问题

现有 WF-01 在开始节点同时定义：

```text
AGENT_USER_INPUT
uid
confirmation_token
request_time
```

多参数工作流只能发布为 API，不能作为平台内部可选择的已发布工作流被 MAIN 直接编排。现有教程中的数据库、大模型、代码和确认节点又直接引用这三个附加开始变量，因此不能只删除开始节点字段，必须同步改造所有下游引用。

## 选定方案

WF-01 对外只接收一条 JSON 字符串。调用方把业务字段放进 `AGENT_USER_INPUT`：

```json
{
  "uid": "test_user_001",
  "user_input": "我是大一学生，计算机专业，想建立画像",
  "confirmation_token": "",
  "request_time": "2026-07-19 16:30:00"
}
```

字段规则：

| 字段 | 类型 | 必填 | 规则 |
|---|---|---|---|
| `uid` | String | 是 | 去除首尾空格后不得为空；数据库按此字段隔离用户。 |
| `user_input` | String | 是 | 用户本轮真正说的话；去除首尾空格后不得为空。 |
| `confirmation_token` | String | 否 | 首次建档、修改和取消时允许为空；确认轮传上一轮返回值。 |
| `request_time` | String | 否 | 推荐格式 `YYYY-MM-DD HH:mm:ss`；缺失时由解析代码生成当前时间。 |

不采用分隔符字符串，因为用户文本可能包含相同分隔符；不采用大模型提取 uid 和 token，因为身份与确认凭证不能依赖概率判断。

## 新增入口模块

保留现有 N01～N30 编号，避免整份教程、现有画布和截图全部重编号。在 N00 与 N01 之间新增三节点：

```text
N00 开始
  ↓
N00A 代码：解析单参数
  ↓
N00B 分支器：单参数有效？
  ├─ 是 → N01 数据库：读取画像和草稿
  └─ 否 → N00C 消息：输入格式错误 → N30 结束
```

### N00

只保留平台固定变量：

```text
AGENT_USER_INPUT:String（必填）
```

### N00A

输入：

```text
raw_input = N00 / AGENT_USER_INPUT
```

输出：

| 变量 | 类型 | 用途 |
|---|---|---|
| `uid` | String | N01、N09、N11、N13、N19、N21 使用。 |
| `user_input` | String | N04 大模型使用。 |
| `confirmation_token` | String | N17 确认校验使用。 |
| `request_time` | String | N09、N17 和数据库时间字段使用。 |
| `input_valid` | Boolean | N00B 判断是否允许进入数据库。 |
| `input_error` | String | N00C 给出可操作的格式错误。 |

解析必须捕获所有异常，并始终返回上述六个同名键，不允许代码节点因坏 JSON 直接中断整个工作流。

### N00B

判断 `N00A/input_valid`：

```text
true  → N01
false → N00C
```

### N00C

关闭流式输出，回答内容说明：WF-01 只接收 JSON 字符串，`uid` 和 `user_input` 必填，并附 `N00A/input_error`。该节点连接 N30，不允许悬空。

## 下游引用改造

| 节点 | 旧引用 | 新引用 |
|---|---|---|
| N01 数据库 | `N00/uid` | `N00A/uid` |
| N04 大模型 | `N00/AGENT_USER_INPUT` | `N00A/user_input` |
| N09 代码 | `N00/uid`、`N00/request_time` | `N00A/uid`、`N00A/request_time` |
| N11 数据范围 | `N00/uid` | `N00A/uid` |
| N13 新增数据 | 开始节点 uid 或缺省 | 明确写入 `N00A/uid`；平台固定系统字段仍按真实页面保留。 |
| N17 代码 | `N00/confirmation_token`、`N00/request_time` | `N00A/confirmation_token`、`N00A/request_time` |
| N19 数据范围 | `N00/uid` | `N00A/uid` |
| N21 数据库 | `N00/uid` | `N00A/uid` |

N04 的输入参数名统一改为 `user_input`，系统提示词与用户提示词同步引用 `{{user_input}}`，不继续把包装后的整段 JSON 交给大模型。

## 流程图要求

草稿轮完整图必须从 N00 开始显示 N00A、N00B 和 N00C。N00B 的“否”分支必须明确结束于 N30。确认轮图从 N17 开始，业务逻辑保持不变，但所有文字说明中的 token 和时间来源改为 N00A。

重新渲染：

```text
docs/workflows/images/WF-01-draft-round.png
docs/workflows/images/WF-01-confirm-round.png
```

确认轮图片如图形内容未变化，可以重新验证而不强制改变像素内容；草稿轮图片必须反映新的入口节点。

## 调试与调用契约

平台调试面板只填写一个字段 `AGENT_USER_INPUT`。教程必须提供以下六组可直接复制的完整 JSON：

1. 新用户首次建档。
2. 已有草稿后的修改。
3. 使用正确 token 确认。
4. 用户取消。
5. 错误 token。
6. 非法 JSON 或缺少 `uid`。

API 或 MAIN 的外层调用仍只有一个参数：

```json
{
  "AGENT_USER_INPUT": "{\"uid\":\"test_user_001\",\"user_input\":\"确认保存\",\"confirmation_token\":\"profile_1_xxx\"}"
}
```

外层值是字符串，不能把内层 JSON 误写成第二层参数对象。

## 错误处理

- 外层不是合法 JSON：N00A 返回 `input_valid=false`，不得查询数据库。
- JSON 顶层不是对象：N00A 返回 `input_valid=false`。
- `uid` 缺失或为空：N00A 返回 `input_valid=false`，不得使用 `anonymous` 代替。
- `user_input` 缺失或为空：N00A 返回 `input_valid=false`。
- 可选 token 缺失：统一输出空字符串。
- 时间缺失：N00A 生成当前时间。
- 后续数据库、模型解析和确认错误继续沿用现有 N28、N29、N27 等业务错误分支。

## 验收标准

- N00 只有 `AGENT_USER_INPUT` 一个输入。
- 入口解析失败不会执行 N01。
- `WF-01-user-profile.md` 正文不存在 `N00/uid`、`N00/confirmation_token` 或 `N00/request_time`。
- N04 只接收解包后的 `user_input`，不接收整段包装 JSON。
- 新增记录时 `uid` 明确来自 N00A。
- 草稿、修改、确认、取消和错误 token 路径仍有明确终点。
- 两张 Mermaid 图与对应 PNG 图片匹配。
- 文档验证脚本通过。
