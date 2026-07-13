from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

from render_workflow_diagrams import parse_flowchart


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / "docs" / "workflows"


def main() -> int:
    errors: list[str] = []
    files = sorted(WORKFLOWS.glob("WF-??-*.md"))
    for path in files:
        text = path.read_text(encoding="utf-8")
        if "```javascript" in text or re.search(r"\b(const|let)\s+\w+\s*=", text):
            errors.append(f"{path.name}: contains JavaScript; code nodes support Python only")
        if "以当前编辑器显示为准" in text:
            errors.append(f"{path.name}: contains vague UI placeholder")
        for block_index, source in enumerate(re.findall(r"```python\s*\n([\s\S]*?)```", text), start=1):
            try:
                compile(source, f"{path.name}:python-{block_index}", "exec")
            except SyntaxError as exc:
                errors.append(
                    f"{path.name}: Python block {block_index} has syntax error on line {exc.lineno}: {exc.msg}"
                )
        mermaids = re.findall(r"```mermaid\s*\n([\s\S]*?)```", text)
        images = re.findall(r"!\[[^]]*\]\((images/[^)]+\.png)\)", text)
        if not mermaids or len(mermaids) != len(images):
            errors.append(
                f"{path.name}: Mermaid/image mismatch ({len(mermaids)} blocks/{len(images)} images)"
            )
        for image in images:
            if not (WORKFLOWS / image).exists():
                errors.append(f"{path.name}: missing image {image}")
        for diagram_index, diagram in enumerate(mermaids, start=1):
            message_ids = set(re.findall(r'\b([A-Za-z]\w*)\[["\']?[^\]\n]*消息', diagram))
            edge_text = re.sub(
                r"\b([A-Za-z][A-Za-z0-9_]*)\s*(?:\{[^}]+\}|\[[^]]+\]|\([^)]*\))",
                lambda match: match.group(1),
                diagram,
            )
            for node_id in message_ids:
                if not re.search(rf"\b{re.escape(node_id)}\s*(?:-->|--[^\n]*-->)", edge_text):
                    errors.append(
                        f"{path.name} diagram {diagram_index}: message {node_id} has no outgoing edge"
                    )
        # Aggregate split diagrams before checking branch completeness.  This
        # allows a shared router (for example WF-10) to show one route per image
        # while still requiring at least two explicit routes overall.
        decision_routes: dict[str, set[tuple[str, str]]] = defaultdict(set)
        for diagram in mermaids:
            nodes, edges = parse_flowchart(diagram)
            for source, target, label in edges:
                if source in nodes and nodes[source][1] == "decision":
                    decision_routes[source].add((target, label))
        for node_id, routes in decision_routes.items():
            if len(routes) < 2:
                errors.append(f"{path.name}: brancher {node_id} has fewer than two outgoing routes")
        if "## 节点逐项配置" not in text and path.name != "WF-01-user-profile.md":
            errors.append(f"{path.name}: missing '节点逐项配置' section")

    if errors:
        print("\n".join(f"ERROR: {item}" for item in errors))
        return 1
    print(f"PASS: validated {len(files)} workflow guides")
    return 0


if __name__ == "__main__":
    sys.exit(main())
