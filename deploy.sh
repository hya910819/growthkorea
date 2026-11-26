#!/usr/bin/env bash
# 그로스코리아 GitHub Pages 배포 스크립트
#   사용: bash work/growthkorea-pages/deploy.sh [owner] [repo]
#
# 배포 구조 (메이트립 hya910819/matetrip 과 동일한 방식)
#  - 실제 게시 주소: https://<owner>.github.io/<repo>/          (홈페이지) · /rank/ (순위 대시보드)
#  - Pages source = gh-pages / root (legacy build)
#  - Pickle의 GitHub 앱 토큰에는 pages=write·administration=write·workflows 권한이 없어서
#    Pages 설정을 API로 바꾸거나 Actions 워크플로를 올릴 수 없다. 그래서 gh-pages 브랜치를
#    그대로 게시 소스로 쓰고, 배포할 때 main과 gh-pages를 함께 밀어 넣는다.
set -euo pipefail

OWNER="${1:-hya910819}"
REPO="${2:-growthkorea}"
REMOTE="https://github.com/${OWNER}/${REPO}.git"
DIR="$(cd "$(dirname "$0")" && pwd)"
SITE="https://${OWNER}.github.io/${REPO}"

cd "$DIR"

echo "== 1) 원격 확인: ${OWNER}/${REPO}"
if ! gh api "/repos/${OWNER}/${REPO}" --jq '.full_name' >/dev/null 2>&1; then
  echo "리포지토리가 없습니다. https://github.com/new 에서 '${REPO}' (Public) 생성 후 다시 실행하세요."; exit 1
fi

if git remote get-url origin >/dev/null 2>&1; then git remote set-url origin "$REMOTE"; else git remote add origin "$REMOTE"; fi

echo "== 2) 배포본 동기화 (홈페이지 · vendor · rank)"
bash "$DIR/sync.sh"

echo "== 3) 커밋"
git add -A
if ! git diff --cached --quiet; then
  git -c user.name="이창희" -c user.email="${OWNER}@users.noreply.github.com" \
      commit -q -m "그로스코리아 홈페이지 · 플레이스 순위 대시보드 배포"
  echo "변경분 커밋 완료"
else
  echo "변경분 없음"
fi

echo "== 4) main · gh-pages 푸시"
if ! git push -u origin main 2>/tmp/gk_push.log; then
  cat /tmp/gk_push.log >&2
  echo "원격 main 에 이미 다른 커밋이 있어 푸시가 거절되었습니다."
  echo "  · 원격에 의미 있는 작업이 없다면: git push --force origin main"
  echo "  · 남길 작업이 있다면: git fetch origin main && git rebase origin/main (README.md 충돌 시 정리) 후 다시 실행"
  exit 1
fi
git branch -f gh-pages main
git push origin gh-pages --force

echo "== 5) Pages 상태"
for i in $(seq 1 12); do
  sleep 10
  code_root=$(curl -s -o /dev/null -w '%{http_code}' "$SITE/" || true)
  code_rank=$(curl -s -o /dev/null -w '%{http_code}' "$SITE/rank/" || true)
  echo "   시도 $i · / → HTTP $code_root · /rank/ → HTTP $code_rank"
  [ "$code_root" = "200" ] && [ "$code_rank" = "200" ] && break
done
gh api "/repos/${OWNER}/${REPO}/pages" --jq '{url: .html_url, status: .status, source: .source.branch}' 2>/dev/null || true
echo "게시 주소: $SITE/  ·  $SITE/rank/"
