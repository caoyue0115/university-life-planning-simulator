import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const dir = path.join(process.cwd(), "docs", "database", "import-templates");
const files = (await fs.readdir(dir)).filter((name) => name.endsWith(".xlsx")).sort();
if (files.length !== 11) throw new Error(`expected 11 xlsx files, found ${files.length}`);

for (const file of files) {
  const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(dir, file)));
  const region = await workbook.inspect({
    kind: "region",
    sheetId: "Sheet1",
    range: "A1:E100",
    maxChars: 20000,
    tableMaxRows: 100,
    tableMaxCols: 5,
  });
  const rows = JSON.parse(region.ndjson).preview;
  const values = rows.slice(1).filter((row) => row[0]).map((row) => row[4]);
  const invalid = values.filter((value) => value !== "是" && value !== "否");
  if (invalid.length) {
    throw new Error(`${file}: 是否必填 must use 是/否; found ${JSON.stringify(invalid)}`);
  }
  console.log(`PASS ${file}`);
}
