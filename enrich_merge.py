import json
from pathlib import Path

import openpyxl
from openpyxl.styles import PatternFill

SOURCE = Path("C:/Users/tcmkr/OneDrive/바탕 화면/초이스메이커 기획/ELT/출판사 및 인플루언서 조사")
ENRICH = Path("C:/Users/tcmkr/.omonyang-mk/work/elt-blog/enrich")
FIELDS = {"title": "원제", "owner": "원출판사", "country": "원출판사 국가", "local": "국내 출판·유통사", "isbn": "ISBN", "level": "확인 수준"}


def load_updates():
    updates = {}
    for path in sorted(ENRICH.glob("*.out.json")):
        for item in json.loads(path.read_text(encoding="utf-8")):
            for key in item.get("keys") or [item["key"]]:
                updates[int(key[1:])] = item
    return updates


def write_workbook(updates):
    book = openpyxl.load_workbook(SOURCE / "공구목록.xlsx")
    ws = book["계정별 공구 도서"]
    header = [c.value for c in ws[1]]
    col = {name: header.index(name) + 1 for name in header if name}
    extra = ws.max_column + 1
    ws.cell(1, extra, "웹 보강 근거")
    ws.cell(1, extra + 1, "웹 보강 메모")
    fill = PatternFill("solid", fgColor="FFF2CC")
    changed = 0
    for index in range(ws.max_row - 1):
        item = updates.get(index)
        if not item:
            continue
        row = index + 2
        touched = False
        for field, name in FIELDS.items():
            value = (item.get(field) or "").strip()
            if not value or name not in col:
                continue
            cell = ws.cell(row, col[name])
            if str(cell.value or "").strip() != value:
                cell.value = value
                cell.fill = fill
                touched = True
        ws.cell(row, extra, " | ".join(item.get("evidence") or []))
        ws.cell(row, extra + 1, item.get("note", ""))
        changed += touched
    out = SOURCE / "공구목록_웹보강.xlsx"
    book.save(out)
    return out, changed


if __name__ == "__main__":
    updates = load_updates()
    out, changed = write_workbook(updates)
    print("MERGE_DONE", len(updates), "rows changed", changed, out, flush=True)
