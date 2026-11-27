#!/usr/bin/env python3
"""그로스코리아 Pages 배포본 로컬 검증 (실제 Chromium)

    LD_LIBRARY_PATH=/workspace/.cache/chromedeps/usr/lib/x86_64-linux-gnu python3 verify_pages.py

확인 항목
  1) /            — 200, 홈페이지 렌더(히어로·섹션), 로컬 에셋(vendor/*) 200, 3D 캔버스 초기화
  2) /rank/       — 200, 대시보드 KPI·표 렌더, 외부 요청 0건(localStorage 저장)
  3) /rank        — 301/302 → /rank/ 로 이동
  4) 홈페이지 v3 — 케이스 카드 4건, 메이트립/순위/크리에이터스 링크, 섹션 5개
  5) 콘솔 오류·페이지 오류·로컬 실패 요청 0건 (외부 CDN 실패는 따로 집계 — 로컬 폴백이 있으면 통과)
결과: verify_pages-report.json / preview-*.png
"""
import http.server
import json
import os
import socketserver
import threading
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
PREVIEW = ROOT / "preview"
PORT = 8833
BASE = f"http://127.0.0.1:{PORT}"
MATETRIP = "https://hya910819.github.io/matetrip/"

checks = []
console_errors, page_errors, failed_local, failed_external = [], [], [], []


def serve():
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(ROOT), **kw)

        def log_message(self, *args):
            pass

    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def check(name, ok, detail=""):
    checks.append({"name": name, "ok": bool(ok), "detail": str(detail)[:400]})
    print(("PASS " if ok else "FAIL ") + name + ((" · " + str(detail)[:160]) if detail != "" else ""))
    return bool(ok)


def attach(page, tag):
    def on_console(m):
        if m.type == "error":
            console_errors.append({"screen": tag, "text": m.text[:300]})

    def on_failed(req):
        url = req.url
        item = {"screen": tag, "url": url[:200], "reason": str(req.failure)[:120]}
        if url.startswith(BASE):
            failed_local.append(item)
        else:
            failed_external.append(item)

    page.on("console", on_console)
    page.on("pageerror", lambda e: page_errors.append({"screen": tag, "text": str(e)[:300]}))
    page.on("requestfailed", on_failed)


