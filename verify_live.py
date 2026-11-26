#!/usr/bin/env python3
"""그로스코리아 GitHub Pages 라이브 검증 (실제 Chromium)

    LD_LIBRARY_PATH=/workspace/.cache/chromedeps/usr/lib/x86_64-linux-gnu python3 verify_live.py

대상
  홈페이지   https://hya910819.github.io/growthkorea/
  순위 대시  https://hya910819.github.io/growthkorea/rank/
  메이트립   https://hya910819.github.io/matetrip/
화면
  데스크톱 1440x900 · 모바일 390x844

확인 항목
  1) HTTP 200
  2) 가로 스크롤 없음 (documentElement.scrollWidth <= innerWidth)
  3) 뷰포트 밖으로 삐져나온 요소(레이아웃 깨짐 후보) 0건
  4) 핵심 요소 렌더 (히어로·KPI·표 등)
  5) '체험단 사이트 보기' 클릭 → 메이트립 새 탭 이동
  6) 콘솔 오류·페이지 오류·로컬 실패 요청 0건
  7) 본문 텍스트 덤프 (오탈자 검수용)
결과: verify_live-report.json / preview-live/*.png / preview-live/text/*.txt
"""
import json
import re
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "preview-live"
TEXT = OUT / "text"

TARGETS = {
    "home": "https://hya910819.github.io/growthkorea/",
    "rank": "https://hya910819.github.io/growthkorea/rank/",
    "matetrip": "https://hya910819.github.io/matetrip/",
}
VIEWPORTS = [("desktop", 1440, 900), ("mobile", 390, 844)]

OVERFLOW_JS = """() => {
  const W = window.innerWidth;
  const bad = [];
  const seen = new Set();
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    if (r.right <= W + 1 && r.left >= -1) continue;
    // 조상이 가로 클리핑(overflow-x hidden/auto/scroll)이면 의도된 처리로 본다
    let clipped = false, p = el.parentElement;
    while (p && p !== document.documentElement) {
      const pcs = getComputedStyle(p);
      if (/(auto|scroll|hidden|clip)/.test(pcs.overflowX)) { clipped = true; break; }
      p = p.parentElement;
    }
    if (clipped) continue;
    const key = el.tagName + '|' + (el.className || '').toString() + '|' + Math.round(r.left) + '|' + Math.round(r.width);
    if (seen.has(key)) continue;
    seen.add(key);
    bad.push({
      tag: el.tagName.toLowerCase(),
      cls: (el.className || '').toString().slice(0, 70),
      id: el.id || '',
      left: Math.round(r.left), right: Math.round(r.right), w: Math.round(r.width),
      pos: cs.position,
      text: (el.innerText || '').replace(/\\s+/g, ' ').slice(0, 40)
    });
  }
  return {
    innerWidth: W,
    scrollWidth: document.documentElement.scrollWidth,
    bodyScrollWidth: document.body.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    scrollHeight: document.documentElement.scrollHeight,
    badCount: bad.length,
    bad: bad.slice(0, 20)
  };
}"""

checks = []
console_errors, page_errors, failed_requests = [], [], []


def check(name, ok, detail=""):
    checks.append({"name": name, "ok": bool(ok), "detail": str(detail)[:400]})
    print(("PASS " if ok else "FAIL ") + name + ((" · " + str(detail)[:200]) if detail != "" else ""))
    return bool(ok)


