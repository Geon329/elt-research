import json
import sys
from pathlib import Path

import openpyxl
from PIL import Image

SOURCE = Path("C:/Users/tcmkr/OneDrive/바탕 화면/초이스메이커 기획/ELT/출판사 및 인플루언서 조사")
SITE = Path(__file__).parent / "docs"
IMG = SITE / "img"


def unq(v):
    return v[1:] if isinstance(v, str) and v.startswith("'") and v[1:2] in "=+-@" else v


def sheet(file, name):
    ws = openpyxl.load_workbook(SOURCE / file, read_only=True, data_only=True)[name]
    rows = ws.iter_rows(values_only=True)
    header = [str(h).strip() if h is not None else "" for h in next(rows)]
    return [dict(zip(header, (unq("" if v is None else str(v).strip()) for v in r))) for r in rows if any(v not in (None, "") for v in r)]


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

GRADES = json.loads((Path(__file__).parent / "publisher-grades.json").read_text(encoding="utf-8"))
grade_of = GRADES["grades"]
publishers = [
    {"name": r["회사명"], "site": r["사이트"], "count": r["시리즈 수"], "grade": grade_of[r["회사명"]]}
    for r in sheet("ELT_출판사_시리즈_신간순20261108.xlsx", "회사별 요약") if r["회사명"] in grade_of
]

series = []
mismatch = 0
for index, r in enumerate(sheet("ELT_출판사_시리즈_신간순20261108.xlsx", "시리즈 전체"), start=2):
    if r["회사명"] not in grade_of:
        continue
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
        "grade": grade_of[r["회사명"]], "kind": {"A": "A 코스형", "B": "B 읽기물형"}.get(r["A/B"], r["A/B"]), "subtype": r["세부 유형"],
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
    for r in sheet("공구목록_웹보강.xlsx", "계정별 공구 도서")
]
enriched = {(p["handle"], p["book"]): p for p in products}
for p in products:
    p["period"] = "최근"
for r in sheet("공구목록_1년치_웹보강.xlsx", "계정별 공구 도서"):
    products.append({"handle": r["계정명"], "date": r["공구날짜"], "product": r["공구제품명"], "book": r["확인된도서"],
                     "title": r["원제"], "owner": r["원출판사"], "country": r["원출판사국가"], "local": r["국내출판유통사"],
                     "level": r["확인수준"], "link": r["공구글링크"], "period": "1년치"})

elt = []
for tab, label in (("ELT_A_코스형", "A 코스형"), ("ELT_B_읽기물형", "B 읽기물형"), ("ELT_판본확인필요", "판본 확인 필요")):
    for r in sheet("ELT_인스타그램_ELT_분류.xlsx", tab):
        match = enriched.get(("@" + handle(r["계정명"]), r["확인된 도서·시리즈"]), {})
        elt.append({"handle": "@" + handle(r["계정명"]), "book": r["확인된 도서·시리즈"], "title": match.get("title", r["원제"]), "owner": match.get("owner", r["원출판사"]), "local": match.get("local", r.get("국내 출판·유통사", "")),
                    "kind": label, "subtype": r["ELT세부유형"], "ages": r["연령대"], "basis": r["분류근거"], "link": r["공구 글 링크"]})

for p in products:
    p.setdefault("period", "최근")
for e in elt:
    e.setdefault("period", "최근")
for r in sheet("공구목록_1년치_웹보강.xlsx", "계정별 공구 도서"):
    if r["ELT분류"] in ("A 코스형", "B 읽기물형"):
        elt.append({"handle": r["계정명"], "book": r["확인된도서"], "title": r["원제"], "owner": r["원출판사"], "local": r["국내출판유통사"],
                    "kind": r["ELT분류"], "subtype": r["세부유형"], "ages": r["연령대"], "basis": "", "link": r["공구글링크"], "period": "1년치"})
