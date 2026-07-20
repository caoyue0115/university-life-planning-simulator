import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const sourceTemplate = process.env.DB_TEMPLATE || "D:/DB_TABLE_导入模板.xlsx";
const repoRoot = process.cwd();
const outputDir = process.env.DB_OUTPUT_DIR || path.join(repoRoot, ".tmp-artifact-templates");
const previewDir = process.env.DB_PREVIEW_DIR || path.join(repoRoot, ".tmp-db-previews");

const F = (name, type, description, defaultValue = null, required = false) => [
  name,
  type,
  description,
  defaultValue,
  required ? "是" : "否",
];

const U = () => F("user_key", "String", "MAIN 生成的会话级业务用户键", null, true);

const definitions = [
  ["DB-01-user-profiles.xlsx", [
    U(),
    F("profile_json", "String", "已由用户确认的正式画像 JSON", "{}"),
    F("pending_profile_json", "String", "等待用户确认的画像草稿 JSON", "{}"),
    F("pending_status", "String", "none/awaiting_confirmation/confirmed/cancelled", "none", true),
    F("record_version", "Integer", "画像记录版本号", 1, true),
    F("source_workflow", "String", "固定 WF-01", "WF-01", true),
  ]],
  ["DB-02-simulation-states.xlsx", [
    U(),
    F("state_id", "String", "业务状态标识", null, true),
    F("workflow_id", "String", "WF-02 或 WF-03", null, true),
    F("state_type", "String", "simulation/adventure", null, true),
    F("state_json", "String", "完整续接状态 JSON", "{}", true),
    F("pending_item_json", "String", "待回答事件或问题 JSON", "{}"),
    F("state_version", "Integer", "同一状态的追加版本号", 1, true),
    F("current_index", "Integer", "当前事件或题目序号", 0, true),
    F("completed", "String", "是否完成，true/false", "false", true),
  ]],
  ["DB-03-route-assessments.xlsx", [
    U(),
    F("assessment_id", "String", "评估业务标识", null, true),
    F("simulation_result_json", "String", "WF-02 完成结果 JSON", "{}"),
    F("adventure_result_json", "String", "WF-03 测试结果 JSON", "{}"),
    F("route_recommendation_json", "String", "WF-04 五路径推荐 JSON", "{}"),
    F("evidence_sources", "String", "本次使用的 WF-02/WF-03 来源列表"),
    F("evidence_gaps_json", "String", "缺少的探索证据 JSON", "[]"),
    F("confidence_level", "String", "low/medium/high", "low", true),
    F("trigger_reason", "String", "首次评估或重新评估原因", null, true),
    F("knowledge_version", "String", "本次使用的知识库版本说明"),
    F("assessment_version", "Integer", "评估版本", 1, true),
  ]],
  ["DB-04-parallel-versions.xlsx", [
    U(),
    F("comparison_id", "String", "一次方向比较标识", null, true),
    F("versions_json", "String", "2～3 个平行版本 JSON", "[]", true),
    F("comparison_json", "String", "统一维度比较结果 JSON", "{}", true),
    F("shared_baseline_json", "String", "各版本共用的初始条件", "{}", true),
    F("selected_version_name", "String", "用户当前选中的版本名"),
    F("comparison_status", "String", "draft/selected/archived", "draft", true),
    F("record_version", "Integer", "方向比较版本号", 1, true),
  ]],
  ["DB-05-main-plans.xlsx", [
    U(),
    F("plan_id", "String", "主规划业务标识", null, true),
    F("plan_json", "String", "当前或历史规划 JSON", "{}", true),
    F("pending_plan_json", "String", "待确认规划 JSON", "{}"),
    F("plan_status", "String", "pending/active/history/cancelled", "pending", true),
    F("source_comparison_id", "String", "来源方向比较标识"),
    F("change_reason", "String", "保存、切换或覆盖原因"),
    F("record_version", "Integer", "规划版本", 1, true),
  ]],
  ["DB-06-semester-tasks.xlsx", [
    U(),
    F("task_id", "String", "任务业务标识", null, true),
    F("plan_id", "String", "所属主规划标识", null, true),
    F("task_type", "String", "academic/project/research/career/habit/fitness/finance/life", "academic", true),
    F("semester", "String", "所属学期", null, true),
    F("period_label", "String", "月份、周次或自定义执行阶段"),
    F("task", "String", "任务内容", null, true),
    F("deadline_text", "String", "用户自然语言中的截止日期或检查点"),
    F("priority", "String", "高/中/低", "中", true),
    F("status", "String", "pending/in_progress/completed/postponed/cancelled", "pending", true),
    F("expected_evidence", "String", "预期成果证据"),
    F("latest_evidence", "String", "最近一次已验证行动或成果证据"),
    F("delay_reason", "String", "延期原因"),
    F("record_version", "Integer", "任务记录版本号", 1, true),
  ]],
  ["DB-07-growth-reviews.xlsx", [
    U(),
    F("review_id", "String", "复盘业务标识", null, true),
    F("plan_id", "String", "被复盘的主规划"),
    F("review_json", "String", "成长复盘结果 JSON", "{}", true),
    F("recommendation_type", "String", "continue/adjust/consider_switch", "continue", true),
    F("evidence_summary_json", "String", "行为证据汇总 JSON", "{}", true),
    F("evidence_gaps_json", "String", "复盘仍缺少的证据 JSON", "[]"),
    F("pending_change_json", "String", "建议后续确认的规划或任务变更", "{}"),
    F("record_version", "Integer", "复盘版本号", 1, true),
  ]],
  ["DB-08-resume-entries.xlsx", [
    U(),
    F("entry_id", "String", "履历条目业务标识", null, true),
    F("entry_type", "String", "项目、科研、竞赛、实习、社团等", null, true),
    F("resume_entry_json", "String", "正式履历条目 JSON", "{}"),
    F("pending_entry_json", "String", "待确认履历草稿 JSON", "{}"),
    F("quality_status", "String", "可用/缺量化/缺证明/需打磨", "需打磨", true),
    F("evidence_location", "String", "证明材料位置"),
    F("record_status", "String", "pending/confirmed/cancelled/archived", "pending", true),
    F("record_version", "Integer", "履历条目版本号", 1, true),
  ]],
  ["DB-09-decision-trials.xlsx", [
    U(),
    F("trial_id", "String", "试错或决策业务标识", null, true),
    F("record_type", "String", "analysis/plan/daily_log/day7_review", null, true),
    F("decision_json", "String", "即时决策分析 JSON", "{}"),
    F("trial_plan_json", "String", "正式七天计划 JSON", "{}"),
    F("pending_json", "String", "待确认计划或复盘 JSON", "{}"),
    F("day_number", "Integer", "第几天，1～7", 0),
    F("daily_log_json", "String", "单日记录 JSON", "{}"),
    F("review_json", "String", "第七天复盘 JSON", "{}"),
    F("trial_status", "String", "pending/active/completed/stopped", "pending", true),
    F("record_version", "Integer", "试错记录版本号", 1, true),
  ]],
  ["DB-10-action-logs.xlsx", [
    U(),
    F("log_id", "String", "行动日志业务标识", null, true),
    F("task_id", "String", "关联任务标识；独立生活记录可为空"),
    F("log_type", "String", "progress/evidence/habit/fitness/expense/safety", null, true),
    F("content_json", "String", "本次行动、习惯、运动或支出事实 JSON", "{}", true),
    F("evidence_text", "String", "成果位置、反馈或用户提供的证据"),
    F("day_number", "Integer", "周期内第几天；不适用为 0", 0),
    F("completed", "String", "本次动作是否完成，true/false", "false", true),
    F("safety_flag", "String", "none/stop_and_seek_help", "none", true),
    F("record_version", "Integer", "行动日志版本号", 1, true),
  ]],
  ["DB-11-session-recaps.xlsx", [
    U(),
    F("recap_id", "String", "会话收束业务标识", null, true),
    F("user_recap_json", "String", "给用户看的复盘 JSON", "{}", true),
    F("agent_recap_json", "String", "给 Agent 续接的复盘 JSON", "{}", true),
    F("new_facts_json", "String", "本轮新增且允许保存的事实", "[]"),
    F("state_changes_json", "String", "本轮成功发生的状态变化", "[]"),
    F("open_questions_json", "String", "未决问题 JSON", "[]"),
    F("next_action", "String", "下次建议的自然语言入口", null, true),
    F("record_version", "Integer", "会话收束版本号", 1, true),
  ]],
];

