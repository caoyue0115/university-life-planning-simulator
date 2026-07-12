"""Render the first Mermaid flowchart in each workflow guide as a PNG.

The renderer supports the small flowchart subset used by this repository and
keeps image generation deterministic without requiring a browser or Mermaid CLI.
"""

from __future__ import annotations

import re
from collections import defaultdict, deque
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / "docs" / "workflows"
FONT_PATH = Path(r"C:\Windows\Fonts\msyh.ttc")
FONT = ImageFont.truetype(str(FONT_PATH), 22)
SMALL = ImageFont.truetype(str(FONT_PATH), 17)

NODE_PATTERN = re.compile(r"\b([A-Za-z][A-Za-z0-9_]*)\s*(\{[^}]+\}|\[[^]]+\]|\([^)]*\))")
EDGE_PATTERN = re.compile(
    r"(?=([A-Za-z][A-Za-z0-9_]*)\s*(?:-->(?:\|([^|]+)\|)?|--\s*([^\-]+?)\s*-->)\s*([A-Za-z][A-Za-z0-9_]*))"
)


def clean_label(shape: str) -> tuple[str, str]:
    if shape.startswith("{"):
        return shape[1:-1], "decision"
    return shape[1:-1], "process"


def parse_flowchart(source: str):
    nodes: dict[str, tuple[str, str]] = {}
    edges: list[tuple[str, str, str]] = []
    for line in source.splitlines():
        line = line.strip()
        if not line or line.startswith(("flowchart", "graph", "%%")):
            continue
        for node_id, shape in NODE_PATTERN.findall(line):
            nodes[node_id] = clean_label(shape)
        edge_line = NODE_PATTERN.sub(lambda match: match.group(1), line)
        for start, pipe_label, arrow_label, end in EDGE_PATTERN.findall(edge_line):
            label = pipe_label or arrow_label
            edges.append((start, end, label.strip()))
            nodes.setdefault(start, (start, "process"))
            nodes.setdefault(end, (end, "process"))
    return nodes, edges


def assign_ranks(nodes, edges):
    incoming = defaultdict(int)
    outgoing = defaultdict(list)
    for start, end, _ in edges:
        outgoing[start].append(end)
        incoming[end] += 1
    roots = [node for node in nodes if incoming[node] == 0] or [next(iter(nodes))]
    rank = {node: 0 for node in roots}
    queue = deque(roots)
    visits = defaultdict(int)
    while queue:
        node = queue.popleft()
        for child in outgoing[node]:
            proposed = min(rank[node] + 1, len(nodes))
            if proposed > rank.get(child, -1):
                rank[child] = proposed
            visits[child] += 1
            if visits[child] <= len(nodes):
                queue.append(child)
    for node in nodes:
        rank.setdefault(node, 0)
    # Collapse runaway ranks caused by intentional feedback arrows.
    ordered = sorted(set(rank.values()))
    remap = {value: index for index, value in enumerate(ordered)}
    return {node: remap[value] for node, value in rank.items()}


def wrapped(text: str, width: int = 14) -> str:
    return "\n".join(text[i : i + width] for i in range(0, len(text), width))


def render(nodes, edges, output: Path):
    ranks = assign_ranks(nodes, edges)
    levels = defaultdict(list)
    for node, level in ranks.items():
        levels[level].append(node)
    max_columns = max(len(group) for group in levels.values())
    node_w, node_h = 260, 92
    gap_x, gap_y = 70, 105
    margin = 70
    width = max(1100, margin * 2 + max_columns * node_w + (max_columns - 1) * gap_x)
    height = margin * 2 + (max(levels) + 1) * node_h + max(levels) * gap_y
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    positions = {}

    for level in sorted(levels):
        group = levels[level]
        total = len(group) * node_w + (len(group) - 1) * gap_x
        start_x = (width - total) // 2
        y = margin + level * (node_h + gap_y)
        for index, node in enumerate(group):
            x = start_x + index * (node_w + gap_x)
            positions[node] = (x, y)

    # Draw edges first so nodes remain legible.
    for start, end, label in edges:
        if start not in positions or end not in positions:
            continue
        sx, sy = positions[start]
        ex, ey = positions[end]
        p1 = (sx + node_w // 2, sy + node_h)
        p4 = (ex + node_w // 2, ey)
        mid_y = (p1[1] + p4[1]) // 2
        points = [p1, (p1[0], mid_y), (p4[0], mid_y), p4]
        draw.line(points, fill="#64748b", width=3, joint="curve")
        draw.polygon([(p4[0], p4[1]), (p4[0] - 8, p4[1] - 13), (p4[0] + 8, p4[1] - 13)], fill="#64748b")
        if label:
            box = draw.textbbox((0, 0), label, font=SMALL)
            tx = (p1[0] + p4[0]) // 2 - (box[2] - box[0]) // 2
            ty = mid_y - 24
            draw.rounded_rectangle((tx - 6, ty - 3, tx + box[2] - box[0] + 6, ty + 24), 5, fill="#ffffff")
            draw.text((tx, ty), label, fill="#334155", font=SMALL)

    for node, (label, kind) in nodes.items():
        x, y = positions[node]
        if kind == "decision":
            polygon = [(x + node_w // 2, y), (x + node_w, y + node_h // 2), (x + node_w // 2, y + node_h), (x, y + node_h // 2)]
            draw.polygon(polygon, fill="#ecfeff", outline="#0891b2", width=3)
        else:
            draw.rounded_rectangle((x, y, x + node_w, y + node_h), 14, fill="#eef2ff", outline="#6366f1", width=3)
        text = wrapped(label)
        box = draw.multiline_textbbox((0, 0), text, font=FONT, spacing=5, align="center")
        tx = x + (node_w - (box[2] - box[0])) // 2
        ty = y + (node_h - (box[3] - box[1])) // 2 - 2
        draw.multiline_text((tx, ty), text, fill="#1f2937", font=FONT, spacing=5, align="center")

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, "PNG", optimize=True)


def main():
    files = sorted([WORKFLOWS / "README.md", *WORKFLOWS.glob("WF-??-*.md")])
    for markdown_path in files:
        text = markdown_path.read_text(encoding="utf-8")
        mermaid = re.search(r"```mermaid\s*\n([\s\S]*?)```", text)
        image_ref = re.search(r"!\[[^]]*\]\((images/[^)]+\.png)\)", text)
        if not mermaid or not image_ref:
            raise RuntimeError(f"{markdown_path.name}: missing Mermaid block or PNG reference")
        nodes, edges = parse_flowchart(mermaid.group(1))
        if not nodes or not edges:
            raise RuntimeError(f"{markdown_path.name}: diagram has no nodes or edges")
        output = WORKFLOWS / image_ref.group(1)
        render(nodes, edges, output)
        print(f"{markdown_path.name} -> {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