def build_stats(products, elt, grade_of):
    import re as _re
    def gkey(s):
        return _re.sub(r"[\s·.,/&'()\-]+", "", str(s or "").lower())
    gk = [(gkey(p), g) for name, g in grade_of.items() for p in name.split("/") if len(gkey(p)) >= 2]
    def grade(r):
        for f in (r.get("local"), r.get("owner")):
            n = gkey(f)
            if n and "미확인" not in str(f):
                for k, g in gk:
                    if k in n or (len(n) >= 3 and n in k):
                        return g
        return "미확인·등급 없음"
    out = []
    def add(group, items, base):
        total = sum(items.values()) or 1
        for label, cnt in sorted(items.items(), key=lambda kv: -kv[1])[:30]:
            out.append({"group": group, "label": label, "count": cnt, "pct": round(cnt * 100 / total, 1), "base": base})
    from collections import Counter
    def canon(s):
        s = str(s or "").strip()
        t = _re.sub(r"\s*[\(（].*?[\)）]", "", s)
        t = _re.sub(r"[,.]?\s*(Inc|Ltd|LLC|Co|Corp|Limited|Publishing|Publishers|Press|Books|Group|UK|USA|US)\.?$", "", t, flags=_re.I).strip()
        t = _re.sub(r"[,.]?\s*(Inc|Ltd|LLC|Co|Corp|Limited)\.?$", "", t, flags=_re.I).strip()
        return t or s
    names = {}
    for p in products:
        if p.get("owner"):
            names.setdefault(canon(p["owner"]).lower(), Counter())[canon(p["owner"])] += 1
    def merged(s):
        c = names.get(canon(s).lower())
        return c.most_common(1)[0][0] if c else s
    for r in list(products) + list(elt):
        o = r.get("owner")
        r["po"] = merged(o) if o and "미확인" not in o else ""
        g = grade(r)
        r["pg"] = "" if g == "미확인·등급 없음" else g
    products = [dict(p, owner=merged(p["owner"])) if p.get("owner") and "미확인" not in p["owner"] else p for p in products]
    elt = [dict(e, owner=merged(e["owner"])) if e.get("owner") and "미확인" not in e["owner"] else e for e in elt]
    ok = [p for p in products if p["level"] in ("확인", "부분 확인") and p.get("owner") and "미확인" not in p["owner"]]
    base = f"원출판사 확인 {len(ok):,} / 전체 {len(products):,}행"
    add("확인 수준", Counter(p["level"] for p in products), f"전체 {len(products):,}행")
    add("원출판사 국가", Counter(p["country"] if p.get("country") and "미확인" not in p["country"] else "미확인" for p in ok), base)
    add("원출판사 순위", Counter(p["owner"] for p in ok), base)
    add("국내 출판·유통사 순위", Counter(p["local"] for p in products if p.get("local") and "미확인" not in p["local"]), "국내 출판·유통사 확인된 행")
    add("출판사 등급(A~E)", Counter(grade(p) for p in products), f"전체 {len(products):,}행")
    add("ELT 분류", Counter(e["kind"] for e in elt), f"ELT {len(elt):,}행")
    add("ELT 연령대", Counter((e.get("ages") or "미확인") for e in elt), f"ELT {len(elt):,}행")
    acc = Counter((p["handle"], p["owner"]) for p in ok)
    for (h, o), c in acc.most_common(30):
        out.append({"group": "계정별 많이 공구한 원출판사", "label": f"{h} · {o}", "count": c, "pct": None, "base": base})
    return out


data = {"stats": build_stats(products, elt, grade_of), "gradeLegend": GRADES["legend"], "publishers": publishers, "series": series, "influencers": influencers,
        "activities": activities, "products": products, "elt": elt}
(SITE / "data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
stats = {k: len(v) for k, v in data.items()}
stats["series_with_image"] = sum(bool(s["img"]) for s in series)
stats["influencers_with_image"] = sum(bool(i["img"]) for i in influencers)
stats["series_row_mismatch"] = mismatch
print("BUILD_DONE", json.dumps(stats, ensure_ascii=False), flush=True)
sys.exit(1 if mismatch else 0)
