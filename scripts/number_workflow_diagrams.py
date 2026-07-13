from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / "docs" / "workflows"
NODE = re.compile(r"\b([A-Za-z][A-Za-z0-9_]*)\s*(\{[^}]+\}|\[[^]]+\]|\([^)]*\))")


def number_block(block: str) -> str:
    assigned: dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        node_id, shape = match.groups()
        if node_id not in assigned:
            assigned[node_id] = f"N{len(assigned):02d}"
        number = assigned[node_id]
        opener, closer = shape[0], shape[-1]
        label = shape[1:-1]
        quote = '"' if label.startswith('"') and label.endswith('"') else ""
        if quote:
            label = label[1:-1]
        label = re.sub(r"^N\d{2}\s+", "", label)
        updated = f"{number} {label}"
        return f"{node_id}{opener}{quote}{updated}{quote}{closer}"

    return NODE.sub(replace, block)


def main() -> None:
    paths = sorted(WORKFLOWS.glob("WF-0[2-9]-*.md")) + sorted(WORKFLOWS.glob("WF-1[0-2]-*.md"))
    for path in paths:
        text = path.read_text(encoding="utf-8")
        text, count = re.subn(
            r"```mermaid\s*\n([\s\S]*?)```",
            lambda match: "```mermaid\n" + number_block(match.group(1)) + "```",
            text,
            count=1,
        )
        if count != 1:
            raise RuntimeError(f"{path.name}: expected one primary Mermaid block")
        path.write_text(text, encoding="utf-8")
        print(path.name)


if __name__ == "__main__":
    main()
