# 말씀 클래스 자동 업데이트 절차

세종월드교회 유튜브 채널(@poongyo_church)에 올라온 **편집본 설교 영상**을 찾아
설교 페이지(`s/*.html`)를 만들고 목록(`sermons.json`)에 추가한 뒤 `main`에 push 한다.
메인 페이지는 `sermon.html` (index.html은 다른 용도이니 건드리지 않는다).

## 0. 준비
- 저장소: `racoon2/20221093.github.io` (push 권한 필요), 기본 브랜치 `main`
- 작업 전 `git pull --rebase origin main`
- 유튜브는 앱의 **내장 브라우저**로 연다 (웹 fetch는 막혀 있음).

## 1. 새 영상 찾기
`https://www.youtube.com/@poongyo_church/videos` 를 열고 2~3초 기다린 뒤 아래 JS 실행:
```js
[...document.querySelectorAll('ytd-rich-item-renderer')].slice(0,30).map(e=>{const a=e.querySelector('a[href*="/watch"]');return {vid:new URL(a.href).searchParams.get('v'), txt:e.innerText.replace(/\s+/g,' ').slice(0,200)}})
```
대상 조건 (모두 만족):
- `sermons.json`에 같은 `vid`가 없다.
- **편집본**이다: 제목이 `설교제목ㅣ본문ㅣ설교자ㅣ예배명ㅣYYYY MM DD` 형식(구분자 `ㅣ`, 날짜 구분은 공백/하이픈/`l` 섞임).
  - 제목이 **날짜로 시작**하면(`2026-11-01 l ...`) 라이브 원본 → 건너뜀.
  - 길이가 70분 이상이면 라이브 원본 → 건너뜀.
- 설교 날짜가 **2026-11-06 이후**.
- 한 번 실행에 최대 6편, 오래된 것부터 처리.

## 2. 영상 정보와 자막 가져오기
`https://www.youtube.com/watch?v=<vid>` 를 열고:
```js
await new Promise(r=>setTimeout(r,3000)); const pr=document.querySelector('#movie_player').getPlayerResponse(); ({title:pr.videoDetails.title, len:+pr.videoDetails.lengthSeconds, live:pr.videoDetails.isLiveContent, hasCaps:!!pr.captions})
```
- `live:true` 이면 건너뜀. `hasCaps:false` 이면 자동 자막이 아직 없음 → 건너뜀(다음 실행 때 다시 시도).

스크립트 패널 열기 → 문단 수집:
```js
document.querySelector('#description-inline-expander #expand, tp-yt-paper-button#expand')?.click(); await new Promise(r=>setTimeout(r,1000));
[...document.querySelectorAll('button')].find(x=>/스크립트|transcript/i.test(x.innerText||x.getAttribute('aria-label')||''))?.click();
await new Promise(r=>setTimeout(r,6000));
[...document.querySelectorAll('transcript-segment-view-model, ytd-transcript-segment-renderer')].map(x=>{const t=x.innerText.trim().split(/\n+/);return t[0]+' '+t.slice(1).join(' ').replace(/^(\d+시간 )?\d+분( \d+초)?\s*|^\d+초\s*/,'')}).join('\n')
```
세그먼트가 0개면 6초 더 기다렸다 한 번 더 시도, 그래도 0이면 건너뜀.

## 3. 데이터 JSON 작성 → `data/<날짜>-<sun|wed|fri|dawn>.json`
형식은 `tools/build.py` 상단 설명 참고. 기준 예시: `data/2026-11-06-fri.json`.
- 제목에서 `title`(설교 제목), `text`(본문: `삿14장19절~15장20절` → `삿 14:19~15:20`), `preacher`(예: `임헌규 담임목사`, `최진호 전도사`), `type`(주일예배/수요예배/금요예배/새벽예배), `date`를 뽑는다. `dur` = lengthSeconds.
- `paragraphs`: 세그먼트를 이어 붙여 **40~70초 단위, 문장 끝에서** 문단으로 나눈다. 각 문단 시간은 첫 세그먼트 시간(m:ss 또는 h:mm:ss).
  - 말씀은 **거의 그대로** 두고, 자동 자막 오인식만 고친다: 성경 인명·지명(딤나, 나실인, 라헬, 기드온, 아론과 훌 등), `세종월드교회`, `침례교회`, 설교자 이름, 띄어쓰기(`이 `가 붙어버린 것 등). 의미가 불분명하면 원문 유지. 욕설처럼 들리는 오인식은 문맥에 맞게 수정.
- `summary` (한국어, 설교 내용에만 근거):
  - `overview` 3~4문장, `keywords` 5~8개, `points` 2~4개([제목, 1~2문장 설명]),
  - `apply` 3~4줄(설교에서 권면한 실천), `chapters` 5~8개([시간, 구간 제목]).

## 4. 페이지 생성·검증·배포
```bash
python3 tools/build.py data/<파일>.json
python3 -m json.tool sermons.json > /dev/null
git add -A data s sermons.json
git commit -m "설교 추가: <날짜> <예배> <제목>"
git pull --rebase origin main && git push origin main
```
- 커밋은 설교 한 편당 하나.
- `tools/`, `sermon.html`, `index.html` 등 다른 파일은 수정하지 않는다.

## 5. 마무리
- 내장 브라우저에서 연 탭은 모두 닫는다.
- 결과 보고: 추가한 설교 목록(날짜·예배·제목), 건너뛴 영상과 이유(자막 없음/라이브 등).
  추가한 게 없으면 "새 설교 없음"으로 짧게.
