#!/usr/bin/env python3
"""라이브 데스크톱(1440x900) 섹션 캡처 + 표/레이아웃 확인"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / "preview-live"
res = {}

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)[:200]))

    page.goto("https://hya910819.github.io/growthkorea/", wait_until="load")
    page.wait_for_timeout(3500)
    for sel, nm in [("#services", "d-home-services"), ("#process", "d-home-process"),
                    ("#channels", "d-home-channels"), ("footer", "d-home-footer")]:
        loc = page.locator(sel).first
        loc.scroll_into_view_if_needed()
        page.wait_for_timeout(600)
        loc.screenshot(path=str(OUT / f"{nm}.png"))

    # 문의 모달(프로젝트 문의) 동작
    page.evaluate("window.scrollTo(0,0)")
    page.wait_for_timeout(600)
    page.locator("button[data-open-consult]").first.click()
    page.wait_for_timeout(1200)
    page.screenshot(path=str(OUT / "d-home-consult-modal.png"))
    res["consult_modal"] = page.evaluate("""() => {
      const d = document.querySelector('dialog[open], [role=dialog], .consult, [class*=modal]');
      if (!d) return null;
      const r = d.getBoundingClientRect();
      return {cls: d.className.toString().slice(0,50), w: Math.round(r.width), h: Math.round(r.height),
              left: Math.round(r.left), right: Math.round(r.right), innerWidth: window.innerWidth,
              text: (d.innerText||'').replace(/\\s+/g,' ').slice(0,120)};
    }""")
    page.keyboard.press("Escape")
    page.wait_for_timeout(600)

    # 순위 대시보드 데스크톱 표
    page.goto("https://hya910819.github.io/growthkorea/rank/", wait_until="load")
    page.wait_for_timeout(2000)
    res["rank_desktop_table"] = page.evaluate("""() => {
      const t = document.querySelector('table');
      if (!t) return null;
      const r = t.getBoundingClientRect();
      const clipped = [];
      for (const c of t.querySelectorAll('td, th')) {
        if (c.scrollWidth > c.clientWidth + 2) clipped.push({text: (c.innerText||'').slice(0,20), sw: c.scrollWidth, cw: c.clientWidth});
      }
      let scroller = null, el = t.parentElement;
      while (el && el !== document.body) {
        const cs = getComputedStyle(el);
        if (/(auto|scroll)/.test(cs.overflowX)) { scroller = {cls: el.className.toString().slice(0,30), sw: el.scrollWidth, cw: el.clientWidth}; break; }
        el = el.parentElement;
      }
      return {w: Math.round(r.width), left: Math.round(r.left), right: Math.round(r.right),
              innerWidth: window.innerWidth, scroller, clippedCount: clipped.length, clipped: clipped.slice(0,8)};
    }""")
    t = page.locator("table").first
    t.scroll_into_view_if_needed()
    page.wait_for_timeout(800)
    page.screenshot(path=str(OUT / "d-rank-table.png"))

    # 행 클릭 → 상세/추이
    page.evaluate("window.scrollTo(0,0)")
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT / "d-rank-mid.png"))

    # 메이트립 데스크톱
    page.goto("https://hya910819.github.io/matetrip/", wait_until="load")
    page.wait_for_timeout(2500)
    page.screenshot(path=str(OUT / "d-matetrip-top.png"))
    res["matetrip_desktop_overflow"] = page.evaluate("""() => {
      const out = [];
      for (const s of document.querySelectorAll('section, footer, header')) {
        if (s.scrollWidth > window.innerWidth + 1) out.push({cls: s.className.toString().slice(0,30), sw: s.scrollWidth, cw: s.clientWidth});
      }
      return out;
    }""")

    res["errors"] = errs
    ctx.close()
    b.close()

print(json.dumps(res, ensure_ascii=False, indent=2))
