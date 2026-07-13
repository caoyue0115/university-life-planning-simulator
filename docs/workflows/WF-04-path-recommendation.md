# WF-04 五路径推荐

## 1. 目标与准备

主 Agent 在 WF-03 完成或用户要求重新评估路径时调用。输入已确认 `profile_json`、`adventure_result_json`，可选行为证据；检索包含来源和更新时间的五路径知识；输出 `data.route_recommendation_json`。推荐是可修正方案，不是预测。

## 2. 最小可运行版

```text
开始 → 知识库（检索五路径要求）→ 大模型（生成五路径推荐）→ 变量提取器（提取推荐）→ 结束
```

从左侧“知识与数据”拖“知识库”，再拖“大模型”“变量提取器”，放在开始与结束之间并依次连线。知识库查询映射 `profile_json` 中年级/专业和五路径；检索字段、TopK 等按本文件逐栏配置。无法稳定返回来源时，结果必须标记 `source_unavailable` 并提醒官方复核，不能编造引用。

## 3. 完整业务版画布与搭建

完整画布、节点数量、拖拽连线和二次校验分支统一见第 7 节。

## 4. 配置、校验与变量映射

知识检索输入由 `grade,major,route_names=[保研,考研,就业,考公,留学]` 组成，输出 `knowledge_hits`。大模型输入再加入画像、测试结果。保存键为 `route_recommendation`，但推荐更新不得覆盖画像或主规划。

代码节点仅支持 Python。输入区配置 `input｜引用｜变量提取器/route_recommendation_json`；输出区声明 `valid:Boolean`、`errors:Array<String>`、`value:Object`：

```python
import json


def main(input):
    try:
        value = json.loads(input) if isinstance(input, str) else input
    except (TypeError, ValueError, json.JSONDecodeError):
        return {"valid": False, "errors": ["JSON 无效"], "value": {}}

    names = ["保研", "考研", "就业", "考公", "留学"]
    levels = ["高匹配", "中匹配", "待验证", "当前不建议投入"]
    errors = []
    routes = value.get("routes") if isinstance(value, dict) else None
    if not isinstance(routes, list):
        errors.append("routes 必须是数组")
        routes = []
    for name in names:
        route = next((item for item in routes if item.get("name") == name), None)
        if not route:
            errors.append(f"缺少路径:{name}")
            continue
        if route.get("level") not in levels:
            errors.append(f"{name}等级无效")
        for key in ["requirements", "gaps", "priorities", "evidence", "limitations"]:
            if not isinstance(route.get(key), list):
                errors.append(f"{name}缺少{key}")
    if not value.get("primary_route"):
        errors.append("缺少主路径")
    if not isinstance(value.get("alternative_routes"), list) or not value["alternative_routes"]:
        errors.append("缺少备选路径")
    if not isinstance(value.get("assumptions_to_validate"), list):
        errors.append("缺少待验证假设")
    return {"valid": not errors, "errors": errors, "value": value}
```

## 5. 可复制的完整提示词

```text
你是可解释的大学路径规划教练。
已确认画像：{{profile_json}}
场景测试结果：{{adventure_result_json}}
行为证据：{{behavior_evidence}}
知识检索结果：{{knowledge_hits}}
对保研、考研、就业、考公、留学逐一评估。依据“偏好匹配、能力匹配、已有履历匹配、资源条件匹配、实际行为证据，减去时间缺口、经济压力、路径风险”做定性判断，只能使用 高匹配/中匹配/待验证/当前不建议投入，不给成功概率或伪精确分数。每条路径都写典型要求、当前差距、优先补齐项、证据、局限和备选方案。选一个主路径和至少一个备选，但明确最终决定权属于用户。未知信息放 assumptions_to_validate，不得补造。政策信息带来源与更新时间；缺失则标注并提示通过学校或主管部门官方渠道复核。
只输出合法 JSON：
{"routes":[{"name":"保研","level":"待验证","requirements":[],"gaps":[],"priorities":[],"evidence":[],"limitations":[],"fallback":""}],"primary_route":"","alternative_routes":[],"reasoning_summary":"","assumptions_to_validate":[],"source_notes":[],"disclaimer":"每个人的大学都是独一无二的。模拟器给的是地图，最终决定和行动由你完成。"}
注意 routes 必须恰好包含五条指定路径。
```

