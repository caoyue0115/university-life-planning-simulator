"""Repack generated field rows into byte-preserved copies of the platform template."""

from __future__ import annotations

from copy import copy
from html import escape
from pathlib import Path
from tempfile import NamedTemporaryFile
from xml.etree import ElementTree as ET
from zipfile import ZipFile
import os
import re


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = Path(r"D:\DB_TABLE_导入模板.xlsx")
OUTPUT_DIR = ROOT / "docs" / "database" / "import-templates"
SOURCE_DIR = Path(os.environ.get("DB_SOURCE_DIR", str(ROOT / ".tmp-artifact-templates")))
SHEET = "xl/worksheets/sheet1.xml"
NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def shared_strings(workbook: ZipFile) -> list[str]:
    name = "xl/sharedStrings.xml"
    if name not in workbook.namelist():
        return []
    root = ET.fromstring(workbook.read(name))
    values = []
    for item in root.findall("x:si", NS):
        values.append("".join(node.text or "" for node in item.iterfind(".//x:t", NS)))
    return values


def read_rows(file: Path) -> list[list[str]]:
    with ZipFile(file) as workbook:
        strings = shared_strings(workbook)
        root = ET.fromstring(workbook.read(SHEET))
        rows = []
        for row in root.findall(".//x:sheetData/x:row", NS):
            if int(row.attrib["r"]) == 1:
                continue
            values = [""] * 5
            for cell in row.findall("x:c", NS):
                ref = cell.attrib.get("r", "A1")
                column = ord(ref[0].upper()) - ord("A")
                if not 0 <= column < 5:
                    continue
                cell_type = cell.attrib.get("t")
                value = cell.findtext("x:v", default="", namespaces=NS)
                if cell_type == "s" and value:
                    value = strings[int(value)]
                elif cell_type == "inlineStr":
                    value = "".join(node.text or "" for node in cell.iterfind(".//x:t", NS))
                elif cell_type == "b":
                    value = "是" if value == "1" else "否"
                values[column] = value
            if values[0]:
                rows.append(values)
        return rows


def inline_cell(column: str, row: int, value: str) -> str:
    if value == "":
        return f'<c r="{column}{row}"/>'
    safe = escape(str(value), quote=False)
    preserve = ' xml:space="preserve"' if safe != safe.strip() else ""
    return f'<c r="{column}{row}" t="inlineStr"><is><t{preserve}>{safe}</t></is></c>'


def build_rows(rows: list[list[str]]) -> str:
    output = []
    for index, values in enumerate(rows, start=2):
        cells = "".join(inline_cell(chr(ord("A") + col), index, value) for col, value in enumerate(values))
        output.append(f'<row r="{index}">{cells}</row>')
    return "".join(output)


def repack(file: Path, rows: list[list[str]]) -> None:
    template_bytes = TEMPLATE.read_bytes()
    with NamedTemporaryFile(delete=False, suffix=".xlsx", dir=file.parent) as handle:
        temp_path = Path(handle.name)
    try:
        template_copy = file.parent / (file.stem + ".template-source.xlsx")
        template_copy.write_bytes(template_bytes)
        try:
            with ZipFile(template_copy, "r") as source, ZipFile(temp_path, "w") as target:
                for info in source.infolist():
                    data = source.read(info.filename)
                    if info.filename == SHEET:
                        text = data.decode("utf-8")
                        last_row = len(rows) + 1
                        text = re.sub(r'<dimension ref="A1:E1"\s*/>', f'<dimension ref="A1:E{last_row}"/>', text, count=1)
                        text = text.replace("</sheetData>", build_rows(rows) + "</sheetData>", 1)
                        data = text.encode("utf-8")
                    target.writestr(copy(info), data)
        finally:
            template_copy.unlink(missing_ok=True)
        temp_path.replace(file)
    finally:
        temp_path.unlink(missing_ok=True)


def main() -> None:
    source_files = sorted(SOURCE_DIR.glob("*.xlsx"))
    if len(source_files) != 11:
        raise RuntimeError(f"expected 11 source xlsx files, found {len(source_files)}")
    data = {file.name: read_rows(file) for file in source_files}
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, rows in data.items():
        file = OUTPUT_DIR / name
        if any(row[4] not in {"是", "否"} for row in rows):
            raise RuntimeError(f"{file.name}: invalid 是否必填 values")
        repack(file, rows)
        print(f"REPACKED {file.name}: {len(rows)} fields")


if __name__ == "__main__":
    main()
