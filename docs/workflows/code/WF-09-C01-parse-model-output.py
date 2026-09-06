# -*- coding: utf-8 -*-
import json


TOP_FIELDS = {
    "reply", "current_workflow", "current_status", "last_user_intent",
    "asset_status", "asset_draft", "asset_confirmed", "next_workflow",
    "completed_workflow_add", "warnings",
}
STATUSES = {"not_started", "collecting", "awaiting_confirmation", "complete", "cancelled"}
DRAFT_FIELDS = {"pending_entry", "existing_entries", "摘要"}
CONFIRMED_FIELDS = {"entries", "摘要"}
ENTRY_FIELDS = {
    "entry_id", "entry_type", "背景", "目标", "角色", "动作", "工具", "结果",
    "指标", "evidence_locations", "resume_bullet", "detailed_story",
    "quality_status", "missing_fields",
}
ENTRY_TYPES = {"课程项目", "科研", "竞赛", "实习", "社团", "学生工作", "志愿服务", "其他"}
QUALITY_STATUSES = {"可直接使用", "缺少量化结果", "缺少证明材料", "需要打磨"}
ARRAY_FIELDS = {"动作", "工具", "结果", "指标", "evidence_locations", "missing_fields"}


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


def exact_fields(value, expected, name):
    missing = expected - set(value)
    extra = set(value) - expected
    if missing:
        raise ValueError(name + " 缺少字段：" + ",".join(sorted(missing)))
    if extra:
        raise ValueError(name + " 包含未允许字段：" + ",".join(sorted(extra)))


def string_value(value, name, allow_empty=False):
    if not isinstance(value, str):
        raise ValueError(name + " 必须是字符串")
    if not allow_empty and not value.strip():
        raise ValueError(name + " 不能为空")


def string_list(value, name, minimum=0, maximum=5):
    if not isinstance(value, list):
        raise ValueError(name + " 必须是 JSON 数组")
    if len(value) < minimum or len(value) > maximum:
        raise ValueError(name + " 项数必须在 " + str(minimum) + " 到 " + str(maximum) + " 之间")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(name + " 中每一项都必须是非空字符串")


def validate_entry(entry, name, require_complete):
    if not isinstance(entry, dict):
        raise ValueError(name + " 必须是对象")
    exact_fields(entry, ENTRY_FIELDS, name)

    for field in {"entry_id", "entry_type", "背景", "目标", "角色", "resume_bullet", "detailed_story", "quality_status"}:
        string_value(entry[field], name + "." + field, allow_empty=not require_complete)
    for field in ARRAY_FIELDS:
        string_list(entry[field], name + "." + field, minimum=1 if require_complete and field == "动作" else 0)

    if entry["entry_type"] and entry["entry_type"] not in ENTRY_TYPES:
        raise ValueError(name + ".entry_type 不合法")
    if entry["quality_status"] and entry["quality_status"] not in QUALITY_STATUSES:
        raise ValueError(name + ".quality_status 不合法")
    if require_complete:
        if not entry["entry_id"].strip().startswith("R"):
            raise ValueError(name + ".entry_id 必须使用 R 编号")
        if not (entry["背景"].strip() or entry["目标"].strip()):
            raise ValueError(name + " 必须至少提供背景或目标")
        if not entry["角色"].strip():
            raise ValueError(name + ".角色不能为空")
        if not entry["evidence_locations"] and entry["quality_status"] != "缺少证明材料":
            raise ValueError(name + " 无证明位置时 quality_status 必须为缺少证明材料")
        if entry["evidence_locations"] and not entry["指标"] and entry["quality_status"] == "可直接使用":
            raise ValueError(name + " 无量化结果时不能标记为可直接使用")


def validate_confirmed(confirmed):
    if not confirmed:
        return []
    exact_fields(confirmed, CONFIRMED_FIELDS, "asset_confirmed")
    entries = confirmed["entries"]
    if not isinstance(entries, list) or len(entries) > 5:
        raise ValueError("asset_confirmed.entries 必须是最多 5 项的数组")
    ids = []
    for index, entry in enumerate(entries):
        validate_entry(entry, "asset_confirmed.entries[" + str(index) + "]", True)
        if entry["entry_id"] in ids:
            raise ValueError("asset_confirmed.entries 中 entry_id 不能重复")
        ids.append(entry["entry_id"])
    string_value(confirmed["摘要"], "asset_confirmed.摘要", allow_empty=len(entries) == 0)
    return ids


