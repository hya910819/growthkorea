#!/usr/bin/env bash
# 그로스코리아 GitHub Pages 배포본 동기화 (커밋·푸시 없이 파일만 갱신)
#   사용: bash work/growthkorea-pages/sync.sh
#
# 소스 (작업 원본)
#   work/groskorea-website/index.html                          → ./index.html
#   work/groskorea-website/vendor/*                            → ./vendor/
#   work/place-rank-dashboard/dist/place-rank-dashboard.html   → ./rank/index.html
#   work/wagzag-booking/dist/wagzag-booking.html               → ./wagzag-booking/index.html
#   work/creator-platform/dist/index.html                      → ./creator/index.html
#
# 홈페이지의 '체험단 사이트 보기' 링크는 로컬 MVP(../gross-experience-site/index.html) 대신
# 배포된 메이트립 사이트(https://hya910819.github.io/matetrip/)를 열도록 바꿔 넣습니다.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
WEB="$DIR/../groskorea-website"
RANK="$DIR/../place-rank-dashboard"
BOOK="$DIR/../wagzag-booking"
MATETRIP_URL="https://hya910819.github.io/matetrip/"
LOCAL_MVP='../gross-experience-site/index.html'

echo "== 1) 홈페이지 복사"
cp "$WEB/index.html" "$DIR/index.html"
python3 - "$DIR/index.html" "$LOCAL_MVP" "$MATETRIP_URL" <<'PY'
import sys, pathlib
path, old, new = sys.argv[1], sys.argv[2], sys.argv[3]
p = pathlib.Path(path)
html = p.read_text(encoding="utf-8")
n = html.count(old)
if n != 1:
    raise SystemExit(f"체험단 링크를 1건 찾아야 하는데 {n}건입니다. 소스를 확인하세요: {old}")
html = html.replace(old, new)
p.write_text(html, encoding="utf-8")
print(f"   체험단 링크 교체: {old} → {new}")
PY

echo "== 2) 에셋(vendor) 복사"
rm -rf "$DIR/vendor"
cp -R "$WEB/vendor" "$DIR/vendor"

echo "== 3) 순위 대시보드 단일 파일 빌드·복사"
python3 "$RANK/build.py"
mkdir -p "$DIR/rank"
cp "$RANK/dist/place-rank-dashboard.html" "$DIR/rank/index.html"

echo "== 4) 와그자그 예약 보드 복사"
python3 "$BOOK/build.py"
mkdir -p "$DIR/wagzag-booking"
cp "$BOOK/dist/wagzag-booking.html" "$DIR/wagzag-booking/index.html"

echo "== 5) 크리에이터스 플랫폼 빌드·복사"
python3 "$DIR/../creator-platform/build.py"
mkdir -p "$DIR/creator"
cp "$DIR/../creator-platform/dist/index.html" "$DIR/creator/index.html"

echo "== 6) 점검"
grep -c "https://hya910819.github.io/matetrip/" "$DIR/index.html" | sed 's/^/   메이트립 링크 수: /'
if grep -q "gross-experience-site" "$DIR/index.html"; then
  echo "   ✗ 로컬 MVP 링크가 남아 있습니다"; exit 1
fi
for f in "$DIR/vendor/three.module.min.js" "$DIR/vendor/three.min.js" "$DIR/vendor/gsap.min.js" "$DIR/vendor/ScrollTrigger.min.js"; do
  [ -s "$f" ] || { echo "   ✗ 누락: $f"; exit 1; }
done
[ -s "$DIR/rank/index.html" ] || { echo "   ✗ 누락: rank/index.html"; exit 1; }
[ -s "$DIR/wagzag-booking/index.html" ] || { echo "   ✗ 누락: wagzag-booking/index.html"; exit 1; }
[ -s "$DIR/creator/index.html" ] || { echo "   ✗ 누락: creator/index.html"; exit 1; }
if grep -qE "<script[^>]+src=|<link[^>]+rel=\"stylesheet\"" "$DIR/creator/index.html"; then
  echo "   ✗ creator/index.html 에 외부 스크립트·스타일 참조가 있습니다"; exit 1
fi
echo "   완료 · index.html $(wc -c < "$DIR/index.html" | tr -d ' ') bytes · rank/index.html $(wc -c < "$DIR/rank/index.html" | tr -d ' ') bytes · wagzag-booking/index.html $(wc -c < "$DIR/wagzag-booking/index.html" | tr -d ' ') bytes · creator/index.html $(wc -c < "$DIR/creator/index.html" | tr -d ' ') bytes"
