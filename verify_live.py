#!/usr/bin/env python3
"""그로스코리아 GitHub Pages 라이브 검증 (v3 · 실제 Chromium)

    LD_LIBRARY_PATH=/workspace/.cache/chromedeps/usr/lib/x86_64-linux-gnu python3 verify_live.py

대상
  홈페이지      https://hya910819.github.io/growthkorea/
  순위 대시보드  https://hya910819.github.io/growthkorea/rank/
  크리에이터스   https://hya910819.github.io/growthkorea/creator/
  예약 보드      https://hya910819.github.io/growthkorea/wagzag-booking/
  메이트립      https://hya910819.github.io/matetrip/

화면
  데스크톱 1440×900 · 모바일 390×844

결과
  preview-live/verify-live-report.json · preview-live/*.png
  ../groskorea-website/preview/pc-home-v3.png · pc-work-v3.png · mobile-home-v3.png
"""
import json
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "preview-live"
PREVIEW = ROOT.parent / "groskorea-website" / "preview"
SITE = "https://hya910819.github.io/growthkorea"
PAGES = {
    "home": SITE + "/",
    "rank": SITE + "/rank/",
    "creator": SITE + "/creator/",
    "wagzag-booking": SITE + "/wagzag-booking/",
    "matetrip": "https://hya910819.github.io/matetrip/",
}

results = []


def check(name, ok, detail=""):
    results.append({"name": name, "ok": bool(ok), "detail": detail})
    print(("  PASS  " if ok else "  FAIL  ") + name + ((" · " + str(detail)) if detail else ""))