## 6. 调试、错误处理与验收清单

- 成功：提供完整画像和 WF-03 结果；观察知识来源、五条路径、主/备选、依据和假设齐全，校验为真。
- 缺失：移除 `adventure_result_json`，应在检索前走缺失分支，`next_action=complete_adventure`。
- 模型漏掉“考公”：首次校验失败、修复一次；再次失败返回 `invalid_json`，不得保存。
- 知识库不可用：可基于画像给“待验证”的一般建议，但 `error=knowledge_unavailable`，政策全部提示官方复核。
- [ ] 只使用四级制，无概率；五路径完整。
- [ ] 数据库写入后检查结果，失败状态为 `write_failed`。
- [ ] 输出共享包装中的 `route_recommendation_json`，供 WF-05/WF-06 使用。

## 7. 完整业务版画布、节点数量与逐边映射

完整画布包含数据库 3、分支器 4、消息 3、知识库 1、大模型 2、变量提取器 2、代码 2，另加开始和结束各 1。所有生成、修复和输出统一使用 PRD 免责声明原文。

从开始右侧横向摆读取、检索、生成、首次校验主线；将修复与二次校验放“首次校验”下方，将缺失、二次失败、写入失败消息放各自分支器下方。依节点清单逐个重命名后，从右侧连接点拖到图示下游左侧，并在四个分支器上逐边填写图中的条件。

从空画布依次拖入并重命名“读取画像、读取测试结果、检查读取与输入、缺失提示、检索五路径要求、生成五路径推荐、提取推荐、首次完整性校验、判断首次校验、修复推荐 JSON、重新提取、二次完整性校验、判断二次校验、保存推荐、检查写入、校验失败提示”，按图连线。

```mermaid
flowchart LR
 A["N00 开始｜开始"] --> B["N01 数据库｜读取画像"] --> C["N02 数据库｜读取测试结果"] --> D{"N03 分支器｜读取成功且输入齐全"}
 D -->|否| E["N04 消息｜缺失或读取失败"] --> Z["N05 结束｜结束"]
 D -->|是| F["N06 知识库｜检索五路径要求"] --> G["N07 大模型｜生成五路径推荐"] --> H["N08 变量提取器｜提取推荐"] --> I["N09 代码｜首次完整性校验"] --> J{"N10 分支器｜首次校验通过"}
 J -->|是| N["N11 数据库｜保存推荐"] --> O{"N12 分支器｜写入成功"}
 J -->|否| K["N13 大模型｜修复推荐 JSON"] --> L["N14 变量提取器｜重新提取"] --> M["N15 代码｜二次完整性校验"] --> P{"N16 分支器｜二次校验通过"}
 P -->|是| N
 P -->|否| X["N17 消息｜校验失败提示"] --> Z
 O -->|是| Z
 O -->|否| Y["N18 消息｜推荐未保存"] --> Z
```

![WF-04 路径推荐分支图](images/WF-04-path-recommendation.png)

逐边变量：A→B/C `uid`；B/C→D `profile_json,adventure_result_json,read_result`；D是→F `grade,major,五路径名`；F→G `profile_json,adventure_result_json,knowledge_hits`；G→H `model_text`；H→I `route_recommendation_json`；I→J `valid,errors,value`；J否→K `value,errors`；K→L `repaired_text`；L→M `route_recommendation_json`；M→P `valid,errors,value`；J是/P是→N `uid,value`；N→O `write_result`。

修复完整提示词：

