#!/usr/bin/env python3
"""설교 데이터(JSON) 하나로 설교 페이지(s/*.html)를 만들고 sermons.json 목록을 갱신한다.

사용법:  python3 tools/build.py data/2026-11-06-fri.json

입력 JSON 형식:
{
  "vid": "유튜브 영상 ID", "date": "YYYY-MM-DD",
  "type": "주일예배|수요예배|금요예배|새벽예배", "title": "설교 제목",
  "text": "성경 본문 (예: 삿 14:19~15:20)", "preacher": "설교자", "dur": 영상 길이(초),
  "paragraphs": [["m:ss", "문단 내용"], ...],          # 시간순, 첫 항목이 자막 시작 시점
  "summary": {
    "overview": "요약 3~4문장",
    "keywords": ["키워드", ...],
    "points":   [["핵심 포인트 제목", "설명"], ...],
    "apply":    ["적용·결단 한 줄", ...],
    "chapters": [["m:ss", "구간 제목"], ...]
  }
}
"""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLUG = {"주일예배": "sun", "수요예배": "wed", "금요예배": "fri", "새벽예배": "dawn"}
TYPE_ORDER = ["주일예배", "수요예배", "금요예배", "새벽예배"]
e = html.escape


def to_sec(t):
    s = 0
    for p in t.split(":"):
        s = s * 60 + int(p)
    return s


def summary_html(d):
    sm = d["summary"]
    kw = "".join(f"<span>{e(k)}</span>" for k in sm.get("keywords", []))
    pts = "".join(f"<li><b>{e(a)}</b><small>{e(b)}</small></li>" for a, b in sm.get("points", []))
    ap = "<br>".join("· " + e(x) for x in sm.get("apply", []))
    ch = "".join(f'<a href="#" data-s="{to_sec(t)}"><time>{e(t)}</time>{e(lbl)}</a>' for t, lbl in sm.get("chapters", []))
    parts = [f'<div class="card"><h2>📝 요약</h2><p>{e(sm["overview"])}</p></div>']
    if kw: parts.append(f'<div class="card"><h2>🔑 키워드</h2><div class="kw">{kw}</div></div>')
    if pts: parts.append(f'<div class="card"><h2>📌 핵심 포인트</h2><ol class="pts">{pts}</ol></div>')
    if ap: parts.append(f'<div class="card"><h2>🙏 적용 · 결단</h2><p>{ap}</p></div>')
    if ch: parts.append(f'<div class="card"><h2>⏱ 구간 바로가기</h2><div class="chap">{ch}</div></div>')
    return '<section id="sum" class="">\n  ' + "\n  ".join(parts) + "\n</section>"


def main(path):
    d = json.load(open(path, encoding="utf-8"))
    for k in ["vid", "date", "type", "title", "text", "preacher", "dur", "paragraphs", "summary"]:
        assert k in d and d[k], f"입력에 '{k}' 값이 없습니다"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", d["date"])
    paras = [[t, x] for t, x in d["paragraphs"] if x.strip()]
    secs = [to_sec(t) for t, _ in paras]
    assert secs == sorted(secs), "문단 시간이 시간순이 아닙니다"

    listing_path = os.path.join(ROOT, "sermons.json")
    listing = json.load(open(listing_path, encoding="utf-8")) if os.path.exists(listing_path) else []
    old = next((s for s in listing if s["vid"] == d["vid"]), None)
    if old and old["url"].startswith("s/"):
        rel = old["url"]
    else:
        base = f'{d["date"]}-{SLUG.get(d["type"], "etc")}'
        rel, n = f"s/{base}.html", 2
        taken = {s["url"] for s in listing if s["vid"] != d["vid"]}
        while rel in taken:
            rel, n = f"s/{base}-{n}.html", n + 1

    y, m, dd = d["date"].split("-")
    first = paras[0][0]
    m_, s_ = divmod(to_sec(first), 60)
    fromnote = f"({m_}분 {s_}초부터)" if to_sec(first) > 20 else ""
    tpl = open(os.path.join(ROOT, "tools", "template.html"), encoding="utf-8").read()
    page = (tpl.replace("__TITLE__", e(d["title"]))
               .replace("__METALINE__", e(f'{d["text"]} · {d["preacher"]} · 세종월드교회 {d["type"]} · {int(y)}. {int(m)}. {int(dd)}'))
               .replace("__SUMMARY__", summary_html(d))
               .replace("__VID__", json.dumps(d["vid"]))
               .replace("__END__", str(int(d["dur"])))
               .replace("__T__", json.dumps(paras, ensure_ascii=False).replace("</", "<\\/"))
               .replace("__FROMNOTE__", fromnote))
    os.makedirs(os.path.join(ROOT, "s"), exist_ok=True)
    open(os.path.join(ROOT, rel), "w", encoding="utf-8").write(page)

    entry = {k: d[k] for k in ["vid", "date", "type", "title", "text", "preacher"]}
    entry["dur"] = int(d["dur"]); entry["url"] = rel
    listing = [s for s in listing if s["vid"] != d["vid"]] + [entry]
    listing.sort(key=lambda s: (s["date"], -TYPE_ORDER.index(s["type"]) if s["type"] in TYPE_ORDER else 0), reverse=True)
    json.dump(listing, open(listing_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    open(listing_path, "a").write("\n")
    print(f"OK {rel}  (목록 {len(listing)}편)")


if __name__ == "__main__":
    main(sys.argv[1])