def http_code(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except Exception as e:  # noqa: BLE001
        return getattr(e, "code", str(e))


def main():
    OUT.mkdir(exist_ok=True)
    PREVIEW.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ---------- 1) HTTP 상태 ----------
        for name, url in PAGES.items():
            code = http_code(url)
            check(f"HTTP 200 · {name}", code == 200, code)
        for asset in ("assets/work-bar.webp", "assets/work-tech.webp", "vendor/three.min.js", "vendor/gsap.min.js"):
            code = http_code(f"{SITE}/{asset}")
            check(f"HTTP 200 · {asset}", code == 200, code)

        # ---------- 2) 홈 · 데스크톱 ----------
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        page = ctx.new_page()
        errors, page_errors, failed = [], [], []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on("requestfailed", lambda r: failed.append(r.url))
        page.goto(PAGES["home"], wait_until="networkidle")
        page.wait_for_timeout(2800)
        page.evaluate("document.fonts.ready")

        info = page.evaluate("""() => ({
          scrollWidth: document.documentElement.scrollWidth,
          innerWidth: window.innerWidth,
          imgs: Array.from(document.images).map(i => ({ src: i.currentSrc.split('/').pop(), w: i.naturalWidth })),
          hasGsap: document.documentElement.classList.contains('has-gsap'),
          noWebgl: document.documentElement.classList.contains('no-webgl'),
          h1: (document.querySelector('h1') || {}).innerText,
          cards: document.querySelectorAll('.work').length,
          gross: (document.body.innerHTML.match(/GROSS/g) || []).length
        })""")
        check("홈: 콘솔 오류 0", len(errors) == 0, errors[:3])
        check("홈: 페이지 오류 0", len(page_errors) == 0, page_errors[:3])
        check("홈: 실패 요청 0", len(failed) == 0, failed[:3])
        check("홈: 가로 스크롤 없음", info["scrollWidth"] <= info["innerWidth"], f'{info["scrollWidth"]}/{info["innerWidth"]}')
        check("홈: 이미지 로드", all(i["w"] > 0 for i in info["imgs"]) and len(info["imgs"]) >= 4, info["imgs"][:2])
        check("홈: WebGL · GSAP", (not info["noWebgl"]) and info["hasGsap"])
        check("홈: H1", "브랜드는" in info["h1"], info["h1"].replace("\n", " / "))
        check("홈: 케이스 4건", info["cards"] == 4, info["cards"])
        check("홈: GROSS 표기 0", info["gross"] == 0, info["gross"])

        page.screenshot(path=str(PREVIEW / "pc-home-v3.png"))
        page.screenshot(path=str(OUT / "01-home-desktop-v3.png"))

        # 워크 그리드 (카드가 보이는 위치)
        page.evaluate("""() => {
          document.documentElement.style.scrollBehavior = 'auto';
          const y = document.getElementById('work').getBoundingClientRect().top + window.scrollY;
          window.scrollTo(0, y + 150);
        }""")
        page.wait_for_timeout(1500)
        page.screenshot(path=str(PREVIEW / "pc-work-v3.png"))
        page.screenshot(path=str(OUT / "02-work-desktop-v3.png"))

        # 필터
        page.click('.filters button[data-filter="tech"]')
        page.wait_for_timeout(600)
        tech = page.evaluate("() => Array.from(document.querySelectorAll('.work')).filter(c => !c.hidden).length")
        check("홈: 필터(퍼포먼스·테크) 2건", tech == 2, tech)
        page.click('.filters button[data-filter="all"]')
        page.wait_for_timeout(500)

        # 모달
        page.click('.work[data-case="wagzag"] .work__open')
        page.wait_for_timeout(800)
        modal = page.evaluate("""() => {
          const m = document.getElementById('caseModal');
          return { hidden: m.hidden, title: (document.getElementById('caseTitle') || {}).innerText,
                   steps: m.querySelectorAll('.case__step').length, links: m.querySelectorAll('.case__links a').length };
        }""")
        check("홈: 케이스 모달 열림", modal["hidden"] is False and modal["title"] == "와그자그 교동점", modal)
        check("홈: 모달 4단계", modal["steps"] == 4, modal["steps"])
        page.screenshot(path=str(OUT / "03-case-modal-desktop-v3.png"))
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        check("홈: 모달 ESC 닫힘", page.evaluate("() => document.getElementById('caseModal').hidden") is True)

        # 앵커
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        page.click('.nav a[data-nav="contact"]')
        page.wait_for_timeout(1600)
        anchor = page.evaluate("() => Math.round(document.getElementById('contact').getBoundingClientRect().top)")
        check("홈: 앵커 이동(헤더에 가리지 않음)", 60 <= anchor <= 120, anchor)

        # 폼
        page.click(".form__submit")
        page.wait_for_timeout(400)
        errs = page.evaluate("() => Array.from(document.querySelectorAll('.field__err')).map(e => e.textContent.trim()).filter(Boolean).length")
        check("홈: 폼 필수 검증", errs == 3, errs)
        ctx.close()

        # ---------- 3) 홈 · 모바일 ----------
        ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
        page = ctx.new_page()
        merr = []
        page.on("console", lambda m: merr.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: merr.append(str(e)))
        page.goto(PAGES["home"], wait_until="networkidle")
        page.wait_for_timeout(2600)
        m = page.evaluate("() => ({ sw: document.documentElement.scrollWidth, iw: window.innerWidth })")
        check("모바일: 가로 스크롤 없음", m["sw"] <= m["iw"], f'{m["sw"]}/{m["iw"]}')
        check("모바일: 콘솔 오류 0", len(merr) == 0, merr[:2])
        page.screenshot(path=str(PREVIEW / "mobile-home-v3.png"))
        page.screenshot(path=str(OUT / "04-home-mobile-v3.png"))
        page.click("#burger")
        page.wait_for_timeout(700)
        check("모바일: 드로어", page.evaluate("() => document.getElementById('menu').classList.contains('is-open')"))
        page.click('.menu a[href="#work"]')
        page.wait_for_timeout(1300)
        page.screenshot(path=str(OUT / "05-work-mobile-v3.png"))
        page.click('.work[data-case="roomnonda"] .work__open')
        page.wait_for_timeout(800)
        check("모바일: 모달", page.evaluate("() => !document.getElementById('caseModal').hidden"))
        page.screenshot(path=str(OUT / "06-case-modal-mobile-v3.png"))
        ctx.close()

        # ---------- 4) 다른 페이지 ----------
        for name in ("rank", "creator", "wagzag-booking"):
            ctx = browser.new_context(viewport={"width": 1440, "height": 900})
            page = ctx.new_page()
            errs, bad = [], []
            page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: bad.append(str(e)))
            page.goto(PAGES[name], wait_until="networkidle")
            page.wait_for_timeout(1400)
            st = page.evaluate("() => ({ sw: document.documentElement.scrollWidth, iw: window.innerWidth, title: document.title })")
            check(f"{name}: 스크롤·오류 없음", st["sw"] <= st["iw"] and not errs and not bad, f'{st["sw"]}/{st["iw"]} · {errs[:1]}')
            page.screenshot(path=str(OUT / f"07-{name}-desktop-v3.png"))
            ctx.close()

        browser.close()

    report = {"at": time.strftime("%Y-%m-%d %H:%M:%S"), "total": len(results),
              "passed": sum(1 for r in results if r["ok"]), "failed": [r for r in results if not r["ok"]], "checks": results}
    (OUT / "verify-live-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{report['passed']}/{report['total']} 통과")
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
