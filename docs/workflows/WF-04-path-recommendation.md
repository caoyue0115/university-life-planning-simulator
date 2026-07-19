# WF-04 五路径推荐：逐节点搭建指南

> 按 WF-01 的实际页面重做。WF-04 是单轮工作流：读取已确认画像和 WF-03 评估，检索知识，生成五路径推荐，校验后更新并回读。当前结束节点仍按你选的第一种方式返回 `workflow_finished`。

## 1. 结果和前置条件

- 必须已有 DB-01 `user_profiles` 中的 confirmed 画像。
- 必须已有 DB-03 `route_assessments` 中由 WF-03 写入的 `assessment_id` 和 `adventure_result_json`。
- 必须先创建知识库 `KB-01 大学五路径规则库`，并上传仓库提供的五份 Markdown 资料；完整操作见本指南第 6.1 节。
- 结果更新回同一条 DB-03 记录的 `route_recommendation_json`。
- 五路径固定：保研、考研、就业、考公、留学；只能使用“高匹配/中匹配/待验证/当前不建议投入”，不输出成功概率。

## 2. 分段连线图

### 2.1 读取两个前置结果

```mermaid
flowchart LR
    N00["N00 开始"] --> N01["N01 数据库：读取 confirmed 画像"]
    N01 --> N02{"N02 分支器：画像 SQL 成功？"}
    N02 -->|否| N31["N31 消息：画像读取失败"]
    N02 -->|是| N03["N03 代码：整理画像"]
    N03 --> N04{"N04 分支器：有 confirmed 画像？"}
    N04 -->|否| N29["N29 消息：缺少画像"]
    N04 -->|是| N05["N05 数据库：读取 WF-03 评估"]
    N05 --> N06{"N06 分支器：评估 SQL 成功？"}
    N06 -->|否| N32["N32 消息：评估读取失败"]
    N06 -->|是| N07["N07 代码：整理评估"]
    N07 --> N08{"N08 分支器：找到评估？"}
    N08 -->|否| N30["N30 消息：缺少评估"]
    N29 --> N34["N34 公共结束"]
    N30 --> N34
    N31 --> N34
    N32 --> N34
```

![WF-04 流程图 1](images/WF-04-path-recommendation-01.png)

### 2.2 检索、生成和校验

```mermaid
flowchart LR
    N08{"N08 分支器：找到评估？"} -->|是| N09["N09 文本处理：生成检索问题"]
    N09 --> N10["N10 知识库：检索五路径要求"]
    N10 --> N11["N11 代码：检查检索结果"]
    N11 --> N12{"N12 分支器：知识可用？"}
    N12 -->|否| N33["N33 消息：知识不可用"]
    N12 -->|是| N13["N13 大模型：生成五路径推荐"]
    N13 --> N14["N14 变量提取器：提取推荐"]
    N14 --> N15["N15 代码：校验五路径"]
    N15 --> N16{"N16 分支器：结果完整？"}
    N16 -->|否| N28["N28 消息：模型结果无效"]
    N28 --> N34["N34 公共结束"]
    N33 --> N34
```

![WF-04 流程图 2](images/WF-04-path-recommendation-02.png)

### 2.3 更新、回读和结束

```mermaid
flowchart LR
    N16{"N16 分支器：结果完整？"} -->|是| N17["N17 数据库：更新推荐"]
    N17 --> N18{"N18 分支器：更新成功？"}
    N18 -->|否| N26["N26 消息：推荐未保存"]
    N18 -->|是| N19["N19 数据库：回读推荐"]
    N19 --> N20{"N20 分支器：回读 SQL 成功？"}
    N20 -->|否| N27["N27 消息：回读失败"]
    N20 -->|是| N21["N21 代码：比较回读结果"]
    N21 --> N22{"N22 分支器：回读一致？"}
    N22 -->|是| N25["N25 消息：展示并确认保存成功"]
    N22 -->|否| N27
    N25 --> N34["N34 公共结束"]
    N26 --> N34
    N27 --> N34
```

![WF-04 流程图 3](images/WF-04-path-recommendation-03.png)

N25～N33 所有消息连接 N34 结束。

## 3. N00 开始

