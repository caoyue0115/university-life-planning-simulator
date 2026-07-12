# 讯飞星辰数据库：从零开始建表与导入教程

这份教程假设你第一次使用讯飞星辰，不要求你会 SQL。请先完成本文件，再打开 WF-01～WF-12 的数据库配置章节。

仓库中的导入文件采用“原始模板另存并填入数据行”的方式生成，除 `Sheet1` 数据行外，XLSX 内部结构与讯飞下载模板保持一致。

## 1. 你最终要创建什么

你需要在讯飞星辰的“数据库”区域创建 11 张数据表。每张表创建后都会自动带有：

```text
id           Integer   平台记录主键
uid          String    平台用户唯一标识
create_time  Time      创建时间
```

这三个字段删不掉是正常的，不要修改，也不要在 Excel 中再次添加。

## 2. 从哪里进入数据库

1. 离开当前工作流画布，返回讯飞星辰项目或 Agent 的资源管理页面。
2. 在项目导航中找到“数据库”。它不是工作流画布左侧的“数据库节点”，而是用于新建数据表的数据库管理页面。
3. 点击“新建数据表”或页面中同义的新增按钮；不同版本按钮名称以当前界面为准。
4. 进入你截图所示的页面后，会看到：
   - 数据表名称；
   - 数据表简介；
   - 导入字段；
   - 添加字段；
   - 默认的 `id`、`uid`、`create_time`。

## 3. 创建第一张表：`user_profiles`

### 3.1 填写表信息

在“数据表名称”填写：

```text
user_profiles
```

在“数据表简介”填写：

```text
保存正式用户画像、待确认画像草稿及确认令牌。
```

不要把表名写成 `old_profile_json`。`old_profile_json` 是工作流中的变量，不是数据库表名。

### 3.2 保留默认字段

看到下面三行时不需要操作：

```text
id
uid
create_time
```

它们由平台维护：

- 查询当前用户时使用 `uid`；
- 更新某一条记录时可以使用 `id`；
- 查看记录创建时间时使用 `create_time`。

### 3.3 导入业务字段

1. 在字段列表上方点击“导入字段”。
2. 选择仓库中的文件：[DB-01-user-profiles.xlsx](import-templates/DB-01-user-profiles.xlsx)。
3. 等待平台读取文件。
4. 在导入预览中确认出现：
   - `profile_json`
   - `pending_profile_json`
   - `confirmation_token`
   - `pending_status`
   - `record_version`
   - `updated_at`
5. 确认没有再次出现 `id`、`uid`、`create_time`。
6. 检查“是否必填”列只能显示文字 `是` 或 `否`。讯飞导入模板不接受 `1/0` 或布尔值；出现其他值会导致整份文件导入失败。
7. 点击确认导入。
8. 回到建表页面，检查字段类型：JSON 字段为 `String`，版本为 `Integer`，更新时间为 `Time`。
9. 点击页面底部或右上角的保存/创建按钮。

## 4. 依次创建其余 10 张表

每次都重新点击“新建数据表”，不要在上一张表中继续导入。

| 次序 | 数据表名称 | 数据表简介 | 上传文件 |
|---|---|---|---|
| 1 | `user_profiles` | 保存正式用户画像、待确认画像草稿及确认令牌。 | [DB-01](import-templates/DB-01-user-profiles.xlsx) |
| 2 | `simulation_states` | 保存虚拟大学和生存大冒险的跨轮状态。 | [DB-02](import-templates/DB-02-simulation-states.xlsx) |
| 3 | `route_assessments` | 保存生存测试结果和五路径推荐。 | [DB-03](import-templates/DB-03-route-assessments.xlsx) |
| 4 | `parallel_versions` | 保存平行人生版本及统一维度比较结果。 | [DB-04](import-templates/DB-04-parallel-versions.xlsx) |
| 5 | `main_plans` | 保存主规划、历史规划和待确认规划变更。 | [DB-05](import-templates/DB-05-main-plans.xlsx) |
| 6 | `semester_tasks` | 保存学期、月度、每周任务和执行证据。 | [DB-06](import-templates/DB-06-semester-tasks.xlsx) |
| 7 | `growth_reviews` | 保存成长证据、动态修正建议和待确认动作。 | [DB-07](import-templates/DB-07-growth-reviews.xlsx) |
| 8 | `resume_entries` | 保存履历事实、待确认草稿和正式履历条目。 | [DB-08](import-templates/DB-08-resume-entries.xlsx) |
| 9 | `decision_trials` | 保存决策分析、七天试错计划和每日记录。 | [DB-09](import-templates/DB-09-decision-trials.xlsx) |
| 10 | `habit_logs` | 保存习惯、记账、入门健身和安全提示记录。 | [DB-10](import-templates/DB-10-habit-logs.xlsx) |
| 11 | `session_recaps` | 保存会话新增事实、状态变化、未决问题和下次入口。 | [DB-11](import-templates/DB-11-session-recaps.xlsx) |