```text
你只修复 JSON 结构，不新增事实、不改变已有等级和依据。原 JSON：{{value}}；校验错误：{{errors}}。补齐且仅补齐五条路径（保研、考研、就业、考公、留学）、合法等级、requirements/gaps/priorities/evidence/limitations 数组、primary_route、至少一个 alternative_routes、assumptions_to_validate、source_notes、disclaimer。缺少事实时填空数组或“待验证”，不得编造来源。disclaimer 必须逐字为：每个人的大学都是独一无二的。模拟器给的是“地图”，但“走路”的人是你自己。勇敢去闯，错了也没关系——毕竟，大学本身就是试错成本最低的地方呀！只输出合法 JSON。
```

生成提示词中的免责声明也必须替换为上述 PRD 原文。二次校验通过才允许保存；失败固定返回 `validation_failed`，不保存。保存成功结束：`{"workflow_id":"WF-04","version":"1.0","status":"completed","reply":"已生成并保存可解释的五路径建议，最终决定由你作出。","data":{"route_recommendation_json":{{value}}},"suggested_writes":[],"next_action":"create_parallel_versions","error":null}`。写入失败：`status=write_failed,reply=推荐已生成但未保存成功,next_action=retry_save,error={"code":"write_failed","message":"推荐未保存成功","retryable":true}`；读取失败用 `read_failed`，两次校验失败用 `validation_failed`。

## 节点逐项配置

<!-- GENERATED-NODE-LEDGER:START -->
### 画布节点连线与页面输入输出总表

本表由流程图生成，用于防止漏连。‘直接上游’决定页面引用下拉框中可选的数据来源；具体变量名以本文件后续业务映射表为准。
开始节点类型规则：`uid/session_id/AGENT_USER_INPUT` 及所有 `*_json/*_token/*_id` 均选 String；计数、天数选 Integer；真伪开关选 Boolean。表中未特别标注的输入一律选 String，JSON 作为字符串传递。

| 节点 | 类型 | 直接上游（输入来源） | 固定/声明输出 | 直接下游 |
|---|---|---|---|---|
| `A` N00 开始｜开始 | 开始 | 无（起点） | 开始节点中声明的同名变量 | B |
| `B` N01 数据库｜读取画像 | 数据库 | A | `isSuccess:Boolean`、`message:String`、`outputList:Array<Object>` | C |
| `C` N02 数据库｜读取测试结果 | 数据库 | B | `isSuccess:Boolean`、`message:String`、`outputList:Array<Object>` | D |
| `D` N03 分支器｜读取成功且输入齐全 | 分支器 | C | 不产生业务变量；按条件输出连线 | E（否）、F（是） |
| `E` N04 消息｜缺失或读取失败 | 消息 | D | 不新增业务变量；回答内容引用上游变量 | Z |
| `Z` N05 结束｜结束 | 结束 | E、X、O、Y | `output` 引用上游最终结果 | 无；必须在正文说明为何终止或转入下一张图 |
| `F` N06 知识库｜检索五路径要求 | 知识库 | D | `results:Array<Object>` | G |
| `G` N07 大模型｜生成五路径推荐 | 大模型 | F | `output:String` | H |
| `H` N08 变量提取器｜提取推荐 | 变量提取器 | G | `route_recommendation_json:String`（完整五路径推荐 JSON） | I |
| `I` N09 代码｜首次完整性校验 | 代码 | H | 与 Python `main()` 返回 dict 的键完全一致 | J |
| `J` N10 分支器｜首次校验通过 | 分支器 | I | 不产生业务变量；按条件输出连线 | N（是）、K（否） |
| `N` N11 数据库｜保存推荐 | 数据库 | J、P | `isSuccess:Boolean`、`message:String`、`outputList:Array<Object>` | O |
| `O` N12 分支器｜写入成功 | 分支器 | N | 不产生业务变量；按条件输出连线 | Z（是）、Y（否） |
| `K` N13 大模型｜修复推荐 JSON | 大模型 | J | `output:String` | L |
| `L` N14 变量提取器｜重新提取 | 变量提取器 | K | `route_recommendation_json:String`（修复后的完整推荐 JSON） | M |
| `M` N15 代码｜二次完整性校验 | 代码 | L | 与 Python `main()` 返回 dict 的键完全一致 | P |
| `P` N16 分支器｜二次校验通过 | 分支器 | M | 不产生业务变量；按条件输出连线 | N（是）、X（否） |
| `X` N17 消息｜校验失败提示 | 消息 | P | 不新增业务变量；回答内容引用上游变量 | Z |
| `Y` N18 消息｜推荐未保存 | 消息 | O | 不新增业务变量；回答内容引用上游变量 | Z |
<!-- GENERATED-NODE-LEDGER:END -->

