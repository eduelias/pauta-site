PW := uv run --no-project --with playwright==1.64.1 --with pillow

.PHONY: serve seo seo-write check shots images live

serve:  ## preview on http://localhost:8091
	python3 -m http.server 8091 --bind 127.0.0.1 --directory site

seo:  ## FAQ JSON-LD, plan offers, sitemap and page chrome are in sync with the pages
	python3 tools/seo.py check

seo-write:  ## regenerate the FAQ JSON-LD and sitemap.xml, then check
	python3 tools/seo.py write

check: seo  ## seo, then old-link forwarding, console errors, local links (Chromium)
	$(PW) python tools/check.py

shots:  ## check, plus desktop and mobile screenshots in shots/
	$(PW) python tools/check.py --shots shots

images:  ## og.png and the campaign images (macOS: uses the system SF font)
	$(PW) python tools/render_images.py

live:  ## the live hosts: redirects, the site, old app links (app stubbed in the browser)
	$(PW) python tools/check_live.py