def status(url, follow=False):
    """로컬 서버 응답 코드 (리다이렉트 미추적)"""
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **kw):
            return None

    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(url, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def main():
    PREVIEW.mkdir(exist_ok=True)
    httpd = serve()
    report = {}
    try:
        # ---------- HTTP 레벨 ----------
        check("HTTP 200 · /", status(f"{BASE}/") == 200)
        check("HTTP 200 · /rank/", status(f"{BASE}/rank/") == 200)
        check("HTTP 200 · /index.html", status(f"{BASE}/index.html") == 200)
        for name in ["three.module.min.js", "three.min.js", "gsap.min.js", "ScrollTrigger.min.js"]:
            check(f"HTTP 200 · /vendor/{name}", status(f"{BASE}/vendor/{name}") == 200)
        check("HTTP 200 · /.nojekyll", status(f"{BASE}/.nojekyll") == 200)
        loc_rank = status(f"{BASE}/rank")
        check("/rank (슬래시 없음) 리다이렉트", loc_rank in (301, 302, 307, 308), f"HTTP {loc_rank}")

        with sync_playwright() as p:
            browser = p.chromium.launch()

            # ---------- 홈페이지 ----------
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            attach(page, "home")
            page.goto(f"{BASE}/", wait_until="load")
            page.wait_for_timeout(4500)

            check("홈 · title", "그로스코리아" in page.title(), page.title())
            check("홈 · 히어로 헤딩", page.locator("h1").first.is_visible())
            hero_txt = page.locator("h1").first.inner_text().replace("\n", " ")
            check("홈 · 히어로 문구", "브랜드는" in hero_txt, hero_txt[:80])

            check("홈 · 케이스 카드 4건", page.locator(".work").count() == 4, page.locator(".work").count())
            check("홈 · 메이트립 링크", page.locator('a[href="' + MATETRIP + '"]').count() >= 1)
            check("홈 · 순위 대시보드 링크", page.locator('a[href$="/growthkorea/rank/"]').count() >= 1)

            # 섹션·3D
            for sel, nm in [("#identity", "Identity"), ("#work", "Work"), ("#capabilities", "Capabilities"), ("#process", "Process"), ("#contact", "Contact")]:
                check(f"홈 · 섹션 {sel}", page.locator(sel).count() > 0)
            # 주의: 캔버스에 getContext('2d')를 호출하면 three.js의 WebGL 초기화가 깨진다.
            # 이미 만들어진 컨텍스트를 그대로 돌려받는 webgl2→webgl 순서로만 확인한다.
            canvas = page.evaluate(
                """() => {
                  const list = [...document.querySelectorAll('canvas')];
                  const c = list[0];
                  if (!c) return {canvas:false};
                  let gl = false;
                  try { gl = !!(c.getContext('webgl2') || c.getContext('webgl')); } catch(e) { gl = false; }
                  return {canvas:true, count:list.length, w:c.width, h:c.height, gl:gl,
                          three: !!window.THREE, gsap: !!window.gsap};
                }"""
            )
            check("홈 · 캔버스·WebGL 초기화", canvas.get("canvas") and canvas.get("gl") and canvas.get("w", 0) > 0, json.dumps(canvas)[:200])
            offscreen = page.evaluate(
                """() => {
                  const t = document.querySelector('.offline-fallback, [data-offline]');
                  return t ? t.className + '|' + getComputedStyle(t).display : null;
                }"""
            )
            report["home_canvas"] = canvas
            report["home_offline_fallback"] = offscreen

            # 스크롤해서 지연 로딩되는 요소까지 확인
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1200)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(600)
            page.screenshot(path=str(PREVIEW / "01-home-desktop.png"), full_page=False)

            scroll_w = page.evaluate("document.documentElement.scrollWidth")
            check("홈 · 가로 스크롤 없음(1440)", scroll_w <= 1441, f"scrollWidth={scroll_w}")

            page.set_viewport_size({"width": 390, "height": 844})
            page.wait_for_timeout(800)
            page.screenshot(path=str(PREVIEW / "02-home-mobile.png"), full_page=False)
            scroll_w_m = page.evaluate("document.documentElement.scrollWidth")
            check("홈 · 가로 스크롤 없음(390)", scroll_w_m <= 391, f"scrollWidth={scroll_w_m}")
            page.close()

            # ---------- CDN 차단 시 로컬 vendor 폴백 ----------
            fb = browser.new_page(viewport={"width": 1280, "height": 800})
            attach(fb, "home-offline")
            fb.route("**cdn.jsdelivr.net/**", lambda route: route.abort())
            fb.route("**fonts.googleapis.com/**", lambda route: route.abort())
            fb.route("**fonts.gstatic.com/**", lambda route: route.abort())
            fb.goto(f"{BASE}/", wait_until="load")
            fb.wait_for_timeout(5000)
            fbres = fb.evaluate(
                """() => {
                  const list = [...document.querySelectorAll('canvas')];
                  const c = list[0];
                  let gl = false;
                  try { gl = c ? !!(c.getContext('webgl2') || c.getContext('webgl')) : false; } catch(e) { gl = false; }
                  return {canvas: !!c, gl: gl, three: !!window.THREE, gsap: !!window.gsap,
                          vendor: performance.getEntriesByType('resource').map(r=>r.name).filter(n=>n.includes('/vendor/')),
                          h1: (document.querySelector('h1')||{}).innerText || ''};
                }"""
            )
            report["home_offline"] = fbres
            check("홈 · CDN 차단 시 로컬 vendor 폴백 로드", len(fbres.get("vendor", [])) >= 1, str(fbres.get("vendor"))[:200])
            check("홈 · CDN 차단 시 3D 캔버스 유지", fbres.get("canvas") and fbres.get("gl"), json.dumps(fbres)[:200])
            check("홈 · CDN 차단 시 히어로 텍스트 표시", "브랜드는" in (fbres.get("h1") or "").replace("\n", " "), (fbres.get("h1") or "")[:80])
            fb.screenshot(path=str(PREVIEW / "03-home-offline-cdn-blocked.png"))
            fb.close()

            # ---------- 순위 대시보드 ----------
            dpage = browser.new_page(viewport={"width": 1440, "height": 900})
            attach(dpage, "rank")
            dpage.goto(f"{BASE}/rank/", wait_until="load")
            dpage.wait_for_timeout(1500)

            check("랭크 · title", "플레이스 순위" in dpage.title(), dpage.title())
            kpi = dpage.locator(".kpi, [class*=kpi]").count()
            check("랭크 · KPI 렌더", kpi >= 4, f"kpi 요소 {kpi}개")
            rows = dpage.locator("table tbody tr").count()
            check("랭크 · 순위표 행", rows >= 10, f"{rows}행")
            check("랭크 · 그로스코리아 표기", "그로스코리아" in dpage.content())
            check("랭크 · 샘플 데이터 로드", dpage.evaluate("!!(localStorage.getItem('gk.placeRank.v2') || localStorage.getItem('gk.placeRank.v1'))"))
            ext = dpage.evaluate(
                """() => performance.getEntriesByType('resource')
                    .filter(r => !r.name.startsWith(location.origin) && !r.name.startsWith('data:'))
                    .map(r => r.name)"""
            )
            check("랭크 · 외부 요청 0건", len(ext) == 0, str(ext)[:200])
            dpage.screenshot(path=str(PREVIEW / "04-rank-desktop.png"))
            scroll_wr = dpage.evaluate("document.documentElement.scrollWidth")
            check("랭크 · 가로 스크롤 없음(1440)", scroll_wr <= 1441, f"scrollWidth={scroll_wr}")

            dpage.set_viewport_size({"width": 390, "height": 844})
            dpage.wait_for_timeout(700)
            dpage.screenshot(path=str(PREVIEW / "05-rank-mobile.png"))
            scroll_wrm = dpage.evaluate("document.documentElement.scrollWidth")
            check("랭크 · 가로 스크롤 없음(390)", scroll_wrm <= 391, f"scrollWidth={scroll_wrm}")

            # 리포트 화면(해시 라우팅) 동작 확인
            dpage.goto(f"{BASE}/rank/#report", wait_until="load")
            dpage.wait_for_timeout(1200)
            check("랭크 · #report 라우팅", dpage.locator("body").inner_text().count("리포트") > 0)
            dpage.close()
            browser.close()
    finally:
        httpd.shutdown()

    # CDN 차단 테스트(home-offline)에서 나오는 외부 리소스 로드 실패는 의도된 결과이므로 제외한다.
    real_console_errors = [
        e for e in console_errors
        if not (e["screen"] == "home-offline" and "ERR_FAILED" in e["text"])
    ]
    check("콘솔 오류 0건", len(real_console_errors) == 0, json.dumps(real_console_errors, ensure_ascii=False)[:300])
    check("페이지 오류 0건", len(page_errors) == 0, json.dumps(page_errors, ensure_ascii=False)[:300])
    check("로컬 실패 요청 0건", len(failed_local) == 0, json.dumps(failed_local, ensure_ascii=False)[:300])

    report.update(
        {
            "checks": checks,
            "passed": sum(1 for c in checks if c["ok"]),
            "total": len(checks),
            "console_errors": console_errors,
            "page_errors": page_errors,
            "failed_local": failed_local,
            "failed_external": failed_external,
            "note": "home-offline 화면에서 기록된 외부 리소스 실패는 CDN 차단 테스트(의도된 결과)이며, 판정에서는 제외했습니다.",
        }
    )
    (ROOT / "verify_pages-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n결과: {report['passed']}/{report['total']} 통과 · 외부 CDN 실패 {len(failed_external)}건(로컬 폴백 사용)")
    if failed_external:
        for f in failed_external[:5]:
            print("  외부:", f["url"])
    ok = report["passed"] == report["total"]
    print("전체 통과" if ok else "실패 항목 있음")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
