# -*- coding: utf-8 -*-
import json


FIELDS = {
    "reply",
    "current_workflow",
    "current_status",
    "last_user_intent",
    "plan_status",
    "plan_draft",
    "plan_confirmed",
    "next_workflow",
    "completed_workflow_add",
    "warnings",
}
PLAN_STATUSES = {
    "not_started",
    "collecting",
    "awaiting_confirmation",
    "complete",
    "cancelled",
}
CURRENT_STATUSES = PLAN_STATUSES | {"clarification_needed"}
PLAN_FIELDS = {
    "selected_route",
    "alternative_route",
    "target_route",
    "planning_horizon",
    "semester_goals",
    "next_four_weeks",
    "decision_points",
    "摘要",
}
GOAL_FIELDS = {
    "学期",
    "进球",
    "success_criteria",
    "monthly_milestones",
    "资源",
    "风险",
    "后备",
    "not_to_do",
}
WEEK_FIELDS = {"week", "actions", "evidence"}


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


def validate_collecting_plan(plan, name):
    validate_exact_fields(plan, PLAN_FIELDS, name)
    validate_string(plan["selected_route"], name + ".selected_route", allow_empty=True)
    validate_string(plan["alternative_route"], name + ".alternative_route", allow_empty=True)
    validate_string(plan["target_route"], name + ".target_route", allow_empty=True)
    validate_string(plan["planning_horizon"], name + ".planning_horizon", allow_empty=True)
    if plan["semester_goals"] != []:
        raise ValueError(name + ".semester_goals 在 collecting 状态下必须为空数组")
    if plan["next_four_weeks"] != []:
        raise ValueError(name + ".next_four_weeks 在 collecting 状态下必须为空数组")
    validate_string_list(plan["decision_points"], name + ".decision_points")
    validate_string(plan["摘要"], name + ".摘要")


def validate_full_plan(plan, name):
    validate_exact_fields(plan, PLAN_FIELDS, name)
    validate_string(plan["selected_route"], name + ".selected_route")
    validate_string(plan["alternative_route"], name + ".alternative_route")
    validate_string(plan["target_route"], name + ".target_route")
    validate_string(plan["planning_horizon"], name + ".planning_horizon")
    validate_string(plan["摘要"], name + ".摘要")
    validate_string_list(plan["decision_points"], name + ".decision_points")

    goals = plan["semester_goals"]
    if not isinstance(goals, list) or len(goals) not in {3, 4}:
        raise ValueError(name + ".semester_goals 必须包含 3 到 4 个核心目标")
    for index, goal in enumerate(goals):
        goal_name = name + ".semester_goals[" + str(index) + "]"
        if not isinstance(goal, dict):
            raise ValueError(goal_name + " 必须是 JSON 对象")
        validate_exact_fields(goal, GOAL_FIELDS, goal_name)
        validate_string(goal["学期"], goal_name + ".学期")
        validate_string(goal["进球"], goal_name + ".进球")
        validate_string_list(goal["success_criteria"], goal_name + ".success_criteria", 1)
        validate_string_list(
            goal["monthly_milestones"],
            goal_name + ".monthly_milestones",
            1,
        )
        validate_string_list(goal["资源"], goal_name + ".资源", 1)
        validate_string_list(goal["风险"], goal_name + ".风险", 1)
        validate_string_list(goal["后备"], goal_name + ".后备", 1)
        validate_string_list(goal["not_to_do"], goal_name + ".not_to_do", 1)

    weeks = plan["next_four_weeks"]
    if not isinstance(weeks, list) or len(weeks) != 4:
        raise ValueError(name + ".next_four_weeks 必须恰好包含四周")
    seen_weeks = []
    for index, week in enumerate(weeks):
        week_name = name + ".next_four_weeks[" + str(index) + "]"
        if not isinstance(week, dict):
            raise ValueError(week_name + " 必须是 JSON 对象")
        validate_exact_fields(week, WEEK_FIELDS, week_name)
        if not isinstance(week["week"], int) or isinstance(week["week"], bool):
            raise ValueError(week_name + ".week 必须是整数")
        if week["week"] not in {1, 2, 3, 4}:
            raise ValueError(week_name + ".week 只能是 1、2、3、4")
        if week["week"] in seen_weeks:
            raise ValueError(name + ".next_four_weeks 周次不能重复")
        seen_weeks.append(week["week"])
        validate_string_list(week["actions"], week_name + ".actions", 1, 3)
        validate_string_list(week["evidence"], week_name + ".evidence", 1, 3)
    if set(seen_weeks) != {1, 2, 3, 4}:
        raise ValueError(name + ".next_four_weeks 必须完整包含 week 1 到 4")


