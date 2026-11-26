# 그로스코리아 — 회사 홈페이지 · 플레이스 순위 대시보드

그로스코리아(GROWTH KOREA) GitHub Pages 배포 저장소입니다. 페이지 두 개를 함께 게시합니다.

| 주소 | 페이지 | 원본 |
|---|---|---|
| `https://hya910819.github.io/growthkorea/` | 회사 홈페이지 v2 (3D·모션그래픽) | `work/groskorea-website/index.html` |
| `https://hya910819.github.io/growthkorea/rank/` | 지점별 네이버 플레이스 순위 관리 대시보드 | `work/place-rank-dashboard/dist/place-rank-dashboard.html` |

> 회사 영문 표기는 **GROWTH KOREA**입니다(`GROSS` 아님).

## 구성

```
growthkorea-pages/
├─ index.html          홈페이지 (문서 1개 + vendor 폴백). '체험단 사이트 보기' → https://hya910819.github.io/matetrip/
├─ vendor/             CDN이 막힌 환경을 위한 로컬 폴백 (three · gsap · ScrollTrigger)
├─ rank/index.html     순위 대시보드 단일 파일 (CSS·JS 인라인, 외부 요청 0건)
├─ .nojekyll           GitHub Pages의 Jekyll 처리 생략
├─ sync.sh             원본 → 배포본 동기화 (커밋·푸시 없음)
├─ deploy.sh           sync → 커밋 → main·gh-pages 푸시 → 접속 확인
├─ verify_pages.py     실제 Chromium 로컬 검증 (39개 항목)
└─ preview/            검증 스크린샷
```

## 배포 방법

저장소(`hya910819/growthkorea`, **Public**)를 한 번 만든 뒤:

```bash
bash work/growthkorea-pages/deploy.sh
```

`deploy.sh`가 하는 일

1. `gh api /repos/hya910819/growthkorea` 로 저장소 확인 (없으면 안내 후 종료)
2. `sync.sh` 로 원본에서 `index.html` · `vendor/` · `rank/index.html` 을 다시 만듦
3. 커밋 (변경분이 있을 때만)
4. `main` 과 `gh-pages` 를 같은 내용으로 푸시 (`gh-pages` 는 force)
5. `https://hya910819.github.io/growthkorea/` 와 `/rank/` 가 HTTP 200이 될 때까지 확인

GitHub Pages 게시 소스는 **`gh-pages` 브랜치 `/` (root)** 입니다. Pickle의 GitHub 앱 토큰에는 Pages 설정 권한(`pages=write`, `administration=write`)이 없어 API로 소스를 바꿀 수 없기 때문에, `main`과 `gh-pages`를 함께 밀어 넣는 메이트립(`hya910819/matetrip`)과 같은 방식을 씁니다.

> 처음 푸시한 뒤 Pages가 자동으로 켜지지 않으면 저장소 **Settings → Pages → Source: `Deploy from a branch` · Branch: `gh-pages` / `(root)`** 로 한 번만 지정하면 됩니다.
> 나중에 Source를 `main / (root)`로 바꾸면 `gh-pages` 없이 갱신됩니다.

## 수정 후 반영

- 홈페이지 문구·디자인: `work/groskorea-website/index.html` 을 고친 뒤 `deploy.sh`
  (`sync.sh` 가 `../gross-experience-site/index.html` 링크를 메이트립 주소로 바꿔 넣으므로, 배포본을 직접 고치지 마세요)
- 순위 대시보드: `work/place-rank-dashboard/assets/*` 를 고치고 `deploy.sh`
  (`sync.sh` 안에서 `build.py` 가 단일 파일을 다시 만듭니다)

## 검증

```bash
cd work/growthkorea-pages
LD_LIBRARY_PATH=/workspace/.cache/chromedeps/usr/lib/x86_64-linux-gnu python3 verify_pages.py
```

로컬 서버(`127.0.0.1:8833`)를 띄워 실제 Chromium으로 확인합니다. 최근 결과 **39/39 통과**.

- `/` 200 · 히어로·섹션 5개·3D 캔버스(WebGL) 초기화 · 로컬 에셋 4개 200 · 가로 스크롤 없음(1440·390)
- `체험단 사이트 보기` → `https://hya910819.github.io/matetrip/` (`target="_blank" rel="noopener"`), 클릭 시 실제 이동 확인
- CDN(jsdelivr·Google Fonts)을 차단해도 `vendor/` 폴백으로 3D가 살아 있는지 확인
- `/rank/` 200 · KPI·순위표 렌더 · 외부 요청 0건 · `#report` 라우팅 · 가로 스크롤 없음(1440·390)
- `/rank`(슬래시 없음) → 301 로 `/rank/` 이동
- 콘솔 오류 0 · 페이지 오류 0 · 로컬 실패 요청 0

## 알아둘 점

- 저장소가 Public이면 `/rank/` 도 **주소를 아는 사람은 누구나** 열 수 있습니다(로그인 없음). 고객사·매장명이 화면에 보이므로 링크는 내부에만 공유하세요.
- 대시보드 기록은 서버가 아니라 **각자 브라우저의 `localStorage`(`gk.placeRank.v1`)** 에 저장됩니다. PC를 바꾸면 `JSON 백업`으로 옮겨야 하고, 팀원끼리 같은 데이터를 보려면 백업 파일을 주고받아야 합니다.
- 홈페이지 상담 폼은 서버 전송 없이 화면에서 문구를 만들고 카카오톡으로 넘기는 방식입니다. 그래서 정적 페이지만으로 동작합니다.
