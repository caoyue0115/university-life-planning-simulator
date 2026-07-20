# 大学人生规划模拟器

完全基于讯飞星辰 Agent 平台搭建、最终发布到讯飞星火/Desk 的游戏化大学规划 Agent。运行时不依赖外部 API。

最终架构是一张用户入口工作流加九张内部 MCP 业务工作流：

```text
用户自然语言
→ MAIN-00（唯一公开入口，Agent 智能决策）
→ 按需调用 WF-01～WF-09（同账号内部 MCP Server）
→ MAIN-00 汇总后回复用户
```

MAIN 不设置“每轮最多调用一张子工作流”的业务限制；它可以在同一轮连续调用多个内部工具。仍需遵守讯飞平台最多 30 个工具、最多 100 轮推理以及运行超时等硬限制。业务子工作流不能继续调用其他工作流或 Agent。

## 文档入口

- [产品需求文档](docs/PRD.md)
- [MAIN-00 总控工作流逐节点指南](docs/workflows/MAIN-00-agent-orchestrator.md)
- [讯飞星辰工作流搭建总指南](docs/workflows/README.md)
- [工作流共享协议](docs/workflows/SHARED-CONTRACTS.md)
- [平台 UI 配置契约](docs/workflows/PLATFORM-UI-CONTRACT.md)
- [数据库从零建表与导入教程](docs/database/README.md)
- [11 张数据库字段字典](docs/database/DATABASE-SCHEMA.md)
- [可复制 SQL 示例](docs/database/SQL-EXAMPLES.md)
- [WF 数据库节点映射](docs/database/WF-DATABASE-MATRIX.md)
- [11 份字段导入模板](docs/database/import-templates/)

## 九张内部业务工作流

- [WF-01 用户建档与画像确认](docs/workflows/WF-01-user-profile.md)
- [WF-02 虚拟大学试玩](docs/workflows/WF-02-virtual-university.md)
- [WF-03 大学生存大冒险](docs/workflows/WF-03-survival-adventure.md)
- [WF-04 五路径推荐](docs/workflows/WF-04-path-recommendation.md)
- [WF-05 方向比较与主规划](docs/workflows/WF-05-direction-and-main-plan.md)
- [WF-06 学期任务与行动](docs/workflows/WF-06-semester-actions.md)
- [WF-07 成长复盘与会话收束](docs/workflows/WF-07-review-and-recap.md)
- [WF-08 履历证据](docs/workflows/WF-08-resume-evidence.md)
- [WF-09 决策分析与七天试错](docs/workflows/WF-09-decision-trial.md)

WF-02、WF-03、WF-04 合称 WFB 探索阶段：WF-02 和 WF-03 可任选其一或都体验，WF-04 汇总已有证据并标记缺口。旧版独立的主规划、微习惯和会话复盘能力已经分别合并到 WF-05、WF-06、WF-07。

## 会话与数据边界

- 用户只向 MAIN 输入自然语言，不输入 JSON、uid、时间、业务 ID 或确认 token。
- MAIN 首轮生成不可见的 `user_key` 并存入同一对话的变量存储器。
- 退出后重新打开原对话，可以继续使用同一个规划档案；新建对话会创建新档案。
- 平台没有公开承诺对话变量永久保存，也没有向当前页面暴露可供 SQL 使用的终端账号 ID，因此本项目不宣称跨新对话自动找回或永久账号级记忆。
- 数据表自动字段 `uid` 只保留为平台系统字段；业务查询和写入范围统一使用显式 `user_key`。

## 仓库校验

```powershell
python scripts/render_workflow_diagrams.py
python scripts/validate_workflow_guides.py
python scripts/validate_database_templates_exact.py
python scripts/validate_agent_architecture.py
```

这些检查覆盖最终工作流数量、单参数入口、变量提取器单输入、业务 `user_key`、Python 代码块、分支出口、流程图、MCP 结果以及 Excel 模板结构。
