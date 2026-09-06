# -*- coding: utf-8 -*-
import json


TOP_FIELDS = {
    "reply", "current_workflow", "current_status", "last_user_intent",
    "trial_status", "trial_draft", "trial_confirmed", "next_workflow",
    "completed_workflow_add", "warnings",
}
STATUSES = {"not_started", "collecting", "awaiting_confirmation", "complete", "cancelled"}
DRAFT_FIELDS = {"模式", "decision_topic", "options", "分析", "试错", "摘要"}
ANALYSIS_FIELDS = {"收益", "风险", "time_cost", "economic_cost", "opportunity_cost", "可逆性", "worst_case", "exit_conditions"}
TRIAL_FIELDS = {"假设", "investment_limit", "daily_minimum_actions", "daily_logs", "day7_review", "recommended_decision"}
LOG_FIELDS = {"day", "精力", "兴趣", "完成度", "困难", "证据"}
MODES = {"decision_analysis", "seven_day_trial"}


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


def text(value, name, allow_empty=False):
    if not isinstance(value, str):
        raise ValueError(name + " 必须是字符串")
    if not allow_empty and not value.strip():
        raise ValueError(name + " 不能为空")


def string_list(value, name, minimum=0, maximum=5):
    if not isinstance(value, list) or len(value) < minimum or len(value) > maximum:
        raise ValueError(name + " 必须是 " + str(minimum) + " 到 " + str(maximum) + " 项的数组")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(name + " 每项必须是非空字符串")


def validate_analysis(value, complete):
    if not isinstance(value, dict):
        raise ValueError("分析必须是对象")
    exact(value, ANALYSIS_FIELDS, "分析")
    for field in ANALYSIS_FIELDS:
        string_list(value[field], "分析." + field, 1 if complete else 0, 5)


def validate_log(value, index):
    name = "daily_logs[" + str(index) + "]"
    if not isinstance(value, dict):
        raise ValueError(name + " 必须是对象")
    exact(value, LOG_FIELDS, name)
    if not isinstance(value["day"], int) or isinstance(value["day"], bool) or not 1 <= value["day"] <= 7:
        raise ValueError(name + ".day 必须是 1 到 7 的整数")
    for field in {"精力", "兴趣", "完成度"}:
        text(value[field], name + "." + field)
    string_list(value["困难"], name + ".困难", 0, 5)
    string_list(value["证据"], name + ".证据", 0, 5)


def validate_trial(value, complete):
    if not isinstance(value, dict):
        raise ValueError("试错必须是对象")
    exact(value, TRIAL_FIELDS, "试错")
    text(value["假设"], "试错.假设", allow_empty=not complete)
    text(value["investment_limit"], "试错.investment_limit", allow_empty=not complete)
    string_list(value["daily_minimum_actions"], "试错.daily_minimum_actions", 1 if complete else 0, 5)
    logs = value["daily_logs"]
    if not isinstance(logs, list) or len(logs) > 7:
        raise ValueError("试错.daily_logs 必须是最多 7 项的数组")
    days = []
    for index, log in enumerate(logs):
        validate_log(log, index)
        if log["day"] in days:
            raise ValueError("daily_logs.day 不能重复")
        days.append(log["day"])
    if not isinstance(value["day7_review"], dict):
        raise ValueError("试错.day7_review 必须是对象")
    text(value["recommended_decision"], "试错.recommended_decision", allow_empty=True)
    if len(logs) < 7 and value["day7_review"]:
        raise ValueError("日志不足 7 天时 day7_review 必须为空")
    if len(logs) < 7 and value["recommended_decision"].strip():
        raise ValueError("日志不足 7 天时 recommended_decision 必须为空")
    if len(logs) == 7 and value["day7_review"] and not value["recommended_decision"].strip():
        raise ValueError("完成 day7_review 时 recommended_decision 不能为空")