| 变量名 | 类型 | 必填 | 调试值 |
|---|---|---:|---|
| `AGENT_USER_INPUT` | String | 是 | `根据场景测试给我五路径建议` |
| `uid` | String | 是 | `test_user_001` |
| `assessment_id` | String | 是 | WF-03 N23 生成并写入的 ID |
| `request_time` | String | 是 | `2026-07-19 14:00:00` |

## 4. N01～N04：读取并整理 confirmed 画像

N01 选“自定义SQL”、数据库 `university`；输入 `uid=N00/uid`：

```sql
SELECT id, uid, profile_json, pending_status, record_version, updated_at
FROM user_profiles
WHERE uid='{{uid}}' AND pending_status='confirmed'
ORDER BY updated_at DESC, create_time DESC
LIMIT 1;
```

N02：`N01/isSuccess == true`；是 → N03，否 → N31。

N03 输入 `outputList=N01/outputList`：

```python
def main(outputList):
    rows = outputList if isinstance(outputList, list) else []
    row = rows[0] if len(rows) > 0 and isinstance(rows[0], dict) else {}
    profile_text = row.get("profile_json", "")
    return {
        "has_profile": len(row) > 0 and isinstance(profile_text, str) and len(profile_text.strip()) > 2,
        "profile_json": profile_text if isinstance(profile_text, str) else "{}",
    }
```

输出 `has_profile:Boolean`、`profile_json:String`。N04：`N03/has_profile == true`；是 → N05，否 → N29。

## 5. N05～N08：读取并整理 WF-03 评估

N05 自定义 SQL，输入 `uid=N00/uid`、`assessment_id=N00/assessment_id`：

```sql
SELECT id, uid, assessment_id, adventure_result_json,
       route_recommendation_json, assessment_version, updated_at
FROM route_assessments
WHERE uid='{{uid}}' AND assessment_id='{{assessment_id}}'
ORDER BY assessment_version DESC, updated_at DESC
LIMIT 1;
```

N06：`N05/isSuccess == true`；是 → N07，否 → N32。

N07 输入 `outputList=N05/outputList`：

```python
def main(outputList):
    rows = outputList if isinstance(outputList, list) else []
    row = rows[0] if len(rows) > 0 and isinstance(rows[0], dict) else {}
    result_text = row.get("adventure_result_json", "")
    try:
        version_value = int(row.get("assessment_version", 0))
    except:
        version_value = 0
    return {
        "has_assessment": len(row) > 0 and isinstance(result_text, str) and len(result_text.strip()) > 2,
        "record_id": int(row.get("id", 0)) if str(row.get("id", "0")).isdigit() else 0,
        "adventure_result_json": result_text if isinstance(result_text, str) else "{}",
        "next_assessment_version": version_value + 1,
    }
```

输出 `has_assessment:Boolean`、`record_id:Integer`、`adventure_result_json:String`、`next_assessment_version:Integer`。N08：`N07/has_assessment == true`；是 → N09，否 → N30。

## 6. N09 文本处理和 N10 知识库

### 6.1 先创建 WF-04 使用的知识库

N10 需要的知识库不是平台预装内容，必须由你在搭建 WF-04 前创建。正式名称固定为：

```text
KB-01 大学五路径规则库
```

仓库已经准备好五份可直接上传的资料：

1. [01-保研路径.md](../knowledge-base/KB-01-five-paths/01-保研路径.md)
2. [02-考研路径.md](../knowledge-base/KB-01-five-paths/02-考研路径.md)
3. [03-就业路径.md](../knowledge-base/KB-01-five-paths/03-就业路径.md)
4. [04-考公路径.md](../knowledge-base/KB-01-five-paths/04-考公路径.md)
5. [05-留学路径.md](../knowledge-base/KB-01-five-paths/05-留学路径.md)

> 这五份是知识内容文件。目录中的 [README.md](../knowledge-base/KB-01-five-paths/README.md) 是操作和维护说明，不要上传到知识库。

#### 第一步：把五份文件下载到本地

如果你正在 GitHub 页面查看某一份文件：

1. 点击上面的文件名打开文件。
2. 点击页面右上方 `Raw` 或下载按钮。
3. 保存时保持原文件名和 `.md` 后缀。
4. 对五份文件分别操作，确认本地文件夹内正好有五份 `.md` 文件。

