# -*- coding: utf-8 -*-
import json


REQUIRED_WARNINGS = [
    "本结果为情景模拟推演，仅供参考，不能替代真实院校政策、招录数据或官方咨询",
    "推免、考试、招录、申请等规则必须以最新官方信息为准",
]
FIELDS = {
    "reply",
    "current_workflow",
    "current_status",
    "last_user_intent",
    "recommendation_status",
    "recommendation_draft",
    "recommendation_confirmed",
    "next_workflow",
    "completed_workflow_add",
    "warnings",
}
RECOMMENDATION_STATUSES = {
    "not_started",
    "awaiting_confirmation",
    "complete",
    "cancelled",
}
CURRENT_STATUSES = RECOMMENDATION_STATUSES | {"clarification_needed"}
ROUTE_NAMES = {"保研", "考研", "就业", "考公", "留学"}
LEVELS = {"高匹配", "中匹配", "待验证", "当前不建议投入"}
RESULT_FIELDS = {
    "路线",
    "primary_route",
    "alternative_routes",
    "cross_route_assets",
    "不确定性",
    "摘要",
}
ROUTE_FIELDS = {
    "姓名",
    "level",
    "证据",
    "空档",
    "priority_actions",
    "风险",
    "official_checks",
}


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


def validate_string_list(value, name, limit=5, nonempty=False):
    if not isinstance(value, list):
        raise ValueError(name + " 必须是 JSON 数组")
    if len(value) > limit:
        raise ValueError(name + " 最多保留 " + str(limit) + " 项")
    if nonempty and not value:
        raise ValueError(name + " 不能为空")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(name + " 中每一项都必须是非空字符串")


