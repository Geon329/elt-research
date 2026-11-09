const PAGE = 50;
const el = (tag, props = {}, ...kids) => {
  const node = Object.assign(document.createElement(tag), props);
  node.append(...kids.filter(k => k !== null && k !== undefined && k !== ""));
  return node;
};
const safeUrl = url => /^https?:\/\//i.test(url || "") ? url : "";
const link = (url, text = "링크") => safeUrl(url) ? el("a", { href: url, target: "_blank", rel: "noopener noreferrer", textContent: text }) : "";
const links = value => {
  const urls = String(value || "").split(/\s*\|\s*|\s+/).filter(safeUrl);
  const box = el("span");
  urls.forEach((u, i) => box.append(link(u, urls.length > 1 ? `링크${i + 1}` : "링크"), " "));
  return box;
};
const tags = list => { const s = el("span"); list.filter(Boolean).forEach(t => s.append(el("span", { className: "tag", textContent: t }))); return s; };
const cover = (src, alt) => src ? el("img", { className: "cover", src, alt, loading: "lazy" }) : el("div", { className: "cover none", textContent: "이미지 없음" });
const who = (img, name, sub) => el("div", { className: "who" },
  img ? el("img", { className: "avatar", src: img, alt: "", loading: "lazy" }) : el("span", { className: "avatar" }),
  el("span", {}, el("strong", { textContent: name }), sub ? el("div", { className: "muted", style: "margin:0", textContent: sub }) : ""));
const followers = text => {
  const m = String(text).replace(/,/g, "").match(/([\d.]+)\s*(만|천|K|M)?/i);
  if (!m) return 0;
  return parseFloat(m[1]) * ({ "만": 1e4, "천": 1e3, k: 1e3, m: 1e6 }[(m[2] || "").toLowerCase()] || 1);
};

function views(d) {
  return {
    publishers: [
      { id: "pub", title: "1. 국내 ELT 출판사 정보", rows: d.publishers,
        cols: [["출판사명", r => r.name, r => r.name], ["사이트링크", r => link(r.site, r.site)], ["시리즈 수", r => r.count, r => +r.count || 0, "num"]],
        search: r => r.name + " " + r.site, filters: [] },
      { id: "series", title: "2. 출판사별 시리즈·프로그램", rows: d.series,
        cols: [["이미지", r => cover(r.img, r.series)], ["출판사명", r => r.company, r => r.company, "co"], ["시리즈명", r => el("strong", { textContent: r.series }), r => r.series],
          ["시리즈 분류", r => tags([r.kind, r.subtype]), r => r.kind + r.subtype], ["연령대", r => tags(r.ages), r => r.ages.join()],
          ["출간일", r => r.date || "미확인", r => r.date || "", "num"], ["링크", r => link(r.link)]],
        search: r => [r.company, r.series, r.subtype].join(" "),
        filters: [["출판사", r => r.company], ["분류", r => r.kind], ["세부 유형", r => r.subtype], ["연령대", r => r.ages, true], ["이미지", r => r.img ? "있음" : "없음"]] },
    ],
    influencers: [
      { id: "inf", title: "3. 인스타그램 인플루언서 정보", rows: d.influencers,
        cols: [["프로필", r => who(r.img, r.name)], ["인스타그램 아이디", r => r.handle, r => r.handle, "nw"], ["팔로워 수", r => r.followers, r => followers(r.followers), "num"], ["링크", r => link(r.link)]],
        search: r => r.handle + " " + r.name, filters: [], sort: [2, -1] },
      { id: "act", title: "4. 인플루언서별 공구·모임", rows: d.activities,
        cols: [["프로필명", r => who(r.img, r.name, r.handle), r => r.name], ["구분", r => tags([r.type, r.elt ? "ELT" : ""]), r => r.type],
          ["공구·모임 내용", r => r.text, r => r.text, "wide"], ["날짜", r => r.date, r => r.date, "date"], ["상태", r => r.status, r => r.status, "nw"], ["링크", r => link(r.link)]],
        search: r => [r.name, r.handle, r.text].join(" "),
        filters: [["구분", r => r.type], ["상태", r => r.status], ["ELT", r => r.elt ? "ELT" : "비ELT"], ["계정", r => r.handle]], sort: [3, -1] },
      { id: "prod", title: "5. 책 공구 제품 정보", rows: d.products,
        cols: [["공구 제품명", r => r.product, r => r.product, "wide"], ["확인된 도서·시리즈", r => r.book, r => r.book], ["원제", r => r.title, r => r.title],
          ["원저작권사(원출판사)", r => r.owner, r => r.owner], ["국가", r => r.country, r => r.country, "nw"], ["국내 출판·유통사", r => r.local, r => r.local],
          ["계정", r => r.handle, r => r.handle, "nw"], ["확인 수준", r => r.level, r => r.level, "nw"], ["링크", r => link(r.link)]],
        search: r => [r.product, r.book, r.title, r.owner, r.local, r.handle].join(" "),
        filters: [["원출판사 국가", r => r.country], ["확인 수준", r => r.level], ["계정", r => r.handle]] },
      { id: "elt", title: "6. 공구 도서의 ELT 분류", rows: d.elt,
        cols: [["도서·시리즈", r => el("strong", { textContent: r.book }), r => r.book], ["원제", r => r.title, r => r.title], ["원출판사", r => r.owner, r => r.owner], ["국내 출판·유통사", r => r.local, r => r.local],
          ["ELT 분류", r => tags([r.kind, r.subtype]), r => r.kind + r.subtype], ["연령대", r => r.ages, r => r.ages, "nw"],
          ["계정", r => r.handle, r => r.handle, "nw"], ["링크", r => links(r.link)]],
        search: r => [r.book, r.title, r.owner, r.local, r.subtype, r.handle].join(" "),
        filters: [["ELT 분류", r => r.kind], ["세부 유형", r => r.subtype], ["연령대", r => r.ages]] },
    ],
  };
}

