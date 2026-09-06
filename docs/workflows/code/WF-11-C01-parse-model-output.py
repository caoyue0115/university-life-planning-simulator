# -*- coding: utf-8 -*-
import json


TOP_FIELDS = {
    "reply", "current_workflow", "current_status", "last_user_intent",
    "habit_status", "habit_draft", "habit_confirmed", "next_workflow",
    "completed_workflow_add", "warnings",
}
STATUSES = {"not_started", "collecting", "awaiting_confirmation", "complete", "cancelled"}
DRAFT_FIELDS = {"行动", "habit_type", "记录", "minimum_next_action", "recent_pattern", "supportive_feedback", "摘要"}
RECORD_FIELDS = {"描述", "duration_or_amount", "类别", "completed", "user_note"}
CONFIRMED_FIELDS = {"records", "摘要"}
ACTIONS = {"plan", "record", "review"}
HABIT_TYPES = {"走路", "冥想", "阅读", "记账", "健身", "素材整理", "其他"}


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def parse_object(value, name):
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, dict):
        raise ValueError(name + " 必须是 JSON 对象")
    return value


def parse_array(value, name):
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, list):
        raise ValueError(name + " 必须是 JSON 数组")
    return value


def exact(value, expected, name):
    missing = expected - set(value)
    extra = set(value) - expected
    if missing:
        raise ValueError(name + " 缺少字段：" + ",".join(sorted(missing)))
    if extra:
        raise ValueError(name + " 包含未允许字段：" + ",".join(sorted(extra)))


def string(value, name, allow_empty=False):
    if not isinstance(value, str):
        raise ValueError(name + " 必须是字符串")
    if not allow_empty and not value.strip():
        raise ValueError(name + " 不能为空")


def string_list(value, name, maximum):
    if not isinstance(value, list) or len(value) > maximum:
        raise ValueError(name + " 必须是最多 " + str(maximum) + " 项的数组")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(name + " 每项必须是非空字符串")


def validate_draft(value, name, complete):
    if not isinstance(value, dict):
        raise ValueError(name + " 必须是对象")
    exact(value, DRAFT_FIELDS, name)
    action = value["行动"]
    habit_type = value["habit_type"]
    if action not in ACTIONS and not (not complete and action == ""):
        raise ValueError(name + ".行动不合法")
    if habit_type not in HABIT_TYPES and not (not complete and habit_type == ""):
        raise ValueError(name + ".habit_type 不合法")
    record = value["记录"]
    if not isinstance(record, dict):
        raise ValueError(name + ".记录必须是对象")
    exact(record, RECORD_FIELDS, name + ".记录")
    for field in {"描述", "duration_or_amount", "类别", "user_note"}:
        string(record[field], name + ".记录." + field, allow_empty=(field != "描述" or not complete))
    if not isinstance(record["completed"], bool):
        raise ValueError(name + ".记录.completed 必须是 Boolean")
    for field in {"minimum_next_action", "recent_pattern", "supportive_feedback", "摘要"}:
        string(value[field], name + "." + field, allow_empty=not complete)
    if complete:
        if action == "plan" and record["completed"]:
            raise ValueError("plan 的 completed 必须为 false")
        if action == "record" and not record["completed"]:
            raise ValueError("record 的 completed 必须为 true")
        if action == "review" and record["completed"]:
            raise ValueError("review 的 completed 必须为 false")
        if habit_type in {"走路", "健身"} and action == "record" and not record["duration_or_amount"].strip():
            raise ValueError("运动记录缺少时长或数量")
        if habit_type == "记账" and action == "record" and not record["duration_or_amount"].strip():
            raise ValueError("记账记录缺少金额")


def validate_confirmed(value):
    if not value:
        return
    exact(value, CONFIRMED_FIELDS, "habit_confirmed")
    records = value["records"]
    if not isinstance(records, list) or len(records) > 5:
        raise ValueError("habit_confirmed.records 必须是最多 5 项的数组")
    for index, record in enumerate(records):
        validate_draft(record, "habit_confirmed.records[" + str(index) + "]", True)
    string(value["摘要"], "habit_confirmed.摘要", allow_empty=len(records) == 0)


def main(model_output, user_input):
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
        draft = parse_object(data["habit_draft"], "habit_draft")
        confirmed = parse_object(data["habit_confirmed"], "habit_confirmed")
        warnings = parse_array(data["warnings"], "warnings")
        string(data["reply"], "reply")
        if data["current_workflow"] != "WF-11":
            raise ValueError("current_workflow 必须是 WF-11")
        status = data["habit_status"]
        if status not in STATUSES or data["current_status"] != status:
            raise ValueError("current_status 必须与合法 habit_status 一致")
        if data["last_user_intent"] != user_input:
            raise ValueError("last_user_intent 必须与 user_input 完全一致")
        if data["next_workflow"] not in {"WF-11", "WF-12"}:
            raise ValueError("next_workflow 不合法")
        if data["completed_workflow_add"] not in {"", "WF-11"}:
            raise ValueError("completed_workflow_add 不合法")
        string_list(warnings, "warnings", 3)
        if len(warnings) != len(set(warnings)):
            raise ValueError("warnings 不能重复")
        validate_confirmed(confirmed)
        if draft:
            validate_draft(draft, "habit_draft", status == "awaiting_confirmation")

        if status == "collecting":
            if not draft or data["next_workflow"] != "WF-11" or data["completed_workflow_add"]:
                raise ValueError("collecting 状态组合不合法")
        elif status == "awaiting_confirmation":
            if not draft:
                raise ValueError("awaiting_confirmation 必须有完整 draft")
            validate_draft(draft, "habit_draft", True)
            if data["next_workflow"] != "WF-11" or data["completed_workflow_add"]:
                raise ValueError("awaiting_confirmation 路由组合不合法")
        elif status == "complete":
            if draft or not confirmed or not confirmed.get("records"):
                raise ValueError("complete 的 draft/confirmed 组合不合法")
            if data["next_workflow"] != "WF-12" or data["completed_workflow_add"] != "WF-11":
                raise ValueError("complete 路由组合不合法")
        elif status in {"not_started", "cancelled"}:
            if draft or data["next_workflow"] != "WF-11" or data["completed_workflow_add"]:
                raise ValueError(status + " 状态组合不合法")

        return {
            "parse_ok": True,
            "error_message": "",
            "reply": data["reply"].strip(),
            "current_workflow": "WF-11",
            "current_status": status,
            "last_user_intent": data["last_user_intent"],
            "habit_status": status,
            "habit_draft_json": compact(draft),
            "habit_confirmed_json": compact(confirmed),
            "next_workflow": data["next_workflow"],
            "completed_workflow_add": data["completed_workflow_add"],
            "warnings_json": compact(warnings),
        }
    except Exception as error:
        safe_input = user_input if isinstance(user_input, str) else ""
        return {
            "parse_ok": False,
            "error_message": str(error),
            "reply": "抱歉，刚才的微习惯记录格式异常，请再发送一次，我会继续为你处理。",
            "current_workflow": "WF-11",
            "current_status": "collecting",
            "last_user_intent": safe_input,
            "habit_status": "collecting",
            "habit_draft_json": "{}",
            "habit_confirmed_json": "{}",
            "next_workflow": "WF-11",
            "completed_workflow_add": "",
            "warnings_json": "[]",
        }