如果你已经在电脑上克隆本仓库，文件位于：

```text
docs/knowledge-base/KB-01-five-paths/
```

#### 第二步：在讯飞平台新建知识库

1. 暂时离开 WF-04 编辑画布，进入平台导航栏的“知识库”。
2. 点击“新建知识库”。如果你已经打开 N10，也可以先在 N10 的“知识库”区域点击“+ 添加知识库”，再从选择页面进入新建入口。
3. 知识库名称填写 `KB-01 大学五路径规则库`。
4. 知识库简介填写：

```text
用于大学人生规划模拟器检索保研、考研、就业、考公和留学五条路径的要求、时间节点、准备材料、风险与官方核验渠道。
```

5. 上传上述五份 `.md` 文件。
6. 分段方式选择“智能分段”，不添加自定义分段规则。
7. 点击“保存并处理”，等待五份文件全部显示处理完成。

#### 第三步：先做知识库命中测试

在知识库的“命中测试”中依次测试：

```text
大二学生准备保研需要核验哪些校级规则？
考研报名和初试时间应去哪里核验？
计算机专业学生准备就业需要积累哪些证据？
考公职位的专业、学历和应届身份如何核验？
申请海外硕士通常要准备哪些材料，最终以什么为准？
```

五次测试应分别命中对应路径文件。返回片段中应能看到路径名称、适用范围、风险和官方核验渠道。如果某条没有命中，先确认该文件已经处理完成，再检查上传的是否为仓库原始 `.md` 文件。

#### 第四步：把知识库关联到 N10

1. 返回 WF-04 编辑画布。
2. 打开 `N10 知识库：检索五路径要求`。
3. 在“知识库”区域点击“+ 添加知识库”。
4. 选择 `KB-01 大学五路径规则库`，不要临时选择其他知识库替代。
5. 调用逻辑选择“强制调用”。
6. 点击“参数设置”，填写 Top K=`3`、Score 阈值=`0.20` 并保存。

### 6.2 配置 N09 文本处理

N09 拖“文本处理节点”，处理方式选“字符串拼接”。输入：`profile_json=N03/profile_json`、`adventure_result_json=N07/adventure_result_json`。规则：

```text
请检索与以下学生画像和场景测试相关的保研、考研、就业、考公、留学五条路径要求、时间节点、典型材料、风险和官方核验渠道。
画像：{{profile_json}}
测试：{{adventure_result_json}}
```

固定输出 `output:String`。

### 6.3 配置 N10 知识库节点

N10 的页面逐项填写：

| 页面区域 | 配置 |
|---|---|
| 输入 `query` | `引用｜N09/output` |
| 知识库 | `KB-01 大学五路径规则库` |
| 调用逻辑 | `强制调用` |
| 参数设置 Top K | `3` |
| 参数设置 Score 阈值 | `0.20` |
| 输出 | 平台固定 `results:Array<Object>`，不需要手动新增 |

这里的知识库只保存所有用户共享的路径规则资料；用户画像和测试结果仍保存在数据库中，两者不要混用。

## 7. N11/N12：检查知识结果

N11 输入 `results=N10/results`：

```python
def main(results):
    values = results if isinstance(results, list) else []
    return {
        "knowledge_available": len(values) > 0,
        "knowledge_hits": values,
        "knowledge_error": "" if len(values) > 0 else "没有检索到可引用的五路径资料",
    }
```

输出 `knowledge_available:Boolean`、`knowledge_hits:Array<Object>`、`knowledge_error:String`。N12：`knowledge_available == true`；是 → N13，否 → N33。

## 8. N13 大模型：生成五路径推荐

模型 `Spark4.0 Ultra`，关闭对话历史。输入：`profile_json=N03/profile_json`、`adventure_result_json=N07/adventure_result_json`、`knowledge_hits=N11/knowledge_hits`。

系统提示词：

