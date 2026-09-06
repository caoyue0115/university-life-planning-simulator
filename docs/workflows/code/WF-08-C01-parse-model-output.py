# -*- coding: utf-8 -*-
import json


FIELDS = {
    "reply", "current_workflow", "current_status", "last_user_intent",
    "review_status", "review_draft", "review_confirmed", "next_workflow",
    "completed_workflow_add", "warnings",
}
REVIEW_STATUSES = {"not_started", "collecting", "awaiting_confirmation", "complete", "cancelled"}
CURRENT_STATUSES = REVIEW_STATUSES | {"clarification_needed"}
REVIEW_FIELDS = {
    "explicit_new_facts", "behavior_evidence", "agent_inferences",
    "changes_since_plan", "impact_on_plan", "推荐",
    "recommended_adjustments", "opportunity_costs", "questions_to_verify", "摘要",
}
RECOMMENDATIONS = {"continue", "adjust", "consider_switch"}
ARRAY_FIELDS = {
    "explicit_new_facts", "behavior_evidence", "agent_inferences",
    "changes_since_plan", "impact_on_plan", "recommended_adjustments",
    "opportunity_costs", "questions_to_verify",
}


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


def validate_exact_fields(value, expected, name):
    missing = expected - set(value)
    extra = set(value) - expected
    if missing:
        raise ValueError(name + " 缺少字段：" + ",".join(sorted(missing)))
    if extra:
        raise ValueError(name + " 包含未允许字段：" + ",".join(sorted(extra)))


def validate_string(value, name, allow_empty=False):
    if not isinstance(value, str):
        raise ValueError(name + " 必须是字符串")
    if not allow_empty and not value.strip():
        raise ValueError(name + " 不能为空")


def validate_string_list(value, name, minimum=0, maximum=5):
    if not isinstance(value, list):
        raise ValueError(name + " 必须是 JSON 数组")
    if len(value) < minimum or len(value) > maximum:
        raise ValueError(name + " 项数必须在 " + str(minimum) + " 到 " + str(maximum) + " 之间")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(name + " 中每一项都必须是非空字符串")


def validate_review(review, name, collecting=False):
    validate_exact_fields(review, REVIEW_FIELDS, name)
    for field in ARRAY_FIELDS:
        minimum = 0
        if not collecting and field in {
            "impact_on_plan", "recommended_adjustments", "opportunity_costs", "questions_to_verify"
        }:
            minimum = 1
        validate_string_list(review[field], name + "." + field, minimum, 5)
    validate_string(review["摘要"], name + ".摘要")

    recommendation = review["推荐"]
    if collecting:
        if recommendation != "":
            raise ValueError(name + ".推荐在 collecting 状态下必须为空")
    elif recommendation not in RECOMMENDATIONS:
        raise ValueError(name + ".推荐不合法")

    if not collecting and not (review["explicit_new_facts"] or review["behavior_evidence"]):
        raise ValueError(name + " 必须至少包含一项明确事实或行为证据")


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

        draft = parse_object(data["review_draft"], "review_draft")
        confirmed = parse_object(data["review_confirmed"], "review_confirmed")
        warnings = parse_array(data["warnings"], "warnings")

        validate_string(data["reply"], "reply")
        if data["current_workflow"] != "WF-08":
            raise ValueError("current_workflow 必须是 WF-08")
        if data["review_status"] not in REVIEW_STATUSES:
            raise ValueError("review_status 不合法")
        if data["current_status"] not in CURRENT_STATUSES:
            raise ValueError("current_status 不合法")
        if data["current_status"] != "clarification_needed" and data["current_status"] != data["review_status"]:
            raise ValueError("非澄清状态下两个 status 必须相同")
        if data["next_workflow"] not in {"WF-08", "WF-12"}:
            raise ValueError("next_workflow 不合法")
        if data["completed_workflow_add"] not in {"", "WF-08"}:
            raise ValueError("completed_workflow_add 不合法")
        if data["last_user_intent"] != user_input:
            raise ValueError("last_user_intent 必须与 user_input 完全一致")
        validate_string_list(warnings, "warnings", 0, 3)
        if len(warnings) != len(set(warnings)):
            raise ValueError("warnings 不能重复")

        status = data["review_status"]
        current_status = data["current_status"]
        if draft:
            validate_review(draft, "review_draft", collecting=status == "collecting")
        if confirmed:
            validate_review(confirmed, "review_confirmed", collecting=False)

        if current_status == "clarification_needed":
            if data["next_workflow"] != "WF-08" or data["completed_workflow_add"]:
                raise ValueError("澄清状态的路由组合不合法")
        elif status == "collecting":
            if not draft:
                raise ValueError("collecting 状态下 review_draft 不能为空")
            validate_review(draft, "review_draft", collecting=True)
            if data["next_workflow"] != "WF-08" or data["completed_workflow_add"]:
                raise ValueError("collecting 状态的路由组合不合法")
        elif status == "awaiting_confirmation":
            if not draft:
                raise ValueError("待确认状态下 review_draft 不能为空")
            validate_review(draft, "review_draft", collecting=False)
            if data["next_workflow"] != "WF-08" or data["completed_workflow_add"]:
                raise ValueError("待确认状态的路由组合不合法")
        elif status == "complete":
            if draft or not confirmed:
                raise ValueError("完成状态的 draft/confirmed 不合法")
            if data["next_workflow"] != "WF-12" or data["completed_workflow_add"] != "WF-08":
                raise ValueError("完成状态的路由组合不合法")
        elif status == "cancelled":
            if draft:
                raise ValueError("取消状态下 review_draft 必须为空")
            if data["next_workflow"] != "WF-08" or data["completed_workflow_add"]:
                raise ValueError("取消状态的路由组合不合法")
        elif status == "not_started":
            if draft:
                raise ValueError("not_started 状态下 review_draft 必须为空")
            if data["next_workflow"] != "WF-08" or data["completed_workflow_add"]:
                raise ValueError("not_started 状态的路由组合不合法")

        return {
            "parse_ok": True,
            "error_message": "",
            "reply": data["reply"].strip(),
            "current_workflow": "WF-08",
            "current_status": current_status,
            "last_user_intent": data["last_user_intent"],
            "review_status": status,
            "review_draft_json": compact(draft),
            "review_confirmed_json": compact(confirmed),
            "next_workflow": data["next_workflow"],
            "completed_workflow_add": data["completed_workflow_add"],
            "warnings_json": compact(warnings),
        }
    except Exception as error:
        safe_user_input = user_input if isinstance(user_input, str) else ""
        return {
            "parse_ok": False,
            "error_message": str(error),
            "reply": "抱歉，刚才的成长复盘结果格式异常，请再发送一次，我会继续为你处理。",
            "current_workflow": "WF-08",
            "current_status": "clarification_needed",
            "last_user_intent": safe_user_input,
            "review_status": "not_started",
            "review_draft_json": "{}",
            "review_confirmed_json": "{}",
            "next_workflow": "WF-08",
            "completed_workflow_add": "",
            "warnings_json": "[]",
        }
