from pathlib import Path

import openpyxl
from openpyxl.styles import PatternFill

SOURCE = Path("C:/Users/tcmkr/OneDrive/바탕 화면/초이스메이커 기획/ELT/출판사 및 인플루언서 조사")
COLUMNS = ["원제", "저자", "원출판사", "원출판사 국가", "공구 판본 출판사", "국내 출판·유통사", "ISBN", "확인 수준", "미확인·주의"]
fill = PatternFill("solid", fgColor="FFF2CC")

enriched = openpyxl.load_workbook(SOURCE / "공구목록_웹보강.xlsx", read_only=True, data_only=True)["계정별 공구 도서"]
rows = list(enriched.iter_rows(values_only=True))
head = list(rows[0])
by_key = {}
for row in rows[1:]:
    record = dict(zip(head, row))
    by_key[(record["계정명"], record["공구 날짜"], record["확인된 도서·시리즈"])] = record

book = openpyxl.load_workbook(SOURCE / "ELT_인스타그램_ELT_분류.xlsx")
changed = matched = total = 0
for ws in book.worksheets:
    header = [c.value for c in ws[1]]
    if not {"계정명", "공구 날짜", "확인된 도서·시리즈"} <= set(header):
        continue
    col = {name: i + 1 for i, name in enumerate(header) if name}
    for r in range(2, ws.max_row + 1):
        key = tuple(ws.cell(r, col[n]).value for n in ("계정명", "공구 날짜", "확인된 도서·시리즈"))
        if not any(key):
            continue
        total += 1
        source = by_key.get(key)
        if not source:
            continue
        matched += 1
        for name in COLUMNS:
            if name in col and name in source and source[name] not in (None, "") and ws.cell(r, col[name]).value != source[name]:
                ws.cell(r, col[name]).value = source[name]
                ws.cell(r, col[name]).fill = fill
                changed += 1
out = SOURCE / "ELT_인스타그램_ELT_분류_웹보강.xlsx"
book.save(out)
print("ELT_MERGE_DONE rows", total, "matched", matched, "cells changed", changed, out, flush=True)
