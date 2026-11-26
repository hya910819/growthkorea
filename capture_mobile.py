#!/usr/bin/env python3
"""라이브 모바일(390x844) 섹션별 캡처 + 인터アクション 확인"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / "preview-live"
OUT.mkdir(exist_ok=True)
res = {}


def shot(page, sel, name):
    loc = page.locator(sel).first
    if loc.count() == 0:
        res[name] = "missing"
        return
    loc.scroll_into_view_if_needed()
    page.wait_for_timeout(700)
    loc.screenshot(path=str(OUT / f"m-{name}.png"))
    res[name] = loc.bounding_box()


with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2,
                        is_mobile=True, has_touch=True,
                        user_agent=("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"))
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)[:200]))

    # ---------------- 홈 ----------------
    page.goto("https://hya910819.github.io/growthkorea/", wait_until="load")
    page.wait_for_timeout(3500)

    # 햄버거 메뉴
    burger = page.locator("#navToggle").first
    res["burger_count"] = page.locator("#navToggle").count()
    if res["burger_count"]:
        burger.click()
        page.wait_for_timeout(800)
        page.screenshot(path=str(OUT / "m-home-menu-open.png"))
        res["menu_open_body_class"] = page.evaluate("document.body.className")
        res["menu_links_visible"] = page.locator("nav a:visible").count()
        page.keyboard.press("Escape")
        page.wait_for_timeout(600)

    for sel, nm in [("#services", "home-services"), ("#process", "home-process"),
                    ("#channels", "home-channels"), ("footer", "home-footer"),
                    ("#about", "home-about")]:
        shot(page, sel, nm)

    # 서비스 아코디언 열기
    row = page.locator("#services .svc__head, #services .acc__head, #services [role=button], #services button").first
    if row.count():
        row.scroll_into_view_if_needed()
        row.click()
        page.wait_for_timeout(900)
        page.screenshot(path=str(OUT / "m-home-services-open.png"))

    # 문의 CTA 동작(카카오 링크)
    kakao = page.locator('a[href*="kakao"]').first
    res["kakao_href"] = kakao.get_attribute("href") if kakao.count() else None

    # 섹션별 가로 넘침
    res["home_sections_overflow"] = page.evaluate("""() => {
      const out = [];
      for (const s of document.querySelectorAll('section, footer, header')) {
        if (s.scrollWidth > window.innerWidth + 1) {
          out.push({id: s.id || s.className.toString().slice(0,30), sw: s.scrollWidth, cw: s.clientWidth});
        }
      }
      return out;
    }""")

    # ---------------- 순위 대시보드 ----------------
    page.goto("https://hya910819.github.io/growthkorea/rank/", wait_until="load")
    page.wait_for_timeout(2000)
    table = page.locator("table")
    res["rank_table"] = page.evaluate("""() => {
      const t = document.querySelector('table');
      if (!t) return null;
      let scroller = null, el = t.parentElement;
      while (el && el !== document.body) {
        const cs = getComputedStyle(el);
        if (/(auto|scroll)/.test(cs.overflowX)) { scroller = {tag: el.tagName, cls: el.className.toString().slice(0,40), sw: el.scrollWidth, cw: el.clientWidth}; break; }
        el = el.parentElement;
      }
      const r = t.getBoundingClientRect();
      // 셀 텍스트 잘림 검사
      const clipped = [];
      for (const c of t.querySelectorAll('td, th')) {
        if (c.scrollWidth > c.clientWidth + 2) clipped.push({text: (c.innerText || '').slice(0, 25), sw: c.scrollWidth, cw: c.clientWidth});
      }
      return {tableW: Math.round(r.width), left: Math.round(r.left), right: Math.round(r.right), innerWidth: window.innerWidth, scroller, clipped: clipped.slice(0, 10), clippedCount: clipped.length};
    }""")
    # 표가 모바일에서 숨겨져 있으면 카드 목록 영역을 캡처
    res["rank_table_visible_mobile"] = page.locator("table").first.is_visible() if page.locator("table").count() else None
    head = page.locator("text=지점별 · 키워드별 순위").first
    if head.count():
        head.scroll_into_view_if_needed()
        page.wait_for_timeout(700)
        page.screenshot(path=str(OUT / "m-rank-list-top.png"))
        res["rank_list_of_clipped"] = page.evaluate("""() => {
          const out = [];
          const W = window.innerWidth;
          for (const el of document.querySelectorAll('main *')) {
            const r = el.getBoundingClientRect();
            if (r.width === 0) continue;
            if (el.scrollWidth > el.clientWidth + 2 && getComputedStyle(el).overflowX === 'hidden') {
              out.push({tag: el.tagName, cls: el.className.toString().slice(0,40), text: (el.innerText||'').slice(0,30), sw: el.scrollWidth, cw: el.clientWidth});
            }
          }
          return out.slice(0, 12);
        }""")
        page.evaluate("window.scrollBy(0, 700)")
        page.wait_for_timeout(700)
        page.screenshot(path=str(OUT / "m-rank-list-cards.png"))

    # 오늘 순위 입력 모달
    btn = page.get_by_role("button", name="순위 입력").locator("visible=true").first
    if btn.count():
        btn.click()
        page.wait_for_timeout(1200)
        page.screenshot(path=str(OUT / "m-rank-modal.png"))
        dlg = page.evaluate("""() => {
          const d = document.querySelector('[role=dialog], dialog[open], .modal, [class*=modal]');
          if (!d) return null;
          const r = d.getBoundingClientRect();
          return {cls: d.className.toString().slice(0,40), w: Math.round(r.width), h: Math.round(r.height),
                  left: Math.round(r.left), right: Math.round(r.right), innerWidth: window.innerWidth};
        }""")
        res["rank_modal"] = dlg
        # 닫기
        for c in ["[aria-label*=닫기]", "text=닫기", "[class*=close]", "text=취소"]:
            cl = page.locator(c).first
            if cl.count() and cl.is_visible():
                cl.click()
                page.wait_for_timeout(600)
                break
        res["modal_closed"] = page.evaluate("""() => !document.querySelector('dialog[open], [role=dialog]:not([hidden])')""")

    # 지점·키워드 탭
    tab = page.locator("text=지점·키워드").first
    if tab.count():
        tab.click()
        page.wait_for_timeout(1200)
        page.screenshot(path=str(OUT / "m-rank-stores.png"))
        res["rank_tab_sw"] = page.evaluate("document.documentElement.scrollWidth")
    rep = page.locator("text=리포트").first
    if rep.count():
        rep.click()
        page.wait_for_timeout(1200)
        page.screenshot(path=str(OUT / "m-rank-report.png"))
        res["rank_report_sw"] = page.evaluate("document.documentElement.scrollWidth")

    # ---------------- 메이트립 ----------------
    page.goto("https://hya910819.github.io/matetrip/", wait_until="load")
    page.wait_for_timeout(2500)
    page.screenshot(path=str(OUT / "m-matetrip-bottom-nav.png"))
    res["matetrip_sections_overflow"] = page.evaluate("""() => {
      const out = [];
      for (const s of document.querySelectorAll('section, footer, header')) {
        if (s.scrollWidth > window.innerWidth + 1) out.push({cls: s.className.toString().slice(0,30), sw: s.scrollWidth, cw: s.clientWidth});
      }
      return out;
    }""")
    # 카드 캡처
    card = page.locator("article, [class*=card]").first
    if card.count():
        card.scroll_into_view_if_needed()
        page.wait_for_timeout(600)
        card.screenshot(path=str(OUT / "m-matetrip-card.png"))

    res["errors"] = errs
    ctx.close()
    b.close()

print(json.dumps(res, ensure_ascii=False, indent=2))
