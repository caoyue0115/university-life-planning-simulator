# -*- coding: utf-8 -*-
import ast
import json


def parse_value(value):
    if not isinstance(value, str):
        return value
    value = value.strip()
    if not value:
        return value
    try:
        return json.loads(value)
    except Exception:
        try:
            return ast.literal_eval(value)
        except Exception:
            return value


def main(route_state_rows, completed_workflow_add):
    try:
        rows = parse_value(route_state_rows)
        if isinstance(rows, dict):
            rows = [rows]
        if not isinstance(rows, list) or not rows:
            raise ValueError("route_state_rows 中没有有效路由记录")
        row = parse_value(rows[0])
        if not isinstance(row, dict):
            raise ValueError("路由记录必须是对象")
        completed = parse_value(row.get("completed_workflows", []))
        if completed in (None, ""):
            completed = []
        if not isinstance(completed, list):
            raise ValueError("completed_workflows 必须是 JSON 数组")
        clean = []
        for item in completed:
            if isinstance(item, str) and item.strip() and item.strip() not in clean:
                clean.append(item.strip())
        addition = completed_workflow_add.strip() if isinstance(completed_workflow_add, str) else completed_workflow_add
        if addition not in {"", "WF-11"}:
            raise ValueError("completed_workflow_add 只能为空或 WF-11")
        if addition and addition not in clean:
            clean.append(addition)
        try:
            version = int(parse_value(row.get("state_version", 1)))
        except Exception:
            version = 1
        return {
            "merge_ok": True,
            "error_message": "",
            "completed_workflows_json": json.dumps(clean, ensure_ascii=False, separators=(",", ":")),
            "state_version_next": version + 1,
        }
    except Exception as error:
        raise RuntimeError("路由状态合并失败：" + str(error))