def validate_plan_by_status(plan, name, status):
    if not plan:
        return
    if status == "collecting":
        validate_collecting_plan(plan, name)
    else:
        validate_full_plan(plan, name)


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

        draft = parse_object(data["plan_draft"], "plan_draft")
        confirmed = parse_object(data["plan_confirmed"], "plan_confirmed")
        warnings = parse_array(data["warnings"], "warnings")

        validate_string(data["reply"], "reply")
        if data["current_workflow"] != "WF-06":
            raise ValueError("current_workflow 必须是 WF-06")
        if data["plan_status"] not in PLAN_STATUSES:
            raise ValueError("plan_status 不合法")
        if data["current_status"] not in CURRENT_STATUSES:
            raise ValueError("current_status 不合法")
        if (
            data["current_status"] != "clarification_needed"
            and data["current_status"] != data["plan_status"]
        ):
            raise ValueError("非澄清状态下两个 status 必须相同")
        if data["next_workflow"] not in {"WF-06", "WF-12"}:
            raise ValueError("next_workflow 不合法")
        if data["completed_workflow_add"] not in {"", "WF-06"}:
            raise ValueError("completed_workflow_add 不合法")
        if data["last_user_intent"] != user_input:
            raise ValueError("last_user_intent 必须与 user_input 完全一致")
        validate_string_list(warnings, "warnings", 0, 3)
        if len(warnings) != len(set(warnings)):
            raise ValueError("warnings 不能重复")

        status = data["plan_status"]
        validate_plan_by_status(draft, "plan_draft", status)
        if confirmed:
            validate_full_plan(confirmed, "plan_confirmed")

        if status == "collecting" and not draft:
            raise ValueError("collecting 状态下 plan_draft 不能为空")
        if status == "awaiting_confirmation":
            if not draft:
                raise ValueError("待确认状态下 plan_draft 不能为空")
            validate_full_plan(draft, "plan_draft")
        if status == "complete":
            if draft or not confirmed:
                raise ValueError("完成状态的 draft/confirmed 不合法")
            if data["next_workflow"] != "WF-12":
                raise ValueError("完成状态的 next_workflow 必须是 WF-12")
            if data["completed_workflow_add"] != "WF-06":
                raise ValueError("完成状态必须添加 WF-06 完成标记")
        elif data["completed_workflow_add"]:
            raise ValueError("只有完成状态才能添加完成标记")
        if status == "cancelled" and draft:
            raise ValueError("取消状态下 plan_draft 必须为空")
        if status == "not_started" and draft:
            raise ValueError("not_started 状态下 plan_draft 必须为空")
        if status != "complete" and data["next_workflow"] != "WF-06":
            raise ValueError("非完成状态的 next_workflow 必须是 WF-06")

        return {
            "parse_ok": True,
            "error_message": "",
            "reply": data["reply"].strip(),
            "current_workflow": "WF-06",
            "current_status": data["current_status"],
            "last_user_intent": data["last_user_intent"],
            "plan_status": status,
            "plan_draft_json": compact(draft),
            "plan_confirmed_json": compact(confirmed),
            "next_workflow": data["next_workflow"],
            "completed_workflow_add": data["completed_workflow_add"],
            "warnings_json": compact(warnings),
        }

    except Exception as error:
        safe_user_input = user_input if isinstance(user_input, str) else ""
        return {
            "parse_ok": False,
            "error_message": str(error),
            "reply": "抱歉，刚才的主规划结果格式异常，请再发送一次，我会继续为你处理。",
            "current_workflow": "WF-06",
            "current_status": "clarification_needed",
            "last_user_intent": safe_user_input,
            "plan_status": "not_started",
            "plan_draft_json": "{}",
            "plan_confirmed_json": "{}",
            "next_workflow": "WF-06",
            "completed_workflow_add": "",
            "warnings_json": "[]",
        }