> 本节必须与[平台 UI 配置契约](PLATFORM-UI-CONTRACT.md)一起使用。先按流程图编号拖入节点并连线，再配置节点；未连线时下游“引用”下拉框会显示暂无数据。

### 本工作流所有节点的页面填写顺序

1. **开始**：按下方开始输入表逐行“+ 添加”，变量名、类型和必填状态照表填写。
2. **自定义 SQL 数据库**：输入参数选择引用；读取结果只使用固定输出 `isSuccess:Boolean`、`message:String`、`outputList:Array<Object>`。
3. **表单新增/更新数据库**：选择 `university / 目标表`；新增在“设置新增数据”逐字段添加，更新先在“设置数据范围”配置 AND 条件，再在“设置更新数据”逐字段添加；固定输出仍为 `isSuccess/message/outputList`。
4. **大模型**：输入参数名与 `{{变量名}}` 完全一致；系统提示词放角色、规则和 JSON 结构，用户提示词只放本轮变量；输出 `output:String`。
5. **变量提取器**：输入固定为 `input｜引用｜上游大模型/output`；每个输出必须填写变量名、类型和提取描述，复杂 JSON 先用 String。
6. **代码**：仅使用 Python `def main(...): return {...}`；输入名与形参一致，输出区声明每个返回键及类型。
7. **分支器**：左侧选上游变量，条件选“等于”等操作；与字面量比较时比较类型选常量/固定值；每条分支和默认分支都必须连接。
8. **消息**：输入区引用需要展示的变量，在“回答内容”用 `{{变量名}}`；流式输出关闭；消息后连接共享结束。
9. **结束**：回答模式选“返回设定格式配置的回答”，输出设置 `output｜引用｜上游最终结果`。所有成功、失败、待补充消息都进入同一个结束节点。

本节的通用点击位置、建表入口、导入按钮和数据库节点输出解释见[数据库从零教程](../database/README.md)；请先完成该教程，再按本节配置当前 WF。

需要 `user_profiles` 和 `route_assessments`，上传 [DB-01](../database/import-templates/DB-01-user-profiles.xlsx) 与 [DB-03](../database/import-templates/DB-03-route-assessments.xlsx)。

| 开始输入 | 来源 | 调试值 |
|---|---|---|
| `AGENT_USER_INPUT` | 开始节点 | `根据测试结果给我路径建议` |
| `uid` | 主 Agent | `test_user_001` |
| `assessment_id` | WF-03 结束输出 | DB-03 中测试记录的 ID |

读取画像 SQL：

```sql
SELECT profile_json FROM user_profiles
WHERE uid='{{uid}}' AND pending_status='confirmed'
ORDER BY updated_at DESC LIMIT 1;
```

读取测试结果 SQL：

```sql
SELECT * FROM route_assessments
WHERE uid='{{uid}}' AND assessment_id='{{assessment_id}}'
ORDER BY assessment_version DESC LIMIT 1;
```

任一 `isSuccess=false` 都进入读取失败；成功空数组进入“缺少前置数据”。推荐生成并校验后，在 `route_assessments` 更新当前 `id` 的 `route_recommendation_json,knowledge_updated_at,updated_at`，再按 `uid + assessment_id` 回读。

节点映射：两个查询的 `outputList` → 推荐大模型；大模型 `output` → 变量提取器/代码校验；校验后的 JSON → 数据库；数据库 `isSuccess` → 写入分支器；最终 `result_json` → 结束 `output`。

调试正常记录、错误 assessment_id 空查询、临时错误表名三种情况。只有回读 JSON 一致才能输出 `completed/write_succeeded`。
