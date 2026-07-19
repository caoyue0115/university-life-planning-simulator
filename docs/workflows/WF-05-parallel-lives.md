# WF-05 平行人生模拟：逐节点搭建指南

> WF-05 只比较 2～3 条路径，不生成或覆盖主规划。它可以把比较草稿保存到 `parallel_versions`，但正式主规划必须交给 WF-06 再确认。结束节点当前按第一种方式返回 `workflow_finished`。

## 1. 最终结果

- 输入：已确认画像、WF-04 五路径推荐、用户想比较的 2～3 条路径。
- 输出：完全相同起点下的 2～3 个版本、统一维度比较、取舍和待回答问题。
- 保存：DB-04 `parallel_versions`，仅保存模拟比较。
- 禁止：写 `main_plans`，把模拟结果说成预测，替用户选定最终版本。

## 2. 数据表

在 `university` 创建 `parallel_versions`，上传 [DB-04](../database/import-templates/DB-04-parallel-versions.xlsx)。保留默认 `id/uid/create_time`。业务必填字段：`comparison_id`、`versions_json`、`comparison_json`、`shared_baseline_json`、`comparison_version`、`updated_at`。

## 3. 清晰连线图

```mermaid
flowchart LR
    N00["N00 开始"] --> N01["N01 变量提取器：提取候选路径"]
    N01 --> N02["N02 代码：校验输入和路径"]
    N02 --> N03{"N03 分支器：输入有效？"}
    N03 -->|否| N04["N04 消息：提示补充"]
    N03 -->|是| N05["N05 大模型：生成平行版本"]
    N05 --> N06["N06 变量提取器：提取比较结果"]
    N06 --> N07["N07 代码：校验并准备数据库行"]
    N07 --> N08{"N08 分支器：结果完整？"}
    N08 -->|否| N09["N09 消息：结果无效"]
    N08 -->|是| N10["N10 数据库：新增比较草稿"]
    N10 --> N11{"N11 分支器：保存成功？"}
    N11 -->|是| N12["N12 消息：展示比较"]
    N11 -->|否| N13["N13 消息：比较未保存"]
    N04 --> N14["N14 公共结束"]
    N09 --> N14
    N12 --> N14
    N13 --> N14
```

![WF-05 流程图 1](images/WF-05-parallel-lives-01.png)

N04、N09、N12、N13 全部连接 N14 结束。

## 4. N00 开始

| 变量名 | 类型 | 必填 | 调试值 |
|---|---|---:|---|
| `AGENT_USER_INPUT` | String | 是 | `比较保研、考研和就业` |
| `uid` | String | 是 | `test_user_001` |
| `profile_json` | String | 是 | WF-01 已确认画像 |
| `route_recommendation_json` | String | 是 | WF-04 完整推荐 |
| `selected_routes` | String | 否 | `保研,考研,就业` |
| `request_time` | String | 是 | `2026-07-19 15:00:00` |

这里把 `selected_routes` 建成 String，因为开始节点截图没有稳定的 Array 输入；N01 会从文本提取数组。

## 5. N01 变量提取器：提取候选路径

模型 `Spark4.0 Ultra`。输入：

- `user_input｜引用｜N00/AGENT_USER_INPUT`
- `selected_routes｜引用｜N00/selected_routes`
- `recommendation｜引用｜N00/route_recommendation_json`

输出：

| 变量 | 类型 | 描述 |
|---|---|---|
| `routes` | Array | 从用户原话或 selected_routes 提取的路径名称数组，只允许保研、考研、就业、考公、留学 |
| `extract_reason` | String | 路径来源和无法判断的原因 |

## 6. N02 代码：校验输入和路径

输入 `profile_json=N00/profile_json`、`routes=N01/routes`、`route_recommendation_json=N00/route_recommendation_json`。

