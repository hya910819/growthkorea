#!/usr/bin/env python3
"""앵커 이동 시 고정 헤더 가림 여부 · skip 링크 기본 상태 확인"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / "preview-live"
res = {}
with sync_playwright() as p:
    b = p.chromium.launch()
    for vp, w, h in [("desktop", 1440, 900), ("mobile", 390, 844)]:
        ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=1,
                            is_mobile=(vp == "mobile"), has_touch=(vp == "mobile"))
        pg = ctx.new_page()
        pg.goto("https://hya910819.github.io/growthkorea/", wait_until="load")
        pg.wait_for_timeout(3000)
        res[vp] = {}
        res[vp]["skip_top_unfocused"] = pg.evaluate("() => getComputedStyle(document.querySelector('.skip')).top")
        res[vp]["header_h"] = pg.evaluate("() => Math.round(document.querySelector('header').getBoundingClientRect().height)")
        for anchor in ["#about", "#services", "#process", "#channels"]:
            pg.evaluate("window.scrollTo(0,0)")
            pg.wait_for_timeout(900)
            if vp == "desktop":
                pg.locator(f'nav.nav a[href="{anchor}"]').first.click()
            else:
                pg.locator("#navToggle").click()
                pg.wait_for_timeout(800)
                pg.locator(f'#drawer a[href="{anchor}"]').first.click()
            pg.wait_for_timeout(1600)
            info = pg.evaluate("""(a) => {
                const s = document.querySelector(a);
                const h = document.querySelector('header').getBoundingClientRect().height;
                const head = s.querySelector('.sec__head, .sec-head, h2, .eyebrow, .sec__label') || s;
                const r = head.getBoundingClientRect();
                return {headerH: Math.round(h), headTop: Math.round(r.top),
                        headText: (head.innerText||'').replace(/\\s+/g,' ').slice(0,40),
                        scrollY: Math.round(window.scrollY)};
            }""", anchor)
            res[vp][anchor] = info
            pg.screenshot(path=str(OUT / f"anchor-{vp}-{anchor[1:]}.png"))
        ctx.close()
    b.close()
print(json.dumps(res, ensure_ascii=False, indent=2))
