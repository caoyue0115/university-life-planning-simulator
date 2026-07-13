from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from render_workflow_diagrams import parse_flowchart


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / "docs" / "workflows"
START = "<!-- GENERATED-NODE-LEDGER:START -->"
END = "<!-- GENERATED-NODE-LEDGER:END -->"


def node_type(label: str) -> str:
    for value in [
        "数据库", "大模型", "变量提取器", "代码", "分支器", "消息", "结束",
        "开始", "知识库", "问答节点", "变量存储器", "文本处理", "长期记忆",
    ]:
        if value in label:
            return value
    return "处理节点"


EXTRACTOR_CONTRACTS = {
    ("WF-02-virtual-university.md", "D"): "`selected_option:String`（匹配当前事件选项）、`is_valid:Boolean`（能否结算）",
    ("WF-02-virtual-university.md", "H"): "`new_state:String`（结算后的完整状态 JSON）",
    ("WF-03-survival-adventure.md", "D"): "`selected_option:String`（当前题答案）、`answer_valid:Boolean`（是否匹配选项）",
    ("WF-03-survival-adventure.md", "H"): "`signal_json:String`（本题五路径与八项能力信号 JSON）",
    ("WF-03-survival-adventure.md", "L"): "`question_json:String`（下一题及选项 JSON）",
    ("WF-04-path-recommendation.md", "H"): "`route_recommendation_json:String`（完整五路径推荐 JSON）",
    ("WF-04-path-recommendation.md", "L"): "`route_recommendation_json:String`（修复后的完整推荐 JSON）",
    ("WF-05-parallel-lives.md", "B"): "`routes:Array<String>`（用户选择的 2～3 条候选路径）",
    ("WF-05-parallel-lives.md", "H"): "`parallel_versions_json:String`（全部版本、共同基线和比较结果 JSON）",
    ("WF-06-main-plan.md", "A1"): "`confirm_action:String`（none/modify/confirm/cancel）、`confirmation_token:String`（用户原样提供）",
    ("WF-06-main-plan.md", "G"): "`main_plan_json:String`（完整四层主规划 JSON）",
    ("WF-07-semester-tasks.md", "A1"): "`intent:String`、`task_id:String`、`requested_changes:String`、`filters:String`、`action_evidence:String`、`confirm_action:String`、`confirmation_token:String`",
    ("WF-07-semester-tasks.md", "E"): "`tasks_json:String`（完整 tasks 数组 JSON）",
    ("WF-08-growth-review.md", "A1"): "`confirm_action:String`（none/modify/confirm/cancel）、`confirmation_token:String`",
    ("WF-08-growth-review.md", "I"): "`growth_review_json:String`（完整成长复盘 JSON）",
    ("WF-09-resume-entry.md", "X"): "`resume_entry_json:String`（仅含用户事实的履历字段 JSON）",
    ("WF-09-resume-entry.md", "GX"): "`final_resume_entry_json:String`（润色后待校验履历 JSON）",
    ("WF-10-decision-and-trial.md", "X"): "`mode:String`、`trial_id:String`、`day:Integer`、`high_risk:Boolean`、`risk_reason:String`",
    ("WF-10-decision-and-trial.md", "PX"): "`trial_plan_json:String`（完整七天计划 JSON）",
    ("WF-10-decision-and-trial.md", "LX"): "`daily_log_json:String`（单日记录 JSON）",
    ("WF-10-decision-and-trial.md", "DX"): "`day7_review_json:String`（第七天复盘 JSON）",
    ("WF-11-micro-habits.md", "X"): "`category:String`、`operation:String`、`risk_flags:Array<String>`、`confirm_action:String`、`confirmation_token:String`",
    ("WF-12-session-recap.md", "X"): "`user_recap:String`、`agent_recap:String`、`state_changes:String`、`next_entry:String`、`session_recap_json:String`",
}


