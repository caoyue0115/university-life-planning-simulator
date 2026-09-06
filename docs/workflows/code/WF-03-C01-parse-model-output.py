# -*- coding: utf-8 -*-
import json

REQUIRED_WARNING = "这是行为倾向信号，不是人格或职业定论"
FIELDS = {"reply", "current_workflow", "current_status", "last_user_intent", "adventure_status", "adventure_draft", "adventure_confirmed", "next_workflow", "completed_workflow_add", "warnings"}
ADVENTURE_STATUSES = {"not_started", "collecting", "awaiting_confirmation", "complete", "cancelled"}
CURRENT_STATUSES = ADVENTURE_STATUSES | {"clarification_needed"}

def parse_object(value, name):
    if isinstance(value, str): value = json.loads(value)
    if not isinstance(value, dict): raise ValueError(name + " 必须是 JSON 对象")
    return value

def parse_array(value, name):
    if isinstance(value, str): value = json.loads(value)
    if not isinstance(value, list): raise ValueError(name + " 必须是 JSON 数组")
    return value

def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

def main(model_output, user_input):
    try:
        if not isinstance(model_output, str): raise ValueError("model_output 必须是字符串")
        if not isinstance(user_input, str): raise ValueError("user_input 必须是字符串")
        text = model_output.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].strip().startswith("```"): lines = lines[1:]
            if lines and lines[-1].strip() == "```": lines = lines[:-1]
            text = "\n".join(lines).strip()
        data = json.loads(text)
        if not isinstance(data, dict): raise ValueError("模型输出顶层必须是 JSON 对象")
        missing, extra = FIELDS - set(data), set(data) - FIELDS
        if missing: raise ValueError("模型输出缺少字段：" + ",".join(sorted(missing)))
        if extra: raise ValueError("模型输出包含未允许字段：" + ",".join(sorted(extra)))
        draft = parse_object(data["adventure_draft"], "adventure_draft")
        confirmed = parse_object(data["adventure_confirmed"], "adventure_confirmed")
        warnings = parse_array(data["warnings"], "warnings")
        if not isinstance(data["reply"], str) or not data["reply"].strip(): raise ValueError("reply 必须是非空字符串")
        if data["current_workflow"] != "WF-03": raise ValueError("current_workflow 必须是 WF-03")
        if data["adventure_status"] not in ADVENTURE_STATUSES: raise ValueError("adventure_status 不合法")
        if data["current_status"] not in CURRENT_STATUSES: raise ValueError("current_status 不合法")
        if data["current_status"] != "clarification_needed" and data["current_status"] != data["adventure_status"]: raise ValueError("非澄清状态下两个 status 必须相同")
        if data["next_workflow"] not in {"WF-03", "WF-12"}: raise ValueError("next_workflow 不合法")
        if data["completed_workflow_add"] not in {"", "WF-03"}: raise ValueError("completed_workflow_add 不合法")
        if data["last_user_intent"] != user_input: raise ValueError("last_user_intent 必须与 user_input 完全一致")
        if len(warnings) > 3 or any(not isinstance(x, str) for x in warnings): raise ValueError("warnings 类型或数量不合法")
        if len(warnings) != len(set(warnings)): raise ValueError("warnings 不能重复")
        if REQUIRED_WARNING not in warnings: raise ValueError("warnings 缺少必要提示")
        if data["adventure_status"] == "complete":
            if draft or not confirmed: raise ValueError("完成状态的 draft/confirmed 不合法")
            if data["next_workflow"] != "WF-12" or data["completed_workflow_add"] != "WF-03": raise ValueError("完成状态的路由字段不合法")
        elif data["completed_workflow_add"]: raise ValueError("只有完成状态才能添加完成标记")
        if data["adventure_status"] == "awaiting_confirmation" and not draft: raise ValueError("待确认状态下 draft 不能为空")
        if data["adventure_status"] == "cancelled" and draft: raise ValueError("取消状态下 draft 必须为空")
        return {"parse_ok": True, "error_message": "", "reply": data["reply"].strip(), "current_workflow": "WF-03", "current_status": data["current_status"], "last_user_intent": data["last_user_intent"], "adventure_status": data["adventure_status"], "adventure_draft_json": compact(draft), "adventure_confirmed_json": compact(confirmed), "next_workflow": data["next_workflow"], "completed_workflow_add": data["completed_workflow_add"], "warnings_json": compact(warnings)}
    except Exception as error:
        return {"parse_ok": False, "error_message": str(error), "reply": "抱歉，刚才的生存大冒险处理结果格式异常，请再发送一次，我会继续为你处理。", "current_workflow": "WF-03", "current_status": "clarification_needed", "last_user_intent": user_input if isinstance(user_input, str) else "", "adventure_status": "not_started", "adventure_draft_json": "{}", "adventure_confirmed_json": "{}", "next_workflow": "WF-03", "completed_workflow_add": "", "warnings_json": compact([REQUIRED_WARNING])}