```text
你是可解释的大学路径规划教练。必须逐一评估保研、考研、就业、考公、留学。只能使用：高匹配、中匹配、待验证、当前不建议投入。不得给成功概率，不得虚构经历。
每条路径必须有 name、level、requirements、gaps、priorities、evidence、limitations、fallback、source_notes。政策性要求必须来自知识结果并保留来源/更新时间；无法确认时写“请以学校或主管部门官方渠道为准”。最后给一个 primary_route、至少一个 alternative_routes，并列出 assumptions_to_validate。
为适配平台变量提取器，顶层必须额外输出 route_names 和 route_levels 两个字符串数组；两者顺序必须与 routes 完全一致。模型还要根据自身输出如实填写 structure_complete 和 source_notes_complete，不能为了通过校验固定写 true。
只输出以下结构的合法 JSON：
{
  "routes": [],
  "route_names": ["保研", "考研", "就业", "考公", "留学"],
  "route_levels": [],
  "primary_route": "",
  "alternative_routes": [],
  "structure_complete": false,
  "source_notes_complete": false,
  "assumptions_to_validate": [],
  "reply": ""
}
```

用户提示词：

```text
已确认画像：{{profile_json}}
场景测试结果：{{adventure_result_json}}
知识检索结果：{{knowledge_hits}}
请按系统规则生成五路径推荐。
```

输出 `output:String`。

## 9. N14 变量提取器和 N15 代码校验

N14 输入 `input=N13/output`，输出：

| 变量名 | 类型 | 描述 |
|---|---|---|
| `route_recommendation_json` | String | 完整推荐对象 JSON 字符串，供数据库保存 |
| `route_names` | Array<String> | 按 routes 顺序提取五个路径名称 |
| `route_levels` | Array<String> | 按 routes 顺序提取五个匹配等级 |
| `primary_route` | String | 主路径名称 |
| `alternative_routes` | Array<String> | 备选路径名称数组 |
| `structure_complete` | Boolean | 每条路径是否都包含规定字段；按实际内容提取 |
| `source_notes_complete` | Boolean | 五条路径是否都有来源或待核验说明；按实际内容提取 |
| `reply` | String | 面向用户的简短总结 |

> 当前页面只提供基础类型数组，不提供 `Array<Object>`。不要添加 `routes:Array<Object>`；完整对象数组只保留在 `route_recommendation_json:String` 中。

N15 输入上述八项：

```python
def main(route_recommendation_json, route_names, route_levels, primary_route, alternative_routes, structure_complete, source_notes_complete, reply):
    required_names = ["保研", "考研", "就业", "考公", "留学"]
    allowed_levels = ["高匹配", "中匹配", "待验证", "当前不建议投入"]
    names = route_names if isinstance(route_names, list) else []
    levels = route_levels if isinstance(route_levels, list) else []
    alternatives = alternative_routes if isinstance(alternative_routes, list) else []
    errors = []

    for name in required_names:
        if name not in names:
            errors.append("缺少路径:" + name)
    if len(names) != 5:
        errors.append("路径数量不是5")
    if len(levels) != 5:
        errors.append("路径等级数量不是5")
    for level in levels:
        if str(level) not in allowed_levels:
            errors.append("无效等级:" + str(level))
    if str(primary_route) not in required_names:
        errors.append("primary_route 无效")
    if len(alternatives) < 1:
        errors.append("缺少备选路径")
    if structure_complete is not True:
        errors.append("路径字段不完整")
    if source_notes_complete is not True:
        errors.append("来源或核验说明不完整")
    text_value = str(route_recommendation_json).strip()
    if not text_value.startswith("{") or not text_value.endswith("}"):
        errors.append("完整 JSON 字符串无效")
    return {
        "valid": len(errors) == 0,
        "error": ";".join(errors),
        "recommendation_json": text_value if len(errors) == 0 else "",
        "reply": str(reply),
    }
```

输出 `valid:Boolean`、`error:String`、`recommendation_json:String`、`reply:String`。N16：`N15/valid == true`；是 → N17，否 → N28。

## 10. N17/N18：更新推荐

N17 选“表单处理数据”→ `university / route_assessments`→“更新数据”。

“设置数据范围”添加两个 AND 条件：

| 表字段 | 条件 | 比较类型 | 比较值 |
|---|---|---|---|
| `uid` | 等于 | 引用 | N00/uid |
| `assessment_id` | 等于 | 引用 | N00/assessment_id |

“设置更新数据”：

