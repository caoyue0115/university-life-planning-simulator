from pathlib import Path
from zipfile import ZipFile
import re


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = Path(r"D:\DB_TABLE_导入模板.xlsx")
OUTPUT_DIR = ROOT / "docs" / "database" / "import-templates"
SHEET = "xl/worksheets/sheet1.xml"


with ZipFile(TEMPLATE) as source:
    source_names = source.namelist()
    source_bytes = {name: source.read(name) for name in source_names if name != SHEET}

files = sorted(OUTPUT_DIR.glob("*.xlsx"))
assert len(files) == 11, f"expected 11 xlsx files, found {len(files)}"

for file in files:
    with ZipFile(file) as workbook:
        assert workbook.namelist() == source_names, f"{file.name}: XLSX package structure changed"
        for name, expected in source_bytes.items():
            assert workbook.read(name) == expected, f"{file.name}: template entry changed: {name}"
        sheet = workbook.read(SHEET).decode("utf-8")
        assert re.search(r'<dimension ref="A1:E\d+"', sheet), f"{file.name}: invalid dimension"
        assert "dataValidations" in sheet, f"{file.name}: template validation rules missing"
        assert ">是<" in sheet and ">否<" in sheet, f"{file.name}: required values must use 是/否"
    print(f"PASS {file.name}")