function table(v) {
  const state = { q: "", f: {}, sort: v.sort || [null, 1], page: 1 };
  const search = el("input", { type: "search", placeholder: "검색 (이름·제목·출판사…)", ariaLabel: v.title + " 검색" });
  const count = el("span", { className: "count" });
  const selects = v.filters.map(([label, get, multi]) => {
    const values = [...new Set(v.rows.flatMap(r => [].concat(get(r)).filter(Boolean)))].sort((a, b) => a.localeCompare(b, "ko"));
    const s = el("select", { ariaLabel: label }, el("option", { value: "", textContent: `${label} · 전체` }), ...values.map(x => el("option", { value: x, textContent: x })));
    s.addEventListener("change", () => { state.f[label] = s.value; state.page = 1; draw(); });
    return s;
  });
  const reset = el("button", { type: "button", textContent: "초기화", className: "reset" });
  const head = el("tr", {}, ...v.cols.map(([name, , key, cls], i) => el("th", { className: cls || "" },
    key ? el("button", { type: "button", textContent: name, onclick: () => { state.sort = [i, state.sort[0] === i ? -state.sort[1] : 1]; draw(); } }) : name)));
  const body = el("tbody");
  const prev = el("button", { type: "button", textContent: "이전" });
  const next = el("button", { type: "button", textContent: "다음" });
  const info = el("span", { className: "muted", style: "margin:0" });
  prev.onclick = () => { state.page--; draw(); };
  next.onclick = () => { state.page++; draw(); };
  search.addEventListener("input", () => { state.q = search.value.trim().toLowerCase(); state.page = 1; draw(); });
  reset.onclick = () => { search.value = ""; state.q = ""; state.f = {}; selects.forEach(s => s.value = ""); state.page = 1; draw(); };

  function draw() {
    let rows = v.rows.filter(r => (!state.q || v.search(r).toLowerCase().includes(state.q)) &&
      v.filters.every(([label, get]) => !state.f[label] || [].concat(get(r)).includes(state.f[label])));
    const [si, dir] = state.sort;
    if (si !== null) {
      const key = v.cols[si][2];
      rows = rows.slice().sort((a, b) => { const x = key(a), y = key(b); return (typeof x === "number" ? x - y : String(x).localeCompare(String(y), "ko")) * dir; });
    }
    const pages = Math.max(1, Math.ceil(rows.length / PAGE));
    state.page = Math.min(Math.max(1, state.page), pages);
    body.replaceChildren(...rows.slice((state.page - 1) * PAGE, state.page * PAGE).map(r =>
      el("tr", {}, ...v.cols.map(([, render, , cls]) => { const c = render(r); return el("td", { className: cls || "" }, c instanceof Node ? c : String(c ?? "")); }))));
    count.textContent = `${rows.length.toLocaleString()} / ${v.rows.length.toLocaleString()}행`;
    info.textContent = `${state.page} / ${pages}`;
    prev.disabled = state.page === 1;
    next.disabled = state.page === pages;
  }
  draw();
  const view = el("div", { className: "view", hidden: true },
    el("h2", { textContent: v.title }),
    el("div", { className: "controls" }, search, ...selects, reset, count),
    el("div", { className: "table-wrap" }, el("table", {}, el("thead", {}, head), body)),
    el("div", { className: "pager" }, prev, info, next));
  view.dataset.view = v.id;
  return view;
}

fetch("data.json").then(r => r.json()).then(d => {
  const all = views(d);
  for (const [panel, list] of Object.entries(all)) {
    const section = document.querySelector(`[data-panel=${panel}]`);
    const nav = section.querySelector(".subnav");
    const box = section.querySelector(".views");
    const built = list.map(table);
    box.append(...built);
    list.forEach((v, i) => {
      const b = el("button", { type: "button", ariaPressed: String(i === 0) }, v.title.replace(/^\d+\.\s*/, ""), el("span", { className: "n", textContent: v.rows.length.toLocaleString() }));
      b.onclick = () => { nav.querySelectorAll("button").forEach(x => x.ariaPressed = String(x === b)); built.forEach((n, j) => n.hidden = j !== i); };
      nav.append(b);
    });
    built[0].hidden = false;
  }
  document.querySelectorAll("[role=tab]").forEach(t => t.onclick = () => {
    document.querySelectorAll("[role=tab]").forEach(x => x.ariaSelected = String(x === t));
    document.querySelectorAll("[data-panel]").forEach(p => p.hidden = p.dataset.panel !== t.dataset.tab);
  });
  const withImg = d.series.filter(s => s.img).length;
  document.getElementById("summary").textContent =
    `출판사 ${d.publishers.length}곳 · 시리즈 ${d.series.length.toLocaleString()}개(표지 ${withImg.toLocaleString()}) · 인플루언서 ${d.influencers.length}명 · 공구·모임 ${d.activities.length}건 · 공구 도서 ${d.products.length}건 · ELT 분류 ${d.elt.length}건`;
}).catch(() => { document.getElementById("summary").textContent = "데이터를 불러오지 못했습니다."; });