| 字段 | 值 |
|---|---|
| `route_recommendation_json` | N15/recommendation_json |
| `knowledge_updated_at` | N00/request_time |
| `assessment_version` | N07/next_assessment_version |
| `updated_at` | N00/request_time |

N18：`N17/isSuccess == true`；是 → N19，否 → N26。

## 11. N19～N22：回读核对

N19 自定义 SQL，输入 uid、assessment_id：

```sql
SELECT route_recommendation_json, assessment_version, updated_at
FROM route_assessments
WHERE uid='{{uid}}' AND assessment_id='{{assessment_id}}'
ORDER BY assessment_version DESC, updated_at DESC
LIMIT 1;
```

N20：`N19/isSuccess == true`；是 → N21，否 → N27。

N21 输入 `expected=N15/recommendation_json`、`outputList=N19/outputList`：

```python
def main(expected, outputList):
    rows = outputList if isinstance(outputList, list) else []
    row = rows[0] if len(rows) > 0 and isinstance(rows[0], dict) else {}
    stored = row.get("route_recommendation_json", "")
    same = str(stored).strip() == str(expected).strip() and len(str(stored).strip()) > 2
    return {"readback_matches": same, "stored_json": str(stored)}
```

输出 `readback_matches:Boolean`、`stored_json:String`。N22：`readback_matches == true`；是 → N25，否 → N27。

## 12. 消息节点 N25～N33

每个消息关闭流式输出并连接 N34。

| 节点 | 输入 | 回答内容 |
|---|---|---|
| N25 保存成功 | `reply=N15/reply`、`result=N21/stored_json` | `{{reply}}\n\n完整五路径推荐：\n{{result}}` |
| N26 更新失败 | `message=N17/message` | `推荐草稿已生成，但没有保存。错误：{{message}}` |
| N27 回读失败 | `message=N19/message` | `数据库更新后无法确认回读一致，因此不能声称已经保存。错误：{{message}}` |
| N28 模型无效 | `error=N15/error` | `推荐结果字段不完整，本轮未保存。缺失或错误：{{error}}` |
| N29 缺少画像 | 无 | `没有找到已确认画像。请先完成并确认 WF-01。` |
| N30 缺少评估 | 无 | `没有找到对应的 WF-03 场景测试结果。请先完成 WF-03，或检查 assessment_id。` |
| N31 画像读取失败 | `message=N01/message` | `画像数据库读取失败，本轮未生成推荐。错误：{{message}}` |
| N32 评估读取失败 | `message=N05/message` | `评估数据库读取失败，本轮未生成推荐。错误：{{message}}` |
| N33 知识不可用 | `error=N11/knowledge_error` | `当前没有检索到可核验的五路径资料，因此本轮不生成政策性推荐。{{error}}` |

## 13. N34 结束

- 回答模式：返回设定格式配置的回答。
- 输出：`output｜输入｜workflow_finished`。
- 回答内容：`本轮处理已结束，请以上方消息节点的提示为准。`
- 思考内容留空，流式输出关闭。

## 14. 调试指南

1. **正常**：使用真实存在的 uid 和 assessment_id。应走到 N25；DB-03 对应记录版本增加，回读文本一致。
2. **缺画像**：换一个没有 confirmed 画像的 uid。应到 N29，不调用知识库和模型。
3. **错误 assessment_id**：应到 N30，不更新数据库。
4. **知识库空**：临时移除 N10 知识库。应到 N33，不让模型编造来源。
5. **模型漏路径**：在 N13 测试输出中删掉“考公”。N15 valid=false，到 N28。
6. **更新失败**：临时清空 N17 的更新范围。应到 N26，测试后恢复。
7. **回读不一致**：临时让 N21 expected 引用错误变量。应到 N27，不能出现“保存成功”。

## 15. 验收清单

- [ ] 两次数据库读取都先检查 isSuccess，再由代码整理 outputList。
- [ ] 五条路径齐全，使用四级制，无成功概率。
- [ ] 知识库无结果时停止，不编造政策来源。
- [ ] 更新后回读，只有一致时 N25 才说已保存。
- [ ] 所有代码无 import、返回键与输出声明一致。
- [ ] 所有失败分支连接消息和 N34，没有悬空。
