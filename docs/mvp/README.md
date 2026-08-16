# 大模型优先最小可运行版

本目录是一套与正式详细版并行存在的验证方案。正式版仍在 [`docs/workflows`](../workflows/README.md)，使用数据库、知识库、确认 token 和逐节点校验；本目录先验证“12 个业务模块能否在一个 MAIN 画布中形成自然语言闭环”。

## 文件导航

| 文件 | 用途 |
|---|---|
| [MVP 设计](MVP-DESIGN.md) | 范围、统一状态、路由规则、风险和成功标准 |
| [统一状态协议](SHARED-STATE.md) | 初始 `state_json`、模块状态和确认规则 |
| [数据库状态改造方案](STATE-DATABASE-REFACTOR.md) | 用数据库替代完整 `state_json` 搬运的目标架构、节点配置和迁移验收 |
| [12 模块输入输出总表](MODULE-IO-MATRIX.md) | 每个 WF 的输入、状态字段和确认后去向 |
| [MAIN 搭建教程](MAIN-BUILD-GUIDE.md) | 按平台页面逐节点配置总画布 |
| [调试教程](TEST-GUIDE.md) | 先做连续性门禁，再跑 12 模块 |
| [WF-01 提示词](prompts/WF-01-user-profile.md) | 用户画像 |
| [WF-02 提示词](prompts/WF-02-virtual-university.md) | 虚拟大学 |
| [WF-03 提示词](prompts/WF-03-survival-adventure.md) | 生存大冒险 |
| [WF-04 提示词](prompts/WF-04-path-recommendation.md) | 五路径推荐 |
| [WF-05 提示词](prompts/WF-05-parallel-lives.md) | 平行人生 |
| [WF-06 提示词](prompts/WF-06-main-plan.md) | 主规划 |
| [WF-07 提示词](prompts/WF-07-semester-tasks.md) | 学期任务 |
| [WF-08 提示词](prompts/WF-08-growth-review.md) | 成长复盘 |
| [WF-09 提示词](prompts/WF-09-resume-entry.md) | 履历素材 |
| [WF-10 提示词](prompts/WF-10-decision-trial.md) | 决策与七天试错 |
| [WF-11 提示词](prompts/WF-11-micro-habits.md) | 微习惯与生活记录 |
| [WF-12 提示词](prompts/WF-12-session-recap.md) | 会话复盘 |

## 最短搭建顺序

```text
阅读 SHARED-STATE
→ 只搭 MAIN 的开始、路由、提取和总分支器
→ 先接 WF-01 与 WF-02
→ 通过三轮连续性门禁
→ 再接 WF-03～WF-12
→ 按 TEST-GUIDE 完整验收
```

不要跳过连续性门禁。当前 MVP 不使用数据库，如果平台没有把上一轮业务输出放进路由节点的对话历史，12 个分支就无法可靠共享状态。

## 这套 MVP 能证明什么

- 用户能否理解并愿意完成 12 个阶段。
- 默认顺序与主动跳转是否自然。
- 大模型能否在一个节点中完成原来多个提取、判断和生成步骤。
- 哪些模块值得继续投入正式数据库和知识库建设。

## 这套 MVP 不能证明什么

- 数据已经永久保存。
- 关闭调试窗口后还能继续。
- 多用户数据已经隔离。
- 路径政策是最新信息。
- 正式发布后具有生产可靠性。