def validate_state(value, name, complete):
    if not isinstance(value, dict):
        raise ValueError(name + " 必须是对象")
    exact(value, DRAFT_FIELDS, name)
    if value["模式"] not in MODES and not (not complete and value["模式"] == ""):
        raise ValueError(name + ".模式不合法")
    text(value["decision_topic"], name + ".decision_topic", allow_empty=not complete)
    string_list(value["options"], name + ".options", 2 if complete and value["模式"] == "decision_analysis" else 0, 5)
    validate_analysis(value["分析"], complete and value["模式"] == "decision_analysis")
    validate_trial(value["试错"], complete and value["模式"] == "seven_day_trial")
    text(value["摘要"], name + ".摘要", allow_empty=not complete)


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

        draft = parse_object(data["trial_draft"], "trial_draft")
        confirmed = parse_object(data["trial_confirmed"], "trial_confirmed")
        warnings = parse_array(data["warnings"], "warnings")
        text(data["reply"], "reply")
        if data["current_workflow"] != "WF-10":
            raise ValueError("current_workflow 必须是 WF-10")
        status = data["trial_status"]
        if status not in STATUSES or data["current_status"] != status:
            raise ValueError("current_status 必须与合法 trial_status 一致")
        if data["last_user_intent"] != user_input:
            raise ValueError("last_user_intent 必须与 user_input 完全一致")
        if data["next_workflow"] not in {"WF-10", "WF-12"}:
            raise ValueError("next_workflow 不合法")
        if data["completed_workflow_add"] not in {"", "WF-10"}:
            raise ValueError("completed_workflow_add 不合法")
        string_list(warnings, "warnings", 0, 3)
        if len(warnings) != len(set(warnings)):
            raise ValueError("warnings 不能重复")
        if confirmed:
            validate_state(confirmed, "trial_confirmed", True)
        if draft:
            validate_state(draft, "trial_draft", status == "awaiting_confirmation")

        if status == "collecting":
            if not draft or data["next_workflow"] != "WF-10" or data["completed_workflow_add"]:
                raise ValueError("collecting 状态组合不合法")
        elif status == "awaiting_confirmation":
            if not draft:
                raise ValueError("awaiting_confirmation 必须有完整 draft")
            validate_state(draft, "trial_draft", True)
            if data["next_workflow"] != "WF-10" or data["completed_workflow_add"]:
                raise ValueError("awaiting_confirmation 路由组合不合法")
        elif status == "complete":
            if draft or not confirmed:
                raise ValueError("complete 的 draft/confirmed 组合不合法")
            if data["next_workflow"] != "WF-12" or data["completed_workflow_add"] != "WF-10":
                raise ValueError("complete 路由组合不合法")
        elif status in {"not_started", "cancelled"}:
            if draft or data["next_workflow"] != "WF-10" or data["completed_workflow_add"]:
                raise ValueError(status + " 状态组合不合法")

        return {
            "parse_ok": True,
            "error_message": "",
            "reply": data["reply"].strip(),
            "current_workflow": "WF-10",
            "current_status": status,
            "last_user_intent": data["last_user_intent"],
            "trial_status": status,
            "trial_draft_json": compact(draft),
            "trial_confirmed_json": compact(confirmed),
            "next_workflow": data["next_workflow"],
            "completed_workflow_add": data["completed_workflow_add"],
            "warnings_json": compact(warnings),
        }
    except Exception as error:
        safe_input = user_input if isinstance(user_input, str) else ""
        return {
            "parse_ok": False,
            "error_message": str(error),
            "reply": "抱歉，刚才的决策分析结果格式异常，请再发送一次，我会继续为你处理。",
            "current_workflow": "WF-10",
            "current_status": "collecting",
            "last_user_intent": safe_input,
            "trial_status": "collecting",
            "trial_draft_json": "{}",
            "trial_confirmed_json": "{}",
            "next_workflow": "WF-10",
            "completed_workflow_add": "",
            "warnings_json": "[]",
        }
