# 그로스코리아 — 회사 홈페이지 · 플레이스 순위 대시보드 · 크리에이터스

그로스코리아(GROWTH KOREA) GitHub Pages 배포 저장소입니다. 페이지 네 개를 함께 게시합니다.

| 주소 | 페이지 | 원본 |
|---|---|---|
| `https://hya910819.github.io/growthkorea/` | 회사 홈페이지 v3 (하이엔드 · 케이스 스터디) | `work/groskorea-website/index.html` |
| `https://hya910819.github.io/growthkorea/rank/` | 지점별 네이버 플레이스 순위 관리 대시보드 | `work/place-rank-dashboard/dist/place-rank-dashboard.html` |
| `https://hya910819.github.io/growthkorea/wagzag-booking/` | 와그자그 교동점 직원용 예약 보드 (PIN 잠금) | `work/wagzag-booking/dist/wagzag-booking.html` |
| `https://hya910819.github.io/growthkorea/creator/` | 크리에이터스 — 크리에이터 모집 플랫폼 (1차 시연) | `work/creator-platform/dist/index.html` |

> 회사 영문 표기는 **GROWTH KOREA**입니다(`GROSS` 아님).

## 구성

```
growthkorea-pages/
├─ index.html          홈페이지 v3 (문서 1개 · Three.js 3D + GSAP + 케이스 모달)
├─ assets/             케이스 스터디 이미지 4종 (work-*.webp, 1200×800)
├─ vendor/             CDN이 막힌 환경을 위한 로컬 폴백 (three · gsap · ScrollTrigger)
├─ rank/index.html     순위 대시보드 단일 파일 (CSS·JS 인라인, 외부 요청 0건)
├─ wagzag-booking/index.html  와그자그 예약 보드 단일 파일 (예약 데이터는 PIN 기반 암호문)
├─ creator/index.html  크리에이터스 모집 플랫폼 단일 파일 (외부 요청 0건, localStorage)
├─ .nojekyll           GitHub Pages의 Jekyll 처리 생략
├─ sync.sh             원본 → 배포본 동기화 (커밋·푸시 없음)
├─ deploy.sh           sync → 커밋 → main·gh-pages 푸시 → 접속 확인
├─ verify_pages.py     배포본 로컬 검증 (38개 항목 — 홈 v3 · rank · 폴백)
├─ verify_live.py      라이브 URL 검증 (1440×900 · 390×844, 31개 항목)
├─ capture_mobile.py   모바일 섹션 캡처 · 인터랙션(드로어·모달·탭) 확인
├─ capture_desktop.py  데스크톱 섹션·표 레이아웃 캡처
├─ anchor_test.py      앵커 이동 시 고정 헤더 가림 확인
├─ preview/            로컬 검증 스크린샷
└─ preview-live/       라이브 검증 스크린샷 · 본문 텍스트 덤프(text/)
```

## 배포 방법

저장소(`hya910819/growthkorea`, **Public**)를 한 번 만든 뒤:

```bash
bash work/growthkorea-pages/deploy.sh
```

`deploy.sh`가 하는 일

1. `gh api /repos/hya910819/growthkorea` 로 저장소 확인 (없으면 안내 후 종료)
2. `sync.sh` 로 원본에서 `index.html` · `vendor/` · `rank/index.html` · `wagzag-booking/index.html` · `creator/index.html` 을 다시 만듦
3. 커밋 (변경분이 있을 때만)
4. `main` 과 `gh-pages` 를 같은 내용으로 푸시 (`gh-pages` 는 force)
5. `https://hya910819.github.io/growthkorea/` · `/rank/` · `/wagzag-booking/` · `/creator/` 가 HTTP 200이 될 때까지 확인

GitHub Pages 게시 소스는 **`gh-pages` 브랜치 `/` (root)** 입니다. Pickle의 GitHub 앱 토큰에는 Pages 설정 권한(`pages=write`, `administration=write`)이 없어 API로 소스를 바꿀 수 없기 때문에, `main`과 `gh-pages`를 함께 밀어 넣는 메이트립(`hya910819/matetrip`)과 같은 방식을 씁니다.

> 2026-11-26 첫 배포에서 `gh-pages` 푸시 직후 Pages가 **자동 활성화**되었습니다(별도 설정 불필요, `status=built`).
> 만약 나중에 자동으로 켜지 않으면 저장소 **Settings → Pages → Source: `Deploy from a branch` · Branch: `gh-pages` / `(root)`** 로 한 번만 지정하면 됩니다.
> 나중에 Source를 `main / (root)`로 바꾸면 `gh-pages` 없이 갱신됩니다.

## 수정 후 반영

- 홈페이지 문구·디자인: `work/groskorea-website/src/` 를 고치고 `python3 build.py` → `deploy.sh`
  (`sync.sh` 가 `index.html`·`assets/`·`vendor/` 를 복사합니다. 배포본을 직접 고치지 마세요)
- 순위 대시보드: `work/place-rank-dashboard/assets/*` 를 고치고 `deploy.sh`
  (`sync.sh` 안에서 `build.py` 가 단일 파일을 다시 만듭니다)

## 검증

