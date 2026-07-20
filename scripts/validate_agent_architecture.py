from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / "docs" / "workflows"
DATABASE = ROOT / "docs" / "database"

EXPECTED_GUIDES = {
    "WF-01-user-profile.md",
    "WF-02-virtual-university.md",
    "WF-03-survival-adventure.md",
    "WF-04-path-recommendation.md",
    "WF-05-direction-and-main-plan.md",
    "WF-06-semester-actions.md",
    "WF-07-review-and-recap.md",
    "WF-08-resume-evidence.md",
    "WF-09-decision-trial.md",
}

CONTRACT = re.compile(
    r"<!--\s*AGENT-CONTRACT\s*\n"
    r"start_inputs:\s*AGENT_USER_INPUT:String\s*\n"
    r"extractor_input_count:\s*1\s*\n"
    r"result_output:\s*result_json:String\s*\n"
    r"-->",
    re.MULTILINE,
)


def sql_blocks(text: str) -> list[str]:
    return re.findall(r"```sql\s*\n([\s\S]*?)```", text, flags=re.IGNORECASE)


def active_docs() -> list[Path]:
    files = [
        ROOT / "README.md",
        ROOT / "docs" / "PRD.md",
        WORKFLOWS / "README.md",
        WORKFLOWS / "SHARED-CONTRACTS.md",
        WORKFLOWS / "PLATFORM-UI-CONTRACT.md",
        DATABASE / "README.md",
        DATABASE / "DATABASE-SCHEMA.md",
        DATABASE / "SQL-EXAMPLES.md",
        DATABASE / "WF-DATABASE-MATRIX.md",
    ]
    files.extend(sorted(WORKFLOWS.glob("WF-??-*.md")))
    return [path for path in files if path.is_file()]


def main() -> int:
    errors: list[str] = []
    main_guide = WORKFLOWS / "MAIN-00-agent-orchestrator.md"
    if not main_guide.is_file():
        errors.append("missing MAIN-00-agent-orchestrator.md")

    actual_guides = {path.name for path in WORKFLOWS.glob("WF-??-*.md")}
    missing = sorted(EXPECTED_GUIDES - actual_guides)
    extra = sorted(actual_guides - EXPECTED_GUIDES)
    if missing:
        errors.append("missing final workflow guides: " + ", ".join(missing))
    if extra:
        errors.append("legacy or unexpected workflow guides remain: " + ", ".join(extra))

    for path in sorted(WORKFLOWS.glob("WF-??-*.md")):
        text = path.read_text(encoding="utf-8")
        if not CONTRACT.search(text):
            errors.append(f"{path.name}: missing exact single-parameter AGENT-CONTRACT marker")
        if "`AGENT_USER_INPUT:String`" not in text:
            errors.append(f"{path.name}: missing exact Start input declaration")
        if "result_json:String" not in text:
            errors.append(f"{path.name}: missing compact MCP result declaration")
        if "调试指南" not in text or "验收清单" not in text:
            errors.append(f"{path.name}: missing detailed debug or acceptance section")
        if re.search(r"输入(?:两行|多行)|变量提取器[^\n]{0,80}输入[：:]?\s*`?\w+=", text):
            errors.append(f"{path.name}: extractor instructions may contain multiple inputs")
        if re.search(r"(?:复制|填写|粘贴|输入)[^\n]{0,24}(?:confirmation_)?token", text, re.IGNORECASE):
            errors.append(f"{path.name}: asks user to handle a confirmation token")
        if re.search(r"```mermaid[\s\S]*?(?:Agent\s*智能决策|工作流节点|MCP\s*工具)[\s\S]*?```", text):
            errors.append(f"{path.name}: child diagram contains nested orchestration")
        for index, sql in enumerate(sql_blocks(text), start=1):
            if re.search(r"\bWHERE\s+uid\b|\bAND\s+uid\b|\buid\s*=", sql, re.IGNORECASE):
                errors.append(f"{path.name}: SQL block {index} uses platform uid as business identity")
            if "user_key" not in sql and re.search(r"\b(?:SELECT|UPDATE|DELETE)\b", sql, re.IGNORECASE):
                errors.append(f"{path.name}: SQL block {index} does not filter by user_key")

    for path in active_docs():
        text = path.read_text(encoding="utf-8")
        for index, sql in enumerate(sql_blocks(text), start=1):
            if re.search(r"\bWHERE\s+uid\b|\bAND\s+uid\b|\buid\s*=", sql, re.IGNORECASE):
                errors.append(f"{path.relative_to(ROOT)}: SQL block {index} uses business uid")

    navigation_files = [ROOT / "README.md", WORKFLOWS / "README.md", ROOT / "docs" / "PRD.md"]
    for path in navigation_files:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(r"WF-1[0-2]", text):
            errors.append(f"{path.relative_to(ROOT)}: navigation/product architecture still references WF-10～WF-12")

    database_schema = DATABASE / "DATABASE-SCHEMA.md"
    if database_schema.is_file():
        schema = database_schema.read_text(encoding="utf-8")
        if schema.count("`user_key`") < 11:
            errors.append("DATABASE-SCHEMA.md: user_key is not declared for all eleven tables")
        if "`action_logs`" not in schema or "`habit_logs`" in schema:
            errors.append("DATABASE-SCHEMA.md: DB-10 must be action_logs, not habit_logs")

    if errors:
        print("\n".join(f"ERROR: {item}" for item in errors))
        print(f"FAIL: {len(errors)} architecture violation(s)")
        return 1
    print("PASS: MAIN-00 + 9 MCP workflow architecture validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