def validate_recommendation(result, name):
    if not result:
        return

    missing = RESULT_FIELDS - set(result)
    extra = set(result) - RESULT_FIELDS
    if missing:
        raise ValueError(name + " 缺少字段：" + ",".join(sorted(missing)))
    if extra:
        raise ValueError(name + " 包含未允许字段：" + ",".join(sorted(extra)))

    routes = result["路线"]
    if not isinstance(routes, list) or len(routes) != 5:
        raise ValueError(name + ".路线 必须恰好包含五项")

    seen_names = []
    for index, route in enumerate(routes):
        route_name = name + ".路线[" + str(index) + "]"
        if not isinstance(route, dict):
            raise ValueError(route_name + " 必须是 JSON 对象")
        missing_route = ROUTE_FIELDS - set(route)
        extra_route = set(route) - ROUTE_FIELDS
        if missing_route:
            raise ValueError(route_name + " 缺少字段：" + ",".join(sorted(missing_route)))
        if extra_route:
            raise ValueError(route_name + " 包含未允许字段：" + ",".join(sorted(extra_route)))
        if route["姓名"] not in ROUTE_NAMES:
            raise ValueError(route_name + ".姓名 不合法")
        if route["姓名"] in seen_names:
            raise ValueError(name + ".路线 不能重复")
        seen_names.append(route["姓名"])
        if route["level"] not in LEVELS:
            raise ValueError(route_name + ".level 不合法")
        validate_string_list(route["证据"], route_name + ".证据")
        validate_string_list(route["空档"], route_name + ".空档", limit=3)
        validate_string_list(
            route["priority_actions"],
            route_name + ".priority_actions",
            limit=3,
        )
        validate_string_list(route["风险"], route_name + ".风险")
        validate_string_list(route["official_checks"], route_name + ".official_checks")

    if set(seen_names) != ROUTE_NAMES:
        raise ValueError(name + ".路线 必须完整包含保研、考研、就业、考公、留学")

    primary = result["primary_route"]
    if primary not in ROUTE_NAMES:
        raise ValueError(name + ".primary_route 必须是五条路径之一")

    alternatives = result["alternative_routes"]
    validate_string_list(alternatives, name + ".alternative_routes", nonempty=True)
    if len(alternatives) != len(set(alternatives)):
        raise ValueError(name + ".alternative_routes 不能重复")
    if any(item not in ROUTE_NAMES for item in alternatives):
        raise ValueError(name + ".alternative_routes 只能包含五条路径名称")
    if primary in alternatives:
        raise ValueError(name + ".alternative_routes 不能包含 primary_route")

    validate_string_list(result["cross_route_assets"], name + ".cross_route_assets")
    validate_string_list(result["不确定性"], name + ".不确定性")
    if not isinstance(result["摘要"], str) or not result["摘要"].strip():
        raise ValueError(name + ".摘要 必须是非空字符串")


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

        missing = FIELDS - set(data)
        extra = set(data) - FIELDS
        if missing:
            raise ValueError("模型输出缺少字段：" + ",".join(sorted(missing)))
        if extra:
            raise ValueError("模型输出包含未允许字段：" + ",".join(sorted(extra)))

        draft = parse_object(data["recommendation_draft"], "recommendation_draft")
        confirmed = parse_object(
            data["recommendation_confirmed"],
            "recommendation_confirmed",
        )
        warnings = parse_array(data["warnings"], "warnings")

        validate_recommendation(draft, "recommendation_draft")
        validate_recommendation(confirmed, "recommendation_confirmed")

        if not isinstance(data["reply"], str) or not data["reply"].strip():
            raise ValueError("reply 必须是非空字符串")
        if data["current_workflow"] != "WF-04":
            raise ValueError("current_workflow 必须是 WF-04")
        if data["recommendation_status"] not in RECOMMENDATION_STATUSES:
            raise ValueError("recommendation_status 不合法")
        if data["current_status"] not in CURRENT_STATUSES:
            raise ValueError("current_status 不合法")
        if (
            data["current_status"] != "clarification_needed"
            and data["current_status"] != data["recommendation_status"]
        ):
            raise ValueError("非澄清状态下两个 status 必须相同")
        if data["next_workflow"] not in {"WF-04", "WF-12"}:
            raise ValueError("next_workflow 不合法")
        if data["completed_workflow_add"] not in {"", "WF-04"}:
            raise ValueError("completed_workflow_add 不合法")
        if data["last_user_intent"] != user_input:
            raise ValueError("last_user_intent 必须与 user_input 完全一致")

        validate_string_list(warnings, "warnings", limit=3)
        if len(warnings) != len(set(warnings)):
            raise ValueError("warnings 不能重复")
        for required_warning in REQUIRED_WARNINGS:
            if required_warning not in warnings:
                raise ValueError("warnings 缺少必要提示：" + required_warning)

        status = data["recommendation_status"]
        if status == "complete":
            if draft or not confirmed:
                raise ValueError("完成状态的 draft/confirmed 不合法")
            if data["next_workflow"] != "WF-12":
                raise ValueError("完成状态的 next_workflow 必须是 WF-12")
            if data["completed_workflow_add"] != "WF-04":
                raise ValueError("完成状态必须添加 WF-04 完成标记")
        elif data["completed_workflow_add"]:
            raise ValueError("只有完成状态才能添加完成标记")

        if status == "awaiting_confirmation" and not draft:
            raise ValueError("待确认状态下 recommendation_draft 不能为空")
        if status == "cancelled" and draft:
            raise ValueError("取消状态下 recommendation_draft 必须为空")
        if status != "complete" and data["next_workflow"] != "WF-04":
            raise ValueError("非完成状态的 next_workflow 必须是 WF-04")

        return {
            "parse_ok": True,
            "error_message": "",
            "reply": data["reply"].strip(),
            "current_workflow": "WF-04",
            "current_status": data["current_status"],
            "last_user_intent": data["last_user_intent"],
            "recommendation_status": status,
            "recommendation_draft_json": compact(draft),
            "recommendation_confirmed_json": compact(confirmed),
            "next_workflow": data["next_workflow"],
            "completed_workflow_add": data["completed_workflow_add"],
            "warnings_json": compact(warnings),
        }

    except Exception as error:
        safe_user_input = user_input if isinstance(user_input, str) else ""
        return {
            "parse_ok": False,
            "error_message": str(error),
            "reply": "抱歉，刚才的五路径推荐结果格式异常，请再发送一次，我会继续为你处理。",
            "current_workflow": "WF-04",
            "current_status": "clarification_needed",
            "last_user_intent": safe_user_input,
            "recommendation_status": "not_started",
            "recommendation_draft_json": "{}",
            "recommendation_confirmed_json": "{}",
            "next_workflow": "WF-04",
            "completed_workflow_add": "",
            "warnings_json": compact(REQUIRED_WARNINGS),
        }