完整字段含义见 [DATABASE-SCHEMA.md](DATABASE-SCHEMA.md)。

## 5. 在工作流中添加数据库节点

建表完成后回到工作流画布：

1. 在左侧“知识&数据”区域找到“数据库”。
2. 把“数据库”拖到画布指定位置。
3. 用前一个节点右侧连接点连接数据库节点左侧连接点。
4. 点击数据库节点；右侧出现配置面板。
5. 点击节点标题旁的编辑图标，把“数据库_1”改成教程要求的名称，例如“读取正式画像及待确认草稿”。

## 6. 什么时候选“表单处理数据”

第一次搭建建议优先使用“表单处理数据”：

1. 点击右侧“表单处理数据”。
2. 选择数据表，例如 `user_profiles`。
3. 操作选择“查询”。
4. 添加条件 `uid = 当前 uid`。
5. 如果可以设置排序，选择 `updated_at` 降序。
6. 如果可以设置数量，填写 `1`。

平台表单模式无法表达排序、复杂条件或回读版本时，再使用“自定义SQL”。

## 7. 自定义 SQL 的输入参数怎么添加

以 WF-01 第一个查询节点为例：

1. 右侧“模式”选择“自定义SQL”。
2. “选择数据库”选择 `user_profiles`。
3. 在“输入”区域，如果有一个空的 `input` 行：
   - 可以把参数名改为 `uid`；
   - 类型选择“引用”时，从上游开始节点或主 Agent 输入中选择 `uid`；
   - 独立调试暂时取不到真实 uid 时，类型改成固定字符串并填写 `test_user_001`。
4. 不要把整段 `AGENT_USER_INPUT` 当作 uid。
5. 在 SQL 区粘贴对应语句。

查询最新画像的 SQL：

```sql
SELECT
  id,
  uid,
  profile_json,
  pending_profile_json,
  confirmation_token,
  pending_status,
  record_version,
  updated_at
FROM user_profiles
WHERE uid = '{{uid}}'
ORDER BY updated_at DESC
LIMIT 1;
```

注意字符串参数必须带单引号：

```sql
uid = '{{uid}}'
```

## 8. 数据库节点三个输出怎么看

数据库节点固定输出通常包括：

| 输出 | 含义 | 下游怎么用 |
|---|---|---|
| `isSuccess` | SQL 或表单操作是否执行成功 | 连接“决策”判断成功/失败 |
| `message` | 失败原因或平台说明 | 失败消息中展示，不把技术细节伪装成成功 |
| `outputList` | 查询返回的记录数组 | 大模型、变量提取器或代码节点读取 |

必须区分：

```text
isSuccess=false
```

表示数据库操作失败。

```text
isSuccess=true 且 outputList=[]
```

表示查询执行成功，只是当前用户还没有记录。WF-01 中这代表新用户，应使用空画像继续，而不是报错。

## 9. 在“决策”节点中判断查询结果

数据库节点后拖入“决策”：

1. 连接数据库节点到决策节点。
2. 将决策节点重命名为“数据库读取成功”。
3. 第一层判断引用数据库节点的 `isSuccess`：
   - `true`：继续处理 `outputList`；
   - `false`：连接“消息”，提示读取失败。
4. 需要区分新用户时再增加一个决策或代码判断 `outputList` 是否为空。

如果平台决策节点不方便判断数组长度，可把 `outputList` 传入“代码”节点，输出：

```javascript
const rows = Array.isArray(outputList) ? outputList : [];
return {
  has_record: rows.length > 0,
  first_record: rows.length > 0 ? rows[0] : null
};
```

## 10. 调试第一张表

### 10.1 新用户空查询

1. 回到 WF-01 画布。
2. 点击右上角“调试”。
3. 测试 uid 使用 `test_user_001`。
4. 用户输入填写：`我是大一学生，计算机专业，想先建立画像。`
5. 执行后点击数据库节点的执行详情。
6. 应看到：
   - `isSuccess=true`；
   - `outputList=[]`，或者没有记录；
   - 流程继续进入新用户画像生成。

### 10.2 数据库失败

临时把 SQL 表名改成不存在的名称，再调试一次：

- 预期 `isSuccess=false`；
- `message` 中出现 SQL 或表不存在说明；
- 流程进入失败消息，不得生成“读取成功”。

测试后立即把表名恢复为 `user_profiles`。

### 10.3 有记录查询

完成一次待确认画像写入后，再用同一个 `test_user_001` 调试：

- `outputList` 应有一条记录；
- 第一条记录包含 `pending_profile_json` 和 `confirmation_token`；
- 下一轮确认必须读取这条草稿，不能重新生成。

## 11. 测试数据清理

完成调试后进入数据库管理页面：

1. 打开对应数据表。
2. 筛选 `uid=test_user_001`。
3. 确认只选中测试记录。
4. 删除测试记录前再次检查表名和 uid，避免删除真实用户数据。

如果平台不允许删除，可以把测试记录的状态改为 `archived`，并确保正式查询排除该状态。
