from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import re


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = Path(r"D:\DB_TABLE_导入模板.xlsx")
OUTPUT_DIR = ROOT / "docs" / "database" / "import-templates"
SHEET = "xl/worksheets/sheet1.xml"
NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

EXPECTED_FILES = {
    "DB-01-user-profiles.xlsx",
    "DB-02-simulation-states.xlsx",
    "DB-03-route-assessments.xlsx",
    "DB-04-parallel-versions.xlsx",
    "DB-05-main-plans.xlsx",
    "DB-06-semester-tasks.xlsx",
    "DB-07-growth-reviews.xlsx",
    "DB-08-resume-entries.xlsx",
    "DB-09-decision-trials.xlsx",
    "DB-10-action-logs.xlsx",
    "DB-11-session-recaps.xlsx",
}


def shared_strings(workbook: ZipFile) -> list[str]:
    name = "xl/sharedStrings.xml"
    if name not in workbook.namelist():
        return []
    root = ET.fromstring(workbook.read(name))
    return ["".join(node.text or "" for node in item.iterfind(".//x:t", NS)) for item in root.findall("x:si", NS)]


def first_column(workbook: ZipFile) -> list[str]:
    strings = shared_strings(workbook)
    root = ET.fromstring(workbook.read(SHEET))
    values: list[str] = []
    for row in root.findall(".//x:sheetData/x:row", NS):
        if int(row.attrib.get("r", "0")) == 1:
            continue
        for cell in row.findall("x:c", NS):
            if not cell.attrib.get("r", "").startswith("A"):
                continue
            cell_type = cell.attrib.get("t")
            value = cell.findtext("x:v", default="", namespaces=NS)
            if cell_type == "s" and value:
                value = strings[int(value)]
            elif cell_type == "inlineStr":
                value = "".join(node.text or "" for node in cell.iterfind(".//x:t", NS))
            if value:
                values.append(value)
    return values


with ZipFile(TEMPLATE) as source:
    source_names = source.namelist()
    source_bytes = {name: source.read(name) for name in source_names if name != SHEET}

files = sorted(OUTPUT_DIR.glob("*.xlsx"))
assert len(files) == 11, f"expected 11 xlsx files, found {len(files)}"
assert {file.name for file in files} == EXPECTED_FILES, "database template filenames do not match final DB-01～DB-11 contract"

for file in files:
    with ZipFile(file) as workbook:
        assert workbook.namelist() == source_names, f"{file.name}: XLSX package structure changed"
        for name, expected in source_bytes.items():
            assert workbook.read(name) == expected, f"{file.name}: template entry changed: {name}"
        sheet = workbook.read(SHEET).decode("utf-8")
        assert re.search(r'<dimension ref="A1:E\d+"', sheet), f"{file.name}: invalid dimension"
        assert "dataValidations" in sheet, f"{file.name}: template validation rules missing"
        assert ">是<" in sheet and ">否<" in sheet, f"{file.name}: required values must use 是/否"
        fields = first_column(workbook)
        assert "user_key" in fields, f"{file.name}: missing required business user_key field"
        assert "uid" not in fields, f"{file.name}: must not declare platform uid as a business field"
    print(f"PASS {file.name}")
