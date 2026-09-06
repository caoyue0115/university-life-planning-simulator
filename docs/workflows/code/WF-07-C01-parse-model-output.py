# -*- coding: utf-8 -*-
import json


FIELDS = {
    "reply",
    "current_workflow",
    "current_status",
    "last_user_intent",
    "task_status",
    "task_draft",
    "task_confirmed",
    "next_workflow",
    "completed_workflow_add",
    "warnings",
}
TASK_STATUSES = {
    "not_started",
    "collecting",
    "awaiting_confirmation",
    "complete",
    "cancelled",
}
CURRENT_STATUSES = TASK_STATUSES | {"clarification_needed"}
STATE_FIELDS = {"学期", "任务", "weekly_focus", "摘要"}
TASK_FIELDS = {
    "task_id",
    "任务",
    "优先级",
    "截止日期",
    "状态",
    "success_criteria",
    "expected_evidence",
    "actual_evidence",
    "delay_reason",
}
PRIORITIES = {"高", "中", "低"}
ITEM_STATUSES = {"待处理", "完成", "推迟", "取消"}


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


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def validate_string(value, name, allow_empty=False):
    if not isinstance(value, str):
        raise ValueError(name + " 必须是字符串")
    if not allow_empty and not value.strip():
        raise ValueError(name + " 不能为空")


def validate_string_list(value, name, minimum=0, maximum=5):
    if not isinstance(value, list):
        raise ValueError(name + " 必须是 JSON 数组")
    if len(value) < minimum or len(value) > maximum:
        raise ValueError(
            name + " 项数必须在 " + str(minimum) + " 到 " + str(maximum) + " 之间"
        )
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(name + " 中每一项都必须是非空字符串")


def validate_exact_fields(value, expected, name):
    missing = expected - set(value)
    extra = set(value) - expected
    if missing:
        raise ValueError(name + " 缺少字段：" + ",".join(sorted(missing)))
    if extra:
        raise ValueError(name + " 包含未允许字段：" + ",".join(sorted(extra)))


def validate_task_item(item, name):
    if not isinstance(item, dict):
        raise ValueError(name + " 必须是 JSON 对象")
    validate_exact_fields(item, TASK_FIELDS, name)
    validate_string(item["task_id"], name + ".task_id")
    validate_string(item["任务"], name + ".任务")
    if item["优先级"] not in PRIORITIES:
        raise ValueError(name + ".优先级不合法")
    validate_string(item["截止日期"], name + ".截止日期", allow_empty=True)
    if item["状态"] not in ITEM_STATUSES:
        raise ValueError(name + ".状态不合法")
    validate_string_list(item["success_criteria"], name + ".success_criteria", 1)
    validate_string_list(item["expected_evidence"], name + ".expected_evidence", 1)
    validate_string_list(item["actual_evidence"], name + ".actual_evidence")
    validate_string(item["delay_reason"], name + ".delay_reason", allow_empty=True)

    if item["状态"] == "完成" and not item["actual_evidence"]:
        raise ValueError(name + " 标记完成时必须包含 actual_evidence")
    if item["状态"] == "推迟":
        if not item["截止日期"].strip() or not item["delay_reason"].strip():
            raise ValueError(name + " 标记推迟时必须包含新时间和 delay_reason")


def validate_task_state(value, name, minimum_tasks=1):
    validate_exact_fields(value, STATE_FIELDS, name)
    validate_string(value["学期"], name + ".学期", allow_empty=minimum_tasks == 0)
    validate_string(value["摘要"], name + ".摘要")
    validate_string_list(value["weekly_focus"], name + ".weekly_focus")

    tasks = value["任务"]
    if not isinstance(tasks, list):
        raise ValueError(name + ".任务必须是 JSON 数组")
    if len(tasks) < minimum_tasks or len(tasks) > 10:
        raise ValueError(
            name + ".任务项数必须在 " + str(minimum_tasks) + " 到 10 之间"
        )

    seen_ids = set()
    for index, item in enumerate(tasks):
        item_name = name + ".任务[" + str(index) + "]"
        validate_task_item(item, item_name)
        task_id = item["task_id"].strip()
        if task_id in seen_ids:
            raise ValueError(name + " 中 task_id 不能重复")
        seen_ids.add(task_id)