```python
def main(profile_json, routes, route_recommendation_json):
    allowed = ["保研", "考研", "就业", "考公", "留学"]
    values = routes if isinstance(routes, list) else []
    normalized = []
    for item in values:
        name = str(item).strip()
        if name in allowed and name not in normalized:
            normalized.append(name)
    profile_text = str(profile_json).strip()
    recommendation_text = str(route_recommendation_json).strip()
    valid = profile_text.startswith("{") and profile_text.endswith("}") and 2 <= len(normalized) <= 3
    return {
        "input_valid": valid,
        "validation_error": "" if valid else "需要已确认画像和 2～3 条互不重复的有效路径",
        "normalized_routes": normalized,
        "shared_baseline_json": profile_text if valid else "{}",
        "recommendation_json": recommendation_text if recommendation_text else "{}",
    }
```

输出 `input_valid:Boolean`、`validation_error:String`、`normalized_routes:Array<String>`、`shared_baseline_json:String`、`recommendation_json:String`。

## 7. N03 分支器和 N04 消息

N03 引用 `N02/input_valid`，等于固定值 `true`。是 → N05；否 → N04。

N04 输入 `error=N02/validation_error`，回答内容：

```text
还不能生成平行版本：{{error}}。
请明确选择 2～3 条不同路径，例如“比较保研、考研和就业”。
```

关闭流式输出，连接 N14。

## 8. N05 大模型：生成平行版本

模型 `Spark4.0 Ultra`，关闭对话历史。输入：`shared_baseline_json=N02/shared_baseline_json`、`normalized_routes=N02/normalized_routes`、`route_recommendation_json=N02/recommendation_json`。

系统提示词：

```text
你是大学规划情景推演师。为 routes 中每条路径生成一个平行版本，所有版本必须共用完全相同的 shared_baseline，不得补造经历，不得给成功概率。
每个版本必须包含 version_name、target_route、semester_trajectory、resume_assets、skill_tree、time_cost、economic_cost、failure_risks、reversibility、crowding_out_effect、graduation_options、limitations、official_verification。
统一比较必须覆盖：路径匹配、剩余学期轨迹、简历素材、技能深度和广度、时间、经济成本、失败风险、可逆性、挤出效应、毕业选择权。
只输出 JSON：
{"versions":[],"comparison":[],"key_tradeoffs":[],"questions_for_user":[],"reply":""}
```

用户提示词：

```text
共同起点：{{shared_baseline_json}}
候选路径：{{normalized_routes}}
已有五路径推荐：{{route_recommendation_json}}
请生成并比较全部版本，只输出规定 JSON。
```

输出格式 text，变量 `output:String`。

## 9. N06 变量提取器：提取比较结果

输入 `input=N05/output`。输出：

| 变量 | 类型 | 描述 |
|---|---|---|
| `parallel_versions_json` | String | 完整模型结果 JSON 字符串 |
| `versions` | Array | 完整 versions 数组 |
| `versions_json` | String | 仅 versions 数组序列化后的 JSON 字符串 |
| `comparison_json` | String | comparison、key_tradeoffs、questions_for_user 的 JSON 字符串 |
| `reply` | String | 面向用户的比较摘要和下一步问题 |

## 10. N07 代码：校验并准备数据库行

输入 `uid=N00/uid`、`request_time=N00/request_time`、`routes=N02/normalized_routes`、`shared_baseline_json=N02/shared_baseline_json`、N06 的全部输出。

