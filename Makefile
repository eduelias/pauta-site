PW := uv run --no-project --with playwright==1.64.1 --with pillow

.PHONY: serve check shots images

serve:  ## preview on http://localhost:8091
	python3 -m http.server 8091 --bind 127.0.0.1 --directory site

check:  ## old-link forwarding, console errors, local links (Chromium)
	$(PW) python tools/check.py

shots:  ## check, plus desktop and mobile screenshots in shots/
	$(PW) python tools/check.py --shots shots

images:  ## og.png and the campaign images (macOS: uses the system SF font)
	$(PW) python tools/render_images.py