def output_contract(kind: str, filename: str, node_id: str) -> str:
    if kind == "变量提取器" and (filename, node_id) in EXTRACTOR_CONTRACTS:
        return EXTRACTOR_CONTRACTS[(filename, node_id)]
    return {
        "开始": "开始节点中声明的同名变量",
        "数据库": "`isSuccess:Boolean`、`message:String`、`outputList:Array<Object>`",
        "大模型": "`output:String`",
        "变量提取器": "按本文件提取变量表逐行声明（含类型和描述）",
        "代码": "与 Python `main()` 返回 dict 的键完全一致",
        "分支器": "不产生业务变量；按条件输出连线",
        "消息": "不新增业务变量；回答内容引用上游变量",
        "结束": "`output` 引用上游最终结果",
        "知识库": "`results:Array<Object>`",
        "问答节点": "`query:String`、`content:String`",
        "变量存储器": "设置或获取的同名变量",
        "文本处理": "`output:String`",
        "长期记忆": "写入：`isSuccess/message`；检索：`memory:Array<Object>`",
    }.get(kind, "按节点页面固定输出")


def clean(value: str) -> str:
    return value.replace("|", "/").replace("\n", " ").replace('"', "").strip()


def build(text: str, filename: str) -> str:
    blocks = re.findall(r"```mermaid\s*\n([\s\S]*?)```", text)
    if not blocks:
        raise RuntimeError(f"{filename}: Mermaid block missing")
    # A workflow may be split into several readable diagrams.  Reusing the same
    # Mermaid ids for shared entry/exit nodes lets the combined ledger dedupe
    # those nodes while retaining every distinct branch.
    nodes, edges = parse_flowchart("\n".join(blocks))
    incoming: dict[str, list[str]] = defaultdict(list)
    outgoing: dict[str, list[str]] = defaultdict(list)
    for source, target, edge_label in edges:
        incoming[target].append(source)
        suffix = f"（{edge_label}）" if edge_label else ""
        outgoing[source].append(f"{target}{suffix}")

    lines = [
        START,
        "### 画布节点连线与页面输入输出总表",
        "",
        "本表由流程图生成，用于防止漏连。‘直接上游’决定页面引用下拉框中可选的数据来源；具体变量名以本文件后续业务映射表为准。",
        "开始节点类型规则：`uid/session_id/AGENT_USER_INPUT` 及所有 `*_json/*_token/*_id` 均选 String；计数、天数选 Integer；真伪开关选 Boolean。表中未特别标注的输入一律选 String，JSON 作为字符串传递。",
        "",
        "| 节点 | 类型 | 直接上游（输入来源） | 固定/声明输出 | 直接下游 |",
        "|---|---|---|---|---|",
    ]
    for node_id, (label, _) in nodes.items():
        kind = node_type(label)
        upstream = "、".join(incoming.get(node_id, [])) or "无（起点）"
        downstream = "、".join(outgoing.get(node_id, [])) or "无；必须在正文说明为何终止或转入下一张图"
        lines.append(
            f"| `{node_id}` {clean(label)} | {kind} | {upstream} | {output_contract(kind, filename, node_id)} | {downstream} |"
        )
    lines.extend([END, ""])
    return "\n".join(lines)


def main() -> None:
    for path in sorted(WORKFLOWS.glob("WF-0[2-9]-*.md")) + sorted(WORKFLOWS.glob("WF-1[0-2]-*.md")):
        text = path.read_text(encoding="utf-8")
        generated = build(text, path.name)
        if START in text:
            text = re.sub(
                rf"{re.escape(START)}[\s\S]*?{re.escape(END)}\n?",
                generated,
                text,
                count=1,
            )
        else:
            marker = "## 节点逐项配置\n"
            if marker not in text:
                raise RuntimeError(f"{path.name}: node configuration section missing")
            text = text.replace(marker, marker + "\n" + generated, 1)
        path.write_text(text.rstrip() + "\n", encoding="utf-8")
        print(path.name)


if __name__ == "__main__":
    main()
