"""Check the site in a real browser before it goes live, and optionally take screenshots.

- Old app links: every page, reached directly or through a 301 (like pauta.cc -> www), sends
  `#/...` fragments on to https://app.pauta.cc/#/... and doesn't forward ordinary anchors.
- No console errors, and every local link and asset answers 200.
- `--shots DIR`: full-page desktop (1440 wide) and mobile (390 wide) screenshots, light and dark.

Run: make check   (or: uv run --no-project --with playwright==1.64.1 python tools/check.py)
"""

import argparse
import functools
import http.server
import re
import sys
import threading
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright

SITE = Path(__file__).resolve().parent.parent / "site"
PAGES = ["/", "/termos.html", "/privacidade.html", "/reembolso.html", "/nao-existe"]
APP = "https://app.pauta.cc/"


class Static(http.server.SimpleHTTPRequestHandler):
    """Like GitHub Pages: unknown paths get 404.html with a 404 status."""

    def send_error(self, code, message=None, explain=None):
        if code != 404:
            return super().send_error(code, message, explain)
        body = (SITE / "404.html").read_bytes()
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def serve(handler):
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_address[1]}"


def redirector(target):
    """A stand-in for Caddy's `redir https://www.pauta.cc{uri} 301` on the apex."""

    class R(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(301)
            self.send_header("Location", target + self.path)
            self.end_headers()

        def log_message(self, *a):
            pass

    return serve(R)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", type=Path, help="write screenshots here")
    args = ap.parse_args()

    base = serve(functools.partial(Static, directory=str(SITE)))
    apex = redirector(base)
    failures = []

    def check(ok, what):
        print(("ok   " if ok else "FAIL ") + what)
        if not ok:
            failures.append(what)

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context()
        app_hits = []

        def fake_app(route):
            app_hits.append(route.request.url)
            route.fulfill(status=200, content_type="text/html", body="<p>app</p>")

        ctx.route(APP + "**", fake_app)
        page = ctx.new_page()
        errors = []
        page.on("console", lambda m: m.type == "error" and errors.append(m.text))
        page.on("pageerror", lambda e: errors.append(str(e)))

        # 1. old app links are forwarded, straight or through the apex's 301
        for origin, label in ((base, "www"), (apex, "apex 301 -> www")):
            for path in PAGES:
                for frag in ("#/mudar/tok-ABC_123", "#/entrar/xyz", "#/"):
                    page.goto(origin + path + frag)
                    page.wait_for_url(APP + "**")
                    check(page.url == APP + frag, f"{label} {path}{frag} -> {page.url}")

        # 2. ordinary anchors and plain pages stay on the site
        app_hits.clear()
        errors.clear()
        for path in PAGES:
            for frag in ("", "#planos", "#beta"):
                page.goto(base + path + frag)
                page.wait_for_load_state("load")
                if path == "/nao-existe":  # the page's own 404 status is logged as an error
                    errors[:] = [e for e in errors if "404" not in e]
                check(
                    page.url.startswith(base) and page.locator("header.top").is_visible(),
                    f"stays {path}{frag}",
                )
        check(not app_hits, f"no request to the app from ordinary pages {app_hits}")
        check(not errors, f"no console errors {errors}")

        # 3. local links and assets answer 200
        seen = set()
        for path in PAGES[:-1]:
            page.goto(base + path)
            html = page.content()
            for ref in re.findall(r'(?:href|src)="([^"#]+)', html):
                url = urljoin(base + path, ref)
                if urlparse(url).netloc != urlparse(base).netloc or url in seen:
                    continue
                seen.add(url)
                r = page.request.get(url)
                check(r.status == 200, f"{r.status} {url[len(base):]}")
        r = page.request.get(base + "/nao-existe")
        check(r.status == 404, "unknown path is a 404 with 404.html")

        # 4. screenshots
        if args.shots:
            args.shots.mkdir(parents=True, exist_ok=True)
            sizes = {
                "desktop": dict(viewport={"width": 1440, "height": 900}),
                "mobile": dict(
                    viewport={"width": 390, "height": 844},
                    device_scale_factor=3,
                    is_mobile=True,
                    has_touch=True,
                ),
            }
            for name, opts in sizes.items():
                for scheme in ("light", "dark"):
                    c = browser.new_context(color_scheme=scheme, **opts)
                    p = c.new_page()
                    for path, slug in (("/", "home"), ("/termos.html", "termos")):
                        if slug == "termos" and scheme == "dark":
                            continue
                        p.goto(base + path)
                        out = args.shots / f"{slug}-{name}-{scheme}.png"
                        p.screenshot(path=str(out), full_page=True)
                        print("shot", out)
                    c.close()
        browser.close()

    print(f"\n{len(failures)} failure(s)" if failures else "\nall good")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
