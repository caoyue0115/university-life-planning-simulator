# -*- coding: utf-8 -*-
import ast
import json


def parse_value(value):
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return value
    try:
        return json.loads(text)
    except Exception:
        try:
            return ast.literal_eval(text)
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

        clean_completed = []
        for item in completed:
            if isinstance(item, str):
                item = item.strip()
                if item and item not in clean_completed:
                    clean_completed.append(item)

        workflow_to_add = completed_workflow_add
        if isinstance(workflow_to_add, str):
            workflow_to_add = workflow_to_add.strip()
        if workflow_to_add not in {"", "WF-04"}:
            raise ValueError("completed_workflow_add 只能为空或 WF-04")
        if workflow_to_add and workflow_to_add not in clean_completed:
            clean_completed.append(workflow_to_add)

        raw_version = parse_value(row.get("state_version", 1))
        try:
            state_version = int(raw_version)
        except Exception:
            state_version = 1

        return {
            "merge_ok": True,
            "error_message": "",
            "completed_workflows_json": json.dumps(
                clean_completed,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            "state_version_next": state_version + 1,
        }

    except Exception as error:
        raise RuntimeError("路由状态合并失败：" + str(error))