await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });

for (const [fileName, rows] of definitions) {
  const input = await FileBlob.load(sourceTemplate);
  const workbook = await SpreadsheetFile.importXlsx(input);
  const sheet = workbook.worksheets.getItem("Sheet1");
  sheet.getRange(`A2:E${rows.length + 1}`).values = rows;

  const used = sheet.getUsedRange();
  used.format.font = { name: "宋体", size: 11 };
  used.format.verticalAlignment = "center";
  used.format.wrapText = true;
  sheet.getRange(`A2:A${rows.length + 1}`).format.columnWidth = 25;
  sheet.getRange(`B2:B${rows.length + 1}`).format.columnWidth = 14;
  sheet.getRange(`C2:C${rows.length + 1}`).format.columnWidth = 46;
  sheet.getRange(`D2:D${rows.length + 1}`).format.columnWidth = 20;
  sheet.getRange(`E2:E${rows.length + 1}`).format.columnWidth = 14;
  sheet.getRange(`A1:E${rows.length + 1}`).format.rowHeight = 30;
  sheet.freezePanes.freezeRows(1);

  const inspect = await workbook.inspect({
    kind: "table",
    range: `Sheet1!A1:E${rows.length + 1}`,
    include: "values",
    tableMaxRows: rows.length + 1,
    tableMaxCols: 5,
  });
  await fs.writeFile(path.join(outputDir, `${fileName}.inspect.ndjson`), inspect.ndjson, "utf8");

  const preview = await workbook.render({ sheetName: "Sheet1", autoCrop: "all", scale: 1.5, format: "png" });
  await fs.writeFile(path.join(previewDir, fileName.replace(/\.xlsx$/, ".png")), new Uint8Array(await preview.arrayBuffer()));

  const output = await SpreadsheetFile.exportXlsx(workbook);
  await output.save(path.join(outputDir, fileName));
  console.log(`${fileName}: ${rows.length} fields`);
}
