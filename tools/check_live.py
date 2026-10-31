"""Check the live hosts: the redirects into www, the site, and old app links reaching the app.

Requests to app.pauta.cc are stubbed in the browser, so the app never sees the made-up
tokens; the app itself is only checked with a plain GET of its front page.

Run: make live
"""

import sys
import urllib.request

from playwright.sync_api import sync_playwright

APP = "https://app.pauta.cc/"
WWW = "https://www.pauta.cc/"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def head(url):
    opener = urllib.request.build_opener(NoRedirect)
    try:
        r = opener.open(urllib.request.Request(url, method="GET"), timeout=15)
        return r.status, r.headers
    except urllib.error.HTTPError as e:
        return e.code, e.headers


# 1. the redirects, hop by hop
for host in ("pauta.cc", "pauta.team", "www.pauta.team"):
    code, h = head(f"https://{host}/termos.html")
    check(code == 301 and h.get("Location") == WWW + "termos.html",
          f"https://{host}/termos.html -> {code} {h.get('Location')}")
code, h = head("http://www.pauta.cc/")
check(code == 301 and h.get("Location") == WWW, f"http://www.pauta.cc/ -> {code} {h.get('Location')}")
code, h = head(WWW)
check(code == 200 and h.get("Server") == "GitHub.com", f"{WWW} -> {code} from {h.get('Server')}")
code, h = head(APP)
check(code == 200 and h.get("Server") != "GitHub.com", f"{APP} -> {code} (the app, still on du7)")

# 2. old links in a real browser, through every redirect
with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context()
    ctx.route(APP + "**", lambda r: r.fulfill(status=200, content_type="text/html", body="app"))
    page = ctx.new_page()
    for start in ("https://pauta.cc/", "https://pauta.team/", "https://www.pauta.cc/",
                  "http://pauta.cc/"):
        for frag in ("#/mudar/live-check-token", "#/entrar/live-check-token"):
            page.goto(start + frag)
            page.wait_for_url(APP + "**")
            check(page.url == APP + frag, f"{start}{frag} -> {page.url}")
    page.goto("https://pauta.cc/")
    page.wait_for_load_state("load")
    check(page.url == WWW and "pauta" in page.title().lower(),
          f"https://pauta.cc/ -> {page.url} ({page.title()})")
    browser.close()

print(f"\n{len(failures)} failure(s)" if failures else "\nall good")
sys.exit(1 if failures else 0)