```bash
cd work/groskorea-website
LD_LIBRARY_PATH=/workspace/.cache/chromedeps/usr/lib/x86_64-linux-gnu python3 verify.py
```

홈페이지 원본(`work/groskorea-website/`)을 로컬 서버로 띄워 실제 Chromium으로 확인합니다. **48/48 통과** (2026-11-28).
콘솔 오류 0 · 이미지 4종 로드 · 360~1920px 가로 스크롤 0 · 커서가 버튼 글자를 가리지 않음 · 필터·모달·아코디언·앵커·폼 · no-JS · 모션 최소화 · CDN 차단 폴백까지 포함합니다.

```bash
cd work/growthkorea-pages
LD_LIBRARY_PATH=/workspace/.cache/chromedeps/usr/lib/x86_64-linux-gnu python3 verify_pages.py   # 배포본 로컬 · 38/38
LD_LIBRARY_PATH=/workspace/.cache/chromedeps/usr/lib/x86_64-linux-gnu python3 verify_live.py    # 라이브 · 31/31
```

`verify_live.py`가 라이브에서 직접 확인하는 것 (2026-11-28 배포분)

- 홈 · `/rank/` · `/creator/` · `/wagzag-booking/` · 메이트립 모두 HTTP 200, `assets/*.webp` · `vendor/*.js` 200
- 데스크톱 1440×900 · 모바일 390×844 가로 스크롤 0, 콘솔 오류 0, 페이지 오류 0, 실패 요청 0
- WebGL 초기화 · GSAP/ScrollTrigger 로드 · 케이스 카드 4건 · 필터(테크 2건) · 모달 열기/ESC 닫기(4단계)
- 앵커 이동 시 섹션 제목이 고정 헤더에 가리지 않음(78px) · 모바일 드로어 · 모바일 모달 전체 폭
- 폼 필수 3항목 검증 · `GROSS` 표기 0건
- 스크린샷: `preview-live/*.png`, `../groskorea-website/preview/pc-home-v3.png` · `pc-work-v3.png` · `mobile-home-v3.png`

## 알아둘 점

- 저장소가 Public이면 `/rank/` 도 **주소를 아는 사람은 누구나** 열 수 있습니다(로그인 없음). 고객사·매장명이 화면에 보이므로 링크는 내부에만 공유하세요.
- 대시보드 기록은 서버가 아니라 **각자 브라우저의 `localStorage`(`gk.placeRank.v1`)** 에 저장됩니다. PC를 바꾸면 `JSON 백업`으로 옮겨야 하고, 팀원끼리 같은 데이터를 보려면 백업 파일을 주고받아야 합니다.
- 홈페이지 상담 폼은 서버 전송 없이 화면에서 문구를 만들고 카카오톡으로 넘기는 방식입니다. 그래서 정적 페이지만으로 동작합니다.
- 홈페이지 케이스 스터디 이미지는 분위기 연출용으로 만든 이미지입니다(실제 매장 사진 아님). 모달 하단에 그 문구를 표시합니다.

## 예약 보드 (`/wagzag-booking/`) — 개인정보 보호

- 저장소가 **Public** 이므로, 예약 보드의 고객 이름·연락처는 `wagzag-booking/index.html` **소스에 평문으로 들어가지 않습니다**. `work/wagzag-booking/build.py` 가 예약 데이터를 매장 공용 4자리 PIN 으로 XOR+Base64 암호화해 넣고, 빌드가 평문 0건을 직접 검사합니다.
- 접속할 때 4자리 PIN 을 한 번 입력하면 그 기기(브라우저)의 `localStorage` 에 기억됩니다. PIN 은 소스에 넣지 않습니다.
- 브라우저가 직접 복호화하는 구조라 **4자리 PIN 은 자물쇠가 아니라 가림막**입니다. 주소는 내부 직원에게만 공유하고, 더 강한 보호가 필요하면 비공개 저장소·서버 로그인으로 옮겨야 합니다.
- 예약 저장 위치: 각 직원 브라우저의 `localStorage`(`wz.booking.v1`, 암호문). 기기를 바꾸면 화면의 **데이터 → 백업 파일**로 옮기고, 백업 파일도 같은 PIN 으로만 열립니다.

## 크리에이터스 (`/creator/`)

- 크리에이터 모집 플랫폼 1차 시연 버전입니다. 캠페인·지원자·매칭 점수는 예시 데이터이고, 입력 내용은 서버로 전송되지 않고 접속한 브라우저의 `localStorage`(`gk.creators.v1`)에만 저장됩니다.
- 원본·검증: `work/creator-platform/` (`python3 build.py`, `verify.py` 80/80 통과)
- 바이오링크 공유는 `.../creator/#p=<base64로 인코딩한 프로필>` 형태로 링크 자체에 프로필이 담깁니다. 암호화가 아니므로 누구나 내용을 볼 수 있고, 서버가 없어도 상대 화면에 보이지만 링크가 길고 수정 시 새로 복사해야 합니다.
- 매니저 콘솔은 로그인 없이 열립니다. 예시 데이터만 들어 있어 위험은 없지만, 실제 접수 데이터를 연결할 때는 반드시 인증을 붙여야 합니다.
