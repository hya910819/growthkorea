#!/usr/bin/env bash
# 그로스코리아 GitHub Pages 배포본 동기화 (커밋·푸시 없이 파일만 갱신)
#   사용: bash work/growthkorea-pages/sync.sh
#
# 소스 (작업 원본)
#   work/groskorea-website/index.html                          → ./index.html   (v3)
#   work/groskorea-website/assets/work-*.webp                  → ./assets/
#   work/groskorea-website/vendor/*                            → ./vendor/
#   work/place-rank-dashboard/dist/place-rank-dashboard.html   → ./rank/index.html
#   work/wagzag-booking/dist/wagzag-booking.html               → ./wagzag-booking/index.html
#   work/creator-platform/dist/index.html                      → ./creator/index.html
#
# 홈페이지의 '체험단 사이트 보기' 링크는 배포된 메이트립 사이트를 직접 가리킵니다.
# (v2 까지는 로컬 MVP 경로를 치환했지만, v3 는 처음부터 절대 주소를 씁니다.)
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
WEB="$DIR/../groskorea-website"
RANK="$DIR/../place-rank-dashboard"
BOOK="$DIR/../wagzag-booking"
MATETRIP_URL="https://hya910819.github.io/matetrip/"

echo "== 1) 홈페이지 복사"
cp "$WEB/index.html" "$DIR/index.html"

echo "== 2) 케이스 스터디 이미지 복사"
mkdir -p "$DIR/assets"
cp "$WEB"/assets/work-*.webp "$DIR/assets/"

echo "== 3) 에셋(vendor) 복사"
rm -rf "$DIR/vendor"
cp -R "$WEB/vendor" "$DIR/vendor"

echo "== 4) 순위 대시보드 단일 파일 빌드·복사"
python3 "$RANK/build.py"
mkdir -p "$DIR/rank"
cp "$RANK/dist/place-rank-dashboard.html" "$DIR/rank/index.html"

echo "== 5) 와그자그 예약 보드 복사"
python3 "$BOOK/build.py"
mkdir -p "$DIR/wagzag-booking"
cp "$BOOK/dist/wagzag-booking.html" "$DIR/wagzag-booking/index.html"

echo "== 6) 크리에이터스 플랫폼 빌드·복사"
python3 "$DIR/../creator-platform/build.py"
mkdir -p "$DIR/creator"
cp "$DIR/../creator-platform/dist/index.html" "$DIR/creator/index.html"

echo "== 7) 점검"
grep -q "$MATETRIP_URL" "$DIR/index.html" || { echo "   ✗ 메이트립 링크가 없습니다"; exit 1; }
if grep -q "gross-experience-site" "$DIR/index.html"; then
  echo "   ✗ 로컬 MVP 링크가 남아 있습니다"; exit 1
fi
if grep -q "{{CSS}}\|{{JS}}" "$DIR/index.html"; then
  echo "   ✗ 미치환 토큰이 남아 있습니다"; exit 1
fi
for f in "$DIR"/assets/work-*.webp; do
  [ -s "$f" ] || { echo "   ✗ 누락: $f"; exit 1; }
done
for f in "$DIR/vendor/three.min.js" "$DIR/vendor/gsap.min.js" "$DIR/vendor/ScrollTrigger.min.js"; do
  [ -s "$f" ] || { echo "   ✗ 누락: $f"; exit 1; }
done
[ -s "$DIR/rank/index.html" ] || { echo "   ✗ 누락: rank/index.html"; exit 1; }
[ -s "$DIR/wagzag-booking/index.html" ] || { echo "   ✗ 누락: wagzag-booking/index.html"; exit 1; }
[ -s "$DIR/creator/index.html" ] || { echo "   ✗ 누락: creator/index.html"; exit 1; }
if grep -qE "<script[^>]+src=|<link[^>]+rel=\"stylesheet\"" "$DIR/creator/index.html"; then
  echo "   ✗ creator/index.html 에 외부 스크립트·스타일 참조가 있습니다"; exit 1
fi
echo "   완료 · index.html $(wc -c < "$DIR/index.html" | tr -d ' ') bytes · assets $(ls "$DIR"/assets | wc -l | tr -d ' ')개 · rank $(wc -c < "$DIR/rank/index.html" | tr -d ' ') bytes · wagzag-booking $(wc -c < "$DIR/wagzag-booking/index.html" | tr -d ' ') bytes · creator $(wc -c < "$DIR/creator/index.html" | tr -d ' ') bytes"
