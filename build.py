import json
import sys
from pathlib import Path

import openpyxl
from PIL import Image

SOURCE = Path("C:/Users/tcmkr/OneDrive/바탕 화면/초이스메이커 기획/ELT/출판사 및 인플루언서 조사")
SITE = Path(__file__).parent / "docs"
IMG = SITE / "img"


def sheet(file, name):
    ws = openpyxl.load_workbook(SOURCE / file, read_only=True, data_only=True)[name]
    rows = ws.iter_rows(values_only=True)
    header = [str(h).strip() if h is not None else "" for h in next(rows)]
    return [dict(zip(header, ("" if v is None else str(v).strip() for v in r))) for r in rows if any(v not in (None, "") for v in r)]


def thumb(src, dest, width):
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        im = im.convert("RGB")
        im.thumbnail((width, width * 2))
        im.save(dest, "WEBP", quality=80)


def images(manifests, key):
    found = {}
    for path in manifests:
        for row in json.loads(path.read_text(encoding="utf-8")):
            if row.get("status") == "saved" and Path(row.get("local_path") or "").is_file():
                found[row[key]] = row
    return found


def handle(value):
    return value.strip().lstrip("@").lower()


series_images = images(sorted((SOURCE / "이미지/목록").glob("시리즈_프로그램_*.json")), "source_excel_row")
profile_images = {handle(k): v for k, v in images([SOURCE / "이미지/목록/인플루언서_프로필_이미지.json"], "handle").items()}

publishers = [
    {"name": r["회사명"], "site": r["사이트"], "count": r["시리즈 수"]}
    for r in sheet("ELT_출판사_시리즈_신간순20261108.xlsx", "회사별 요약")
]

series = []
mismatch = 0
for index, r in enumerate(sheet("ELT_출판사_시리즈_신간순20261108.xlsx", "시리즈 전체"), start=2):
    image = series_images.get(index)
    if image and (image["company"], image["series"]) != (r["회사명"], r["시리즈·프로그램"]):
        mismatch += 1
        image = None
    file = ""
    if image:
        file = f"img/s/{image['id']}.webp"
        thumb(image["local_path"], SITE / file, 240)
    series.append({
        "company": r["회사명"], "series": r["시리즈·프로그램"],
        "kind": {"A": "A 코스형", "B": "B 읽기물형"}.get(r["A/B"], r["A/B"]), "subtype": r["세부 유형"],
        "ages": [a for a in ("유아", "초등", "중등", "성인") if r[a] == "O"],
        "link": r["근거 링크"], "date": r["출간일"][:10], "img": file,
    })

influencers = []
for r in sheet("ELT_인스타그램.xlsx", "간단 목록"):
    h = handle(r["계정명"])
    file = ""
    if h in profile_images:
        file = f"img/p/{h}.webp"
        thumb(profile_images[h]["local_path"], SITE / file, 96)
    influencers.append({"handle": "@" + h, "name": r["프로필 이름"], "followers": r["팔로워 수"], "link": r["계정 링크"], "img": file})
avatar = {i["handle"]: (i["name"], i["img"]) for i in influencers}

activities = []
for r in sheet("ELT_인스타그램_공구,모임.xlsx", "공구·모임 근거"):
    name, img = avatar.get("@" + handle(r["계정명"]), (r["계정명"], ""))
    activities.append({
        "handle": "@" + handle(r["계정명"]), "name": name, "img": img, "type": r["구분"],
        "date": r["날짜"], "text": r["내용"], "status": r["상태"], "elt": r["ELT"] == "O", "link": r["근거 링크"],
    })

products = [
    {"handle": "@" + handle(r["계정명"]), "date": r["공구 날짜"], "product": r["공구 제품명"], "book": r["확인된 도서·시리즈"],
     "title": r["원제"], "owner": r["원출판사"], "country": r["원출판사 국가"], "local": r["국내 출판·유통사"],
     "level": r["확인 수준"], "link": r["공구 글 링크"]}
    for r in sheet("공구목록.xlsx", "계정별 공구 도서")
]

elt = []
for tab, label in (("ELT_A_코스형", "A 코스형"), ("ELT_B_읽기물형", "B 읽기물형"), ("ELT_판본확인필요", "판본 확인 필요")):
    for r in sheet("ELT_인스타그램_ELT_분류.xlsx", tab):
        elt.append({"handle": "@" + handle(r["계정명"]), "book": r["확인된 도서·시리즈"], "title": r["원제"], "owner": r["원출판사"],
                    "kind": label, "subtype": r["ELT세부유형"], "ages": r["연령대"], "basis": r["분류근거"], "link": r["공구 글 링크"]})

data = {"publishers": publishers, "series": series, "influencers": influencers,
        "activities": activities, "products": products, "elt": elt}
(SITE / "data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
stats = {k: len(v) for k, v in data.items()}
stats["series_with_image"] = sum(bool(s["img"]) for s in series)
stats["influencers_with_image"] = sum(bool(i["img"]) for i in influencers)
stats["series_row_mismatch"] = mismatch
print("BUILD_DONE", json.dumps(stats, ensure_ascii=False), flush=True)
sys.exit(1 if mismatch else 0)