```python
def main(uid, request_time, routes, shared_baseline_json, parallel_versions_json, versions, versions_json, comparison_json, reply):
    required = [
        "version_name", "target_route", "semester_trajectory", "resume_assets",
        "skill_tree", "time_cost", "economic_cost", "failure_risks",
        "reversibility", "crowding_out_effect", "graduation_options",
        "limitations", "official_verification"
    ]
    route_values = routes if isinstance(routes, list) else []
    version_values = versions if isinstance(versions, list) else []
    errors = []
    if len(version_values) != len(route_values):
        errors.append("版本数量与路径数量不一致")
    found_routes = []
    for index, item in enumerate(version_values):
        if not isinstance(item, dict):
            errors.append("版本不是对象:" + str(index))
            continue
        found_routes.append(str(item.get("target_route", "")))
        for key in required:
            if key not in item:
                errors.append("versions[" + str(index) + "]缺少" + key)
    for route in route_values:
        if str(route) not in found_routes:
            errors.append("缺少路径版本:" + str(route))
    full_text = str(parallel_versions_json).strip()
    if not full_text.startswith("{") or not full_text.endswith("}"):
        errors.append("完整结果不是 JSON 对象字符串")
    return {
        "result_valid": len(errors) == 0,
        "result_error": ";".join(errors),
        "comparison_id": str(uid) + "-COMPARE-" + str(request_time),
        "versions_json": str(versions_json),
        "comparison_json": str(comparison_json),
        "shared_baseline_json": str(shared_baseline_json),
        "selected_version_name": "",
        "comparison_version": 1,
        "updated_at": str(request_time),
        "display_result": full_text,
        "reply": str(reply),
    }
```

输出区声明：`result_valid:Boolean`、`result_error:String`、`comparison_version:Integer`，其余返回键均 String。不要漏掉 `display_result` 和 `reply`。

## 11. N08/N09：完整性分支

N08：`N07/result_valid == true`。是 → N10；否 → N09。

N09 输入 `error=N07/result_error`，回答：`平行版本结果字段不完整，本轮未保存。请重试。错误：{{error}}`，连接 N14。

## 12. N10 数据库：新增比较草稿

模式“表单处理数据”，数据表 `university / parallel_versions`，处理模式“新增数据”。设置：

| 表字段 | 值 |
|---|---|
| `uid` | 页面强制显示时引用 N00/uid |
| `comparison_id` | N07/comparison_id |
| `versions_json` | N07/versions_json |
| `comparison_json` | N07/comparison_json |
| `shared_baseline_json` | N07/shared_baseline_json |
| `selected_version_name` | N07/selected_version_name |
| `comparison_version` | N07/comparison_version |
| `updated_at` | N07/updated_at |

固定输出 `isSuccess/message/outputList`。

## 13. N11～N13：保存结果消息

N11：`N10/isSuccess == true`。是 → N12；否 → N13。

N12 输入 `reply=N07/reply`、`result=N07/display_result`、`comparison_id=N07/comparison_id`，回答：

```text
{{reply}}

完整比较：
{{result}}

本次比较草稿编号：{{comparison_id}}。它只是模拟版本，还没有成为主规划；选定版本后再进入 WF-06。
```

N13 输入 `result=N07/display_result`、`message=N10/message`，回答：

```text
平行版本已经生成，但比较草稿没有保存。下面仍可查看本轮结果；不要把它当作已保存记录。
{{result}}
错误：{{message}}
```

两者连接 N14。

## 14. N14 结束

- 回答模式：返回设定格式配置的回答。
- 输出：`output｜输入｜workflow_finished`。
- 回答内容：`本轮处理已结束，请以上方消息节点的提示为准。`
- 思考内容留空；流式输出关闭。

## 15. 调试指南

1. 正常：三条路径，预期 N03 是、N08 是、N11 是，DB-04 新增一行。
2. 只有一条路径：预期 N03 否到 N04，不调用模型、不写数据库。
3. 重复路径：输入“就业、就业、考研”，N02 去重后仍只有两条，可继续；若去重后不足两条则失败。
4. 模型漏字段：让测试输出删除 `reversibility`，预期 N08 否到 N09。
5. 版本起点：检查每个版本没有自行修改学校、专业、预算等共同基线。
6. 写入失败：临时清空 N10/comparison_id，预期 N13，不声称已保存。

## 16. 验收清单

- [ ] 开始节点的 selected_routes 是 String，N01 再提取 Array。
- [ ] 只接受 2～3 条去重路径，所有版本共享同一基线。
- [ ] 代码节点无 import，输出区声明全部返回键。
- [ ] DB-04 保存模拟比较，但不写 main_plans。
- [ ] 所有失败分支和成功分支都连接 N14。