def main(model_output, user_input):
    try:
        if not isinstance(model_output, str):
            raise ValueError("model_output 必须是字符串")
        if not isinstance(user_input, str):
            raise ValueError("user_input 必须是字符串")

        text = model_output.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("模型输出顶层必须是 JSON 对象")
        validate_exact_fields(data, FIELDS, "模型输出")

        draft = parse_object(data["task_draft"], "task_draft")
        confirmed = parse_object(data["task_confirmed"], "task_confirmed")
        warnings = parse_array(data["warnings"], "warnings")

        validate_string(data["reply"], "reply")
        if data["current_workflow"] != "WF-07":
            raise ValueError("current_workflow 必须是 WF-07")
        if data["task_status"] not in TASK_STATUSES:
            raise ValueError("task_status 不合法")
        if data["current_status"] not in CURRENT_STATUSES:
            raise ValueError("current_status 不合法")
        if (
            data["current_status"] != "clarification_needed"
            and data["current_status"] != data["task_status"]
        ):
            raise ValueError("非澄清状态下两个 status 必须相同")
        if data["next_workflow"] not in {"WF-07", "WF-08", "WF-12"}:
            raise ValueError("next_workflow 不合法")
        if data["completed_workflow_add"] not in {"", "WF-07"}:
            raise ValueError("completed_workflow_add 不合法")
        if data["last_user_intent"] != user_input:
            raise ValueError("last_user_intent 必须与 user_input 完全一致")
        validate_string_list(warnings, "warnings", 0, 3)
        if len(warnings) != len(set(warnings)):
            raise ValueError("warnings 不能重复")

        status = data["task_status"]
        current_status = data["current_status"]

        if draft:
            minimum = 0 if status == "collecting" else 1
            validate_task_state(draft, "task_draft", minimum)
        if confirmed:
            validate_task_state(confirmed, "task_confirmed", 1)

        if current_status == "clarification_needed":
            if data["next_workflow"] != "WF-07":
                raise ValueError("澄清状态的 next_workflow 必须是 WF-07")
            if data["completed_workflow_add"]:
                raise ValueError("澄清状态不能添加完成标记")
        elif status == "collecting":
            if not draft:
                raise ValueError("collecting 状态下 task_draft 不能为空")
            validate_task_state(draft, "task_draft", 0)
            if data["next_workflow"] != "WF-07" or data["completed_workflow_add"]:
                raise ValueError("collecting 状态的路由组合不合法")
        elif status == "awaiting_confirmation":
            if not draft:
                raise ValueError("待确认状态下 task_draft 不能为空")
            initial_minimum = 3 if not confirmed else 1
            validate_task_state(draft, "task_draft", initial_minimum)
            if not confirmed and len(draft["任务"]) > 5:
                raise ValueError("首次生成任务必须为 3 到 5 项")
            if data["next_workflow"] != "WF-07" or data["completed_workflow_add"]:
                raise ValueError("待确认状态的路由组合不合法")
        elif status == "complete":
            if draft or not confirmed:
                raise ValueError("complete 状态的 draft/confirmed 不合法")
            if data["completed_workflow_add"] == "WF-07":
                if data["next_workflow"] != "WF-12":
                    raise ValueError("确认完成后的 next_workflow 必须是 WF-12")
            else:
                if data["next_workflow"] != "WF-08":
                    raise ValueError("查看已确认任务后的 next_workflow 必须是 WF-08")
        elif status == "cancelled":
            if draft:
                raise ValueError("cancelled 状态下 task_draft 必须为空")
            if data["next_workflow"] != "WF-07" or data["completed_workflow_add"]:
                raise ValueError("cancelled 状态的路由组合不合法")
        elif status == "not_started":
            if draft:
                raise ValueError("not_started 状态下 task_draft 必须为空")
            if data["next_workflow"] != "WF-07" or data["completed_workflow_add"]:
                raise ValueError("not_started 状态的路由组合不合法")

        return {
            "parse_ok": True,
            "error_message": "",
            "reply": data["reply"].strip(),
            "current_workflow": "WF-07",
            "current_status": current_status,
            "last_user_intent": data["last_user_intent"],
            "task_status": status,
            "task_draft_json": compact(draft),
            "task_confirmed_json": compact(confirmed),
            "next_workflow": data["next_workflow"],
            "completed_workflow_add": data["completed_workflow_add"],
            "warnings_json": compact(warnings),
        }

    except Exception as error:
        safe_user_input = user_input if isinstance(user_input, str) else ""
        return {
            "parse_ok": False,
            "error_message": str(error),
            "reply": "抱歉，刚才的学期任务结果格式异常，请再发送一次，我会继续为你处理。",
            "current_workflow": "WF-07",
            "current_status": "clarification_needed",
            "last_user_intent": safe_user_input,
            "task_status": "not_started",
            "task_draft_json": "{}",
            "task_confirmed_json": "{}",
            "next_workflow": "WF-07",
            "completed_workflow_add": "",
            "warnings_json": "[]",
        }
