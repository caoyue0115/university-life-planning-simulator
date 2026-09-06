# -*- coding: utf-8 -*-
import json


TOP_FIELDS = {
    "reply", "current_workflow", "current_status", "last_user_intent",
    "final_review_status", "final_review_draft", "final_review_confirmed",
    "next_workflow", "completed_workflow_add", "warnings",
}
DRAFT_FIELDS = {
    "completed_modules", "confirmed_decisions", "new_explicit_facts",
    "pending_drafts", "unresolved_questions", "next_three_actions",
    "recommended_return_point", "user_summary", "agent_notes",
}
NOTE_FIELDS = {"preference_changes", "route_changes", "task_changes", "inferences_to_verify"}
PENDING_FIELDS = {"workflow", "module_name"}
STATUSES = {"not_started", "collecting", "awaiting_confirmation", "complete", "cancelled"}
WORKFLOWS = {"WF-01", "WF-02", "WF-03", "WF-04", "WF-06", "WF-07", "WF-08", "WF-09", "WF-10", "WF-11", "WF-12"}
MENU_NAMES = {"用户画像", "虚拟大学", "生存大冒险", "五路径推荐", "主规划", "学期任务", "成长复盘", "履历素材", "决策与七天试错", "微习惯", "会话复盘"}
MODULES = (
    ("WF-01", "用户画像", "profile_status"),
    ("WF-02", "虚拟大学", "simulation_status"),
    ("WF-03", "生存大冒险", "adventure_status"),
    ("WF-04", "五路径推荐", "recommendation_status"),
    ("WF-06", "主规划", "plan_status"),
    ("WF-07", "学期任务", "task_status"),
    ("WF-08", "成长复盘", "review_status"),
    ("WF-09", "履历素材", "asset_status"),
    ("WF-10", "决策与七天试错", "trial_status"),
    ("WF-11", "微习惯", "habit_status"),
)


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def parse_value(value):
    if not isinstance(value, str):
        return value
    value = value.strip()
    if not value:
        return value
    return json.loads(value)


def parse_object(value, name):
    value = parse_value(value)
    if not isinstance(value, dict):
        raise ValueError(name + " 必须是 JSON 对象")
    return value


def parse_array(value, name):
    value = parse_value(value)
    if not isinstance(value, list):
        raise ValueError(name + " 必须是 JSON 数组")
    return value


def first_row(value):
    value = parse_value(value)
    if isinstance(value, dict):
        return value
    if isinstance(value, list) and value:
        row = parse_value(value[0])
        return row if isinstance(row, dict) else {}
    return {}


def exact(value, expected, name):
    missing = expected - set(value)
    extra = set(value) - expected
    if missing:
        raise ValueError(name + " 缺少字段：" + ",".join(sorted(missing)))
    if extra:
        raise ValueError(name + " 包含未允许字段：" + ",".join(sorted(extra)))


