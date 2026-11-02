"""Keep the site's SEO bits in sync with the pages, or fail when they aren't.

- FAQ: the `FAQPage` JSON-LD in site/index.html is generated from the FAQ section's
  <details>/<summary> pairs, between the `seo:faq` markers in <head>.
- Plans: every Offer in the `SoftwareApplication` JSON-LD must match a plan card (name and
  price) in the Planos section, and the other way round.
- Sitemap: site/sitemap.xml lists every page but 404.html, with `lastmod` from the last git
  commit that touched the page (today for a page with uncommitted changes).
- Chrome: every page's <header class="top"> and <footer> are byte-for-byte the ones in
  index.html, so a nav change in one page can't be forgotten in another.

Run: make seo         (check; `make check` runs it first)
     make seo-write   (rewrite the FAQ JSON-LD and the sitemap, then check)
No dependencies beyond Python 3.11 and git.
"""

import datetime as dt
import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
ORIGIN = "https://www.pauta.cc"
FAQ_MARK = ("<!-- seo:faq -->", "<!-- /seo:faq -->")
INDENT = "  "


def pages():
    """Every published page, as site-relative paths, index first."""
    found = sorted(p for p in SITE.rglob("*.html") if p.name != "404.html")
    return sorted(found, key=lambda p: (p != SITE / "index.html", str(p)))


def url_of(page):
    rel = page.relative_to(SITE).as_posix()
    if rel.endswith("index.html"):
        rel = rel[: -len("index.html")]
    return f"{ORIGIN}/{rel}"


def text(fragment):
    """Visible text of an HTML fragment, whitespace collapsed."""
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", fragment))).strip()


# ---- FAQ ------------------------------------------------------------------------------


def faq_items(index_html):
    section = re.search(r'<div class="faq">(.*?)</div>\s*</div>\s*</section>', index_html, re.S)
    if not section:
        sys.exit("index.html: no <div class=\"faq\"> section")
    items = re.findall(r"<details>\s*<summary>(.*?)</summary>(.*?)</details>", section.group(1), re.S)
    if not items:
        sys.exit("index.html: the FAQ section has no <details>")
    return [(text(q), text(a)) for q, a in items]


def faq_jsonld(items):
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in items
        ],
    }
    body = json.dumps(data, ensure_ascii=False, indent=2)
    body = "\n".join(INDENT + line for line in body.splitlines())
    return (
        f"{FAQ_MARK[0]}\n{INDENT}<script type=\"application/ld+json\">\n{body}\n"
        f"{INDENT}</script>\n{INDENT}{FAQ_MARK[1]}"
    )


def faq_block(index_html):
    m = re.search(re.escape(FAQ_MARK[0]) + r".*?" + re.escape(FAQ_MARK[1]), index_html, re.S)
    if not m:
        sys.exit(f"index.html: no {FAQ_MARK[0]} ... {FAQ_MARK[1]} block in <head>")
    return m


# ---- plans ----------------------------------------------------------------------------


def html_plans(index_html):
    plans = re.findall(r'<div class="plan(?: hl)?">(.*?)</div>\s*(?=<div class="plan|</div>)', index_html, re.S)
    out = {}
    for block in plans:
        name = text(re.search(r"<h3>(.*?)</h3>", block, re.S).group(1))
        price = text(re.search(r'<div class="price">(.*?)</div>', block, re.S).group(1))
        amount = re.search(r"R\$\s*([\d.]+)", price).group(1).replace(".", "")
        out[name] = f"{int(amount):.2f}"
    return out


def jsonld_plans(index_html):
    out = {}
    for script in re.findall(r'<script type="application/ld\+json">(.*?)</script>', index_html, re.S):
        data = json.loads(script)
        for node in data.get("@graph", [data]):
            if node.get("@type") != "SoftwareApplication":
                continue
            for offer in node.get("offers", []):
                out[offer["name"]] = f"{float(offer['price']):.2f}"
    return out


# ---- sitemap --------------------------------------------------------------------------


def lastmod(page):
    rel = page.relative_to(ROOT).as_posix()
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", rel], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()
    if dirty:
        return dt.date.today().isoformat()
    out = subprocess.run(
        ["git", "log", "-1", "--format=%cs", "--", rel], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()
    return out or dt.date.today().isoformat()


def sitemap():
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for page in pages():
        lines.append(f"  <url><loc>{url_of(page)}</loc><lastmod>{lastmod(page)}</lastmod></url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


# ---- chrome ---------------------------------------------------------------------------


def chrome(page_html):
    header = re.search(r'<header class="top">.*?</header>', page_html, re.S)
    footer = re.search(r"<footer>.*?</footer>", page_html, re.S)
    return (header and header.group(0), footer and footer.group(0))


# ---- main -----------------------------------------------------------------------------


def main():
    write = len(sys.argv) > 1 and sys.argv[1] == "write"
    if len(sys.argv) > 1 and sys.argv[1] not in ("check", "write"):
        sys.exit(__doc__)
    failures = []

    def check(ok, what):
        print(("ok   " if ok else "FAIL ") + what)
        if not ok:
            failures.append(what)

    index = SITE / "index.html"
    index_html = index.read_text(encoding="utf-8")

    # FAQ JSON-LD
    want = faq_jsonld(faq_items(index_html))
    block = faq_block(index_html)
    if write and block.group(0) != want:
        index_html = index_html[: block.start()] + want + index_html[block.end():]
        index.write_text(index_html, encoding="utf-8")
        print("wrote the FAQPage JSON-LD in index.html")
    check(faq_block(index_html).group(0) == want, "FAQPage JSON-LD matches the FAQ section")

    # plans
    in_html, in_ld = html_plans(index_html), jsonld_plans(index_html)
    check(in_html == in_ld, f"SoftwareApplication offers match the plan cards {in_html} / {in_ld}")

    # sitemap
    want = sitemap()
    sm = SITE / "sitemap.xml"
    if write and (not sm.exists() or sm.read_text(encoding="utf-8") != want):
        sm.write_text(want, encoding="utf-8")
        print("wrote sitemap.xml")
    check(sm.exists() and sm.read_text(encoding="utf-8") == want, "sitemap.xml is current")

    # chrome, canonical, title, description, one h1
    ref = chrome(index_html)
    for page in pages():
        page_html = page.read_text(encoding="utf-8")
        rel = page.relative_to(SITE).as_posix()
        check(chrome(page_html) == ref, f"{rel}: header and footer are index.html's")
        canonical = re.search(r'<link rel="canonical" href="([^"]+)">', page_html)
        check(canonical and canonical.group(1) == url_of(page), f"{rel}: canonical is {url_of(page)}")
        check(len(re.findall(r"<h1[\s>]", page_html)) == 1, f"{rel}: exactly one <h1>")
        title = re.search(r"<title>(.*?)</title>", page_html, re.S)
        check(title and 10 <= len(text(title.group(1))) <= 65, f"{rel}: title is 10-65 characters")
        desc = re.search(r'<meta name="description" content="([^"]*)">', page_html)
        check(desc and 50 <= len(desc.group(1)) <= 160, f"{rel}: description is 50-160 characters")
        for script in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page_html, re.S):
            try:
                json.loads(script)
                check(True, f"{rel}: JSON-LD parses")
            except ValueError as e:
                check(False, f"{rel}: JSON-LD parses ({e})")

    print(f"\n{len(failures)} failure(s)" if failures else "\nall good")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
