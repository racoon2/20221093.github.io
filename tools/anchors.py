"""자막 구간을 문단으로 묶으면서 구간 시작점([단어순번, 초])을 같이 남긴다.

입력 raw: [["m:ss", [[초, "구간 글"], ...]], ...]  (브라우저에서 뽑은 문단별 자막 구간)
fixes:   [("틀린 말", "고친 말"), ...]  (구간마다 적용 — 구간 경계를 넘는 교정은 적용되지 않음)
출력:    [["m:ss", "문단 내용", [[단어순번, 초], ...]], ...]  (build.py 형식)
"""
def build(raw, fixes=()):
    out = []
    for t, segs in raw:
        words, anchors = [], []
        for sec, txt in segs:
            for a, b in fixes:
                txt = txt.replace(a, b)
            ws = txt.split()
            if not ws:
                continue
            anchors.append([len(words), round(float(sec), 2)])
            words += ws
        text = " ".join(words)
        out.append([t, text, anchors])
    return out