def validate_draft(draft, status, confirmed_ids):
    if not draft:
        return
    exact_fields(draft, DRAFT_FIELDS, "asset_draft")
    pending = draft["pending_entry"]
    if not isinstance(pending, dict) or not pending:
        raise ValueError("asset_draft.pending_entry 必须是非空对象")
    validate_entry(pending, "asset_draft.pending_entry", status == "awaiting_confirmation")
    if pending["entry_id"] and pending["entry_id"] in confirmed_ids:
        raise ValueError("pending_entry.entry_id 与已确认条目重复")

    existing = draft["existing_entries"]
    if not isinstance(existing, list) or len(existing) > 5:
        raise ValueError("asset_draft.existing_entries 必须是最多 5 项的数组")
    for index, entry in enumerate(existing):
        validate_entry(entry, "asset_draft.existing_entries[" + str(index) + "]", True)
    string_value(draft["摘要"], "asset_draft.摘要")


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
        exact_fields(data, TOP_FIELDS, "模型输出")

        draft = parse_object(data["asset_draft"], "asset_draft")
        confirmed = parse_object(data["asset_confirmed"], "asset_confirmed")
        warnings = parse_array(data["warnings"], "warnings")

        string_value(data["reply"], "reply")
        if data["current_workflow"] != "WF-09":
            raise ValueError("current_workflow 必须是 WF-09")
        if data["asset_status"] not in STATUSES or data["current_status"] not in STATUSES:
            raise ValueError("status 不合法")
        if data["current_status"] != data["asset_status"]:
            raise ValueError("current_status 必须与 asset_status 一致")
        if data["next_workflow"] not in {"WF-09", "WF-12"}:
            raise ValueError("next_workflow 不合法")
        if data["completed_workflow_add"] not in {"", "WF-09"}:
            raise ValueError("completed_workflow_add 不合法")
        if data["last_user_intent"] != user_input:
            raise ValueError("last_user_intent 必须与 user_input 完全一致")
        string_list(warnings, "warnings", 0, 3)
        if len(warnings) != len(set(warnings)):
            raise ValueError("warnings 不能重复")

        confirmed_ids = validate_confirmed(confirmed)
        status = data["asset_status"]
        if draft:
            validate_draft(draft, status, confirmed_ids)

        if status == "collecting":
            if not draft:
                raise ValueError("collecting 状态下 asset_draft 不能为空")
            if data["next_workflow"] != "WF-09" or data["completed_workflow_add"]:
                raise ValueError("collecting 状态的路由组合不合法")
        elif status == "awaiting_confirmation":
            if not draft:
                raise ValueError("待确认状态下 asset_draft 不能为空")
            validate_draft(draft, status, confirmed_ids)
            if data["next_workflow"] != "WF-09" or data["completed_workflow_add"]:
                raise ValueError("待确认状态的路由组合不合法")
        elif status == "complete":
            if draft or not confirmed or not confirmed.get("entries"):
                raise ValueError("完成状态的 draft/confirmed 不合法")
            if data["next_workflow"] != "WF-12" or data["completed_workflow_add"] != "WF-09":
                raise ValueError("完成状态的路由组合不合法")
        elif status in {"not_started", "cancelled"}:
            if draft:
                raise ValueError(status + " 状态下 asset_draft 必须为空")
            if data["next_workflow"] != "WF-09" or data["completed_workflow_add"]:
                raise ValueError(status + " 状态的路由组合不合法")

        return {
            "parse_ok": True,
            "error_message": "",
            "reply": data["reply"].strip(),
            "current_workflow": "WF-09",
            "current_status": status,
            "last_user_intent": data["last_user_intent"],
            "asset_status": status,
            "asset_draft_json": compact(draft),
            "asset_confirmed_json": compact(confirmed),
            "next_workflow": data["next_workflow"],
            "completed_workflow_add": data["completed_workflow_add"],
            "warnings_json": compact(warnings),
        }
    except Exception as error:
        safe_user_input = user_input if isinstance(user_input, str) else ""
        return {
            "parse_ok": False,
            "error_message": str(error),
            "reply": "抱歉，刚才的履历素材结果格式异常，请再发送一次，我会继续为你处理。",
            "current_workflow": "WF-09",
            "current_status": "collecting",
            "last_user_intent": safe_user_input,
            "asset_status": "collecting",
            "asset_draft_json": "{}",
            "asset_confirmed_json": "{}",
            "next_workflow": "WF-09",
            "completed_workflow_add": "",
            "warnings_json": "[]",
        }
