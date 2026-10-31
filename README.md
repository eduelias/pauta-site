# pauta-site

The public site of [Pauta](https://github.com/eduelias/pauta) at **https://www.pauta.cc**:
landing page, proposed plans, and draft terms, privacy and refund pages (needed for Paddle,
decision 6 in eduelias/pauta). Plain HTML and CSS, no framework, no trackers, no cookies.
The app itself is at https://app.pauta.cc and is not in this repo.

| Path | What |
|---|---|
| `site/` | Everything that is published. `CNAME` is `www.pauta.cc` |
| `tools/check.py` | Browser check: old app links forward, no console errors, local links answer |
| `tools/render_images.py` | `site/og.png` and the campaign images (macOS, SF font) |
| `campaign/` | Launch copy and images. Not published |

```bash
make serve    # http://localhost:8091
make check    # needs uv; Playwright's Chromium is installed once with
              # uv run --no-project --with playwright==1.64.1 playwright install chromium
make shots    # check + desktop/mobile screenshots in shots/
make images   # og.png and campaign/*.png
```

## Hosting

GitHub Pages, published by `.github/workflows/pages.yml` from `site/` on every push to `main`.
DNS is in `du7/dns-zone` (`pauta.tf`): `www.pauta.cc` is a DNS-only CNAME to
`eduelias.github.io`. The apex `pauta.cc`, `pauta.team` and `www.pauta.team` stay on du7's
Caddy as a 301 to `https://www.pauta.cc{uri}`.

## Old app links

Until 1.6.1 the app lived on the apex, so WhatsApp chats hold links like
`https://pauta.cc/#/mudar/<token>` and `#/entrar/<token>`. Browsers keep the `#fragment`
through the apex's 301 to www, so the first thing in every page's `<head>` is:

```js
if (location.hash.startsWith("#/")) location.replace("https://app.pauta.cc/" + location.hash)
```

Every new page must start with it too; `make check` tests every page, directly and through a
301. Ordinary anchors (`#planos`, `#beta`) don't start with `#/` and stay on the site.

## Before taking payments

- Prices on the page are marked as a proposal; the owner confirms them (decision 6).
- Termos, Privacidade and Reembolso are drafts for legal review; the highlighted bits are open.
- The beta contact channel is a placeholder (`data-contact` in `index.html`, `[CONTATO]` in the
  campaign, "canal de contato a definir" in the legal pages).