def nonempty_string(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(name + " 必须是非空字符串")


def string_list(value, name, maximum):
    if not isinstance(value, list) or len(value) > maximum:
        raise ValueError(name + " 必须是最多 " + str(maximum) + " 项的数组")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(name + " 每项必须是非空字符串")
    if len(value) != len(set(value)):
        raise ValueError(name + " 不能重复")


def completed_from_route(route_state_rows):
    row = first_row(route_state_rows)
    completed = parse_value(row.get("completed_workflows", []))
    if completed in (None, ""):
        completed = []
    if not isinstance(completed, list):
        raise ValueError("公共 completed_workflows 必须是数组")
    clean = []
    for item in completed:
        if isinstance(item, str) and item in WORKFLOWS and item not in clean:
            clean.append(item)
    return clean


def expected_pending(rows):
    result = []
    for (workflow, name, status_field), state_rows in zip(MODULES, rows):
        row = first_row(state_rows)
        if row.get(status_field) == "awaiting_confirmation":
            result.append({"workflow": workflow, "module_name": name})
    return result


def validate_review(value, name, expected_completed, expected_pending_items):
    if not isinstance(value, dict):
        raise ValueError(name + " 必须是对象")
    exact(value, DRAFT_FIELDS, name)
    completed = value["completed_modules"]
    if not isinstance(completed, list) or len(completed) > 11:
        raise ValueError(name + ".completed_modules 最多 11 项")
    if any(item not in WORKFLOWS for item in completed) or len(completed) != len(set(completed)):
        raise ValueError(name + ".completed_modules 包含无效或重复工作流")
    if completed != expected_completed:
        raise ValueError(name + ".completed_modules 必须与公共完成列表一致")
    for field in ("confirmed_decisions", "new_explicit_facts", "unresolved_questions"):
        string_list(value[field], name + "." + field, 5)
    string_list(value["next_three_actions"], name + ".next_three_actions", 3)
    pending = value["pending_drafts"]
    if not isinstance(pending, list) or len(pending) > 10:
        raise ValueError(name + ".pending_drafts 最多 10 项")
    for index, item in enumerate(pending):
        if not isinstance(item, dict):
            raise ValueError(name + ".pending_drafts 项必须是对象")
        exact(item, PENDING_FIELDS, name + ".pending_drafts[" + str(index) + "]")
        nonempty_string(item["module_name"], name + ".pending_drafts.module_name")
        known = {(workflow, module_name) for workflow, module_name, _ in MODULES}
        if (item["workflow"], item["module_name"]) not in known:
            raise ValueError(name + ".pending_drafts 包含无效模块")
    if len({item["workflow"] for item in pending}) != len(pending):
        raise ValueError(name + ".pending_drafts 不能重复")
    if pending != expected_pending_items:
        raise ValueError(name + ".pending_drafts 必须与真实待确认状态一致")
    if value["recommended_return_point"] not in WORKFLOWS:
        raise ValueError(name + ".recommended_return_point 不合法")
    nonempty_string(value["user_summary"], name + ".user_summary")
    notes = value["agent_notes"]
    if not isinstance(notes, dict):
        raise ValueError(name + ".agent_notes 必须是对象")
    exact(notes, NOTE_FIELDS, name + ".agent_notes")
    for field in NOTE_FIELDS:
        string_list(notes[field], name + ".agent_notes." + field, 5)


def main(model_output, user_input, route_state_rows,
         profile_state_rows, simulation_state_rows, adventure_state_rows,
         recommendation_state_rows, plan_state_rows, task_state_rows,
         review_state_rows, resume_state_rows, trial_state_rows, habit_state_rows):
    try:
        if not isinstance(model_output, str) or not isinstance(user_input, str):
            raise ValueError("model_output 和 user_input 必须是字符串")
        raw = model_output.strip()
        if raw.startswith("```"):
            lines = raw.splitlines()
            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw = "\n".join(lines).strip()
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("模型输出顶层必须是对象")
        exact(data, TOP_FIELDS, "模型输出")
        draft = parse_object(data["final_review_draft"], "final_review_draft")
        confirmed = parse_object(data["final_review_confirmed"], "final_review_confirmed")
        warnings = parse_array(data["warnings"], "warnings")
        nonempty_string(data["reply"], "reply")
        if data["current_workflow"] != "WF-12":
            raise ValueError("current_workflow 必须是 WF-12")
        status = data["final_review_status"]
        if status not in STATUSES or data["current_status"] != status:
            raise ValueError("current_status 必须与合法 final_review_status 一致")
        if data["last_user_intent"] != user_input:
            raise ValueError("last_user_intent 必须与 user_input 完全一致")
        if data["next_workflow"] not in WORKFLOWS:
            raise ValueError("next_workflow 不合法")
        if data["completed_workflow_add"] not in {"", "WF-12"}:
            raise ValueError("completed_workflow_add 不合法")
        string_list(warnings, "warnings", 3)

        expected_completed = completed_from_route(route_state_rows)
        module_rows = (profile_state_rows, simulation_state_rows, adventure_state_rows,
                       recommendation_state_rows, plan_state_rows, task_state_rows,
                       review_state_rows, resume_state_rows, trial_state_rows, habit_state_rows)
        pending = expected_pending(module_rows)
        if draft:
            validate_review(draft, "final_review_draft", expected_completed, pending)
        if confirmed:
            validate_review(confirmed, "final_review_confirmed", confirmed["completed_modules"], confirmed["pending_drafts"])

        if status == "awaiting_confirmation":
            if not draft or data["next_workflow"] != "WF-12" or data["completed_workflow_add"]:
                raise ValueError("awaiting_confirmation 状态组合不合法")
            for name in MENU_NAMES:
                if name not in data["reply"]:
                    raise ValueError("reply 缺少模块菜单项：" + name)
            for label in {"已完成", "待确认", "未完成"}:
                if label not in data["reply"]:
                    raise ValueError("reply 缺少菜单状态标签：" + label)
            if "确认" not in data["reply"]:
                raise ValueError("reply 必须询问是否确认")
            if "系统记录" not in data["reply"] or "永久" not in data["reply"]:
                raise ValueError("reply 缺少数据库持久化边界说明")
        elif status == "complete":
            if draft or not confirmed:
                raise ValueError("complete 的 draft/confirmed 组合不合法")
            if data["completed_workflow_add"] != "WF-12":
                raise ValueError("complete 必须追加 WF-12")
            if data["next_workflow"] != confirmed["recommended_return_point"]:
                raise ValueError("complete 的 next_workflow 必须等于 recommended_return_point")
        elif status in {"not_started", "collecting", "cancelled"}:
            if status in {"not_started", "cancelled"} and draft:
                raise ValueError(status + " 不得保留 draft")
            if data["next_workflow"] != "WF-12" or data["completed_workflow_add"]:
                raise ValueError(status + " 路由组合不合法")

        return {
            "parse_ok": True,
            "error_message": "",
            "reply": data["reply"].strip(),
            "current_workflow": "WF-12",
            "current_status": status,
            "last_user_intent": data["last_user_intent"],
            "final_review_status": status,
            "final_review_draft_json": compact(draft),
            "final_review_confirmed_json": compact(confirmed),
            "next_workflow": data["next_workflow"],
            "completed_workflow_add": data["completed_workflow_add"],
            "warnings_json": compact(warnings),
        }
    except Exception as error:
        safe_input = user_input if isinstance(user_input, str) else ""
        return {
            "parse_ok": False,
            "error_message": str(error),
            "reply": "抱歉，刚才的会话复盘格式异常，请再发送一次，我会继续为你处理。",
            "current_workflow": "WF-12",
            "current_status": "collecting",
            "last_user_intent": safe_input,
            "final_review_status": "collecting",
            "final_review_draft_json": "{}",
            "final_review_confirmed_json": "{}",
            "next_workflow": "WF-12",
            "completed_workflow_add": "",
            "warnings_json": "[]",
        }