def http_status(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:  # noqa: BLE001
        return f"ERR {e}"


def attach(page, tag):
    page.on("console", lambda m: console_errors.append({"screen": tag, "text": m.text[:300]})
            if m.type == "error" else None)
    page.on("pageerror", lambda e: page_errors.append({"screen": tag, "text": str(e)[:300]}))
    page.on("requestfailed", lambda r: failed_requests.append(
        {"screen": tag, "url": r.url[:200], "reason": str(r.failure)[:120]}))
    page.on("response", lambda r: None)


def typo_scan(text):
    """기계적으로 걸러낼 수 있는 흔적만 (오탈자 최종 판단은 본문 덤프를 사람이 읽어 확인)"""
    issues = []
    if "\ufffd" in text:
        issues.append("U+FFFD 대체문자(인코딩 깨짐)")
    for pat, label in [(r"undefined", "undefined 노출"), (r"\bNaN\b", "NaN 노출"),
                       (r"lorem ipsum", "lorem ipsum"), (r"TODO|FIXME", "TODO/FIXME"),
                       (r"\?\?", "?? 물음표 연속"), (r"\u3131\u3131", "자모 반복")]:
        if re.search(pat, text, re.I):
            issues.append(label)
    if re.search(r"[ \t]{4,}", text):
        issues.append("공백 4칸 이상")
    return issues


def main():
    OUT.mkdir(exist_ok=True)
    TEXT.mkdir(exist_ok=True)
    report = {"targets": TARGETS, "screens": {}}

    # ---------- HTTP ----------
    for key, url in TARGETS.items():
        code = http_status(url)
        check(f"HTTP 200 · {key}", code == 200, f"HTTP {code} · {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--font-render-hinting=none"])

        for key, url in TARGETS.items():
            report["screens"][key] = {}
            for vp_name, w, h in VIEWPORTS:
                tag = f"{key}-{vp_name}"
                ctx = browser.new_context(
                    viewport={"width": w, "height": h},
                    device_scale_factor=2 if vp_name == "mobile" else 1,
                    is_mobile=(vp_name == "mobile"),
                    has_touch=(vp_name == "mobile"),
                    locale="ko-KR",
                    timezone_id="Asia/Seoul",
                    user_agent=("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
                                "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
                    if vp_name == "mobile" else None,
                )
                page = ctx.new_page()
                attach(page, tag)
                resp = page.goto(url, wait_until="load", timeout=60000)
                page.wait_for_timeout(4000)
                # 지연 로딩 요소까지 확인
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1500)
                page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(800)

                m = page.evaluate(OVERFLOW_JS)
                report["screens"][key][vp_name] = m
                check(f"{tag} · HTTP 상태", (resp.status if resp else None) == 200, resp.status if resp else "no response")
                check(f"{tag} · 가로 스크롤 없음 (scrollWidth<=innerWidth)",
                      m["scrollWidth"] <= m["innerWidth"],
                      f"scrollWidth={m['scrollWidth']} innerWidth={m['innerWidth']}")
                check(f"{tag} · 뷰포트 밖 요소 0건", m["badCount"] == 0,
                      json.dumps(m["bad"][:5], ensure_ascii=False))

                # 화면 캡처
                page.screenshot(path=str(OUT / f"{tag}-top.png"))
                page.screenshot(path=str(OUT / f"{tag}-full.png"), full_page=True)

                # 본문 텍스트 덤프
                body_text = page.locator("body").inner_text()
                (TEXT / f"{tag}.txt").write_text(body_text, encoding="utf-8")
                issues = typo_scan(body_text)
                check(f"{tag} · 표기 기계 검사", not issues, "; ".join(issues))

                # 화면별 핵심 요소
                if key == "home":
                    h1 = page.locator("h1").first
                    check(f"{tag} · 히어로 h1 표시", h1.is_visible())
                    check(f"{tag} · 히어로 문구", "브랜드는" in h1.inner_text(), h1.inner_text().replace("\n", " ")[:80])
                    if vp_name == "mobile":
                        link = page.locator('a:has-text("체험단 사이트 보기")').first
                        check(f"{tag} · 체험단 링크 href(모바일)",
                              link.first.get_attribute("href") == "https://hya910819.github.io/matetrip/",
                              link.first.get_attribute("href"))
                        with page.context.expect_page() as info_m:
                            link.first.click()
                        npm = info_m.value
                        npm.wait_for_load_state("load", timeout=60000)
                        check(f"{tag} · 체험단 링크 클릭 → 메이트립 이동",
                              npm.url.rstrip("/") == "https://hya910819.github.io/matetrip", npm.url)
                        npm.close()
                    if vp_name == "desktop":
                        link = page.locator('a:has-text("체험단 사이트 보기")').first
                        check(f"{tag} · 체험단 링크 href",
                              link.get_attribute("href") == "https://hya910819.github.io/matetrip/",
                              link.get_attribute("href"))
                        check(f"{tag} · 체험단 링크 target",
                              link.get_attribute("target") == "_blank", link.get_attribute("target"))
                        with page.context.expect_page() as info:
                            link.click()
                        np = info.value
                        np.wait_for_load_state("load", timeout=60000)
                        check(f"{tag} · 체험단 링크 클릭 → 메이트립 이동",
                              np.url.rstrip("/") == "https://hya910819.github.io/matetrip",
                              np.url)
                        np.screenshot(path=str(OUT / "click-matetrip-target.png"))
                        np.close()
                        # nav 앵커 동작
                        page.evaluate("window.scrollTo(0,0)")
                        page.wait_for_timeout(400)
                        nav = page.locator('a[href="#services"]').first
                        if nav.count() > 0:
                            nav.click()
                            page.wait_for_timeout(1200)
                            y = page.evaluate("window.scrollY")
                            check(f"{tag} · nav #services 앵커 스크롤", y > 100, f"scrollY={y}")
                    canvas = page.evaluate("""() => {
                        const c = document.querySelector('canvas');
                        if (!c) return {canvas:false};
                        let gl=false; try { gl = !!(c.getContext('webgl2')||c.getContext('webgl')); } catch(e) {}
                        return {canvas:true, gl, three: !!window.THREE, gsap: !!window.gsap};
                    }""")
                    check(f"{tag} · 3D 캔버스·라이브러리", canvas.get("canvas") and canvas.get("gl"),
                          json.dumps(canvas))
                if key == "rank":
                    kpi = page.locator(".kpi, [class*=kpi]").count()
                    rows = page.locator("table tbody tr").count()
                    check(f"{tag} · KPI 렌더", kpi >= 4, f"kpi {kpi}개")
                    check(f"{tag} · 순위표 행", rows >= 10, f"{rows}행")
                    check(f"{tag} · 그로스코리아 표기", "그로스코리아" in page.content())
                    # 표가 화면 안에 있는지(컨테이너 내부 스크롤 허용)
                    table_box = page.evaluate("""() => {
                        const t = document.querySelector('table');
                        if (!t) return null;
                        const r = t.getBoundingClientRect();
                        return {left: Math.round(r.left), right: Math.round(r.right), w: Math.round(r.width),
                                innerWidth: window.innerWidth};
                    }""")
                    report["screens"][key][vp_name]["table"] = table_box
                if key == "matetrip":
                    check(f"{tag} · 본문 렌더", len(body_text.strip()) > 100, f"{len(body_text.strip())}자")
                    # 상단 주요 링크/버튼 개수
                    links = page.locator("a").count()
                    check(f"{tag} · 링크 렌더", links >= 3, f"a {links}개")

                ctx.close()
        browser.close()

    real_console = [e for e in console_errors if "favicon" not in e["text"].lower()]
    check("콘솔 오류 0건", not real_console, json.dumps(real_console, ensure_ascii=False)[:300])
    check("페이지 오류 0건", not page_errors, json.dumps(page_errors, ensure_ascii=False)[:300])
    check("실패 요청 0건", not failed_requests, json.dumps(failed_requests[:5], ensure_ascii=False)[:400])

    report.update({
        "checks": checks,
        "passed": sum(1 for c in checks if c["ok"]),
        "total": len(checks),
        "console_errors": console_errors,
        "page_errors": page_errors,
        "failed_requests": failed_requests,
    })
    (ROOT / "verify_live-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n결과: {report['passed']}/{report['total']} 통과")
    ok = report["passed"] == report["total"]
    print("전체 통과" if ok else "실패 항목 있음")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
