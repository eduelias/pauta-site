# pauta-site

The public site of [Pauta](https://github.com/eduelias/pauta) at **https://www.pauta.cc**:
landing page, proposed plans, and draft terms, privacy and refund pages (needed for Paddle,
decision 6 in eduelias/pauta). Plain HTML and CSS, no framework, no trackers, no cookies.
The app itself is at https://app.pauta.cc and is not in this repo.

| Path | What |
|---|---|
| `site/` | Everything that is published. `CNAME` is `www.pauta.cc` |
| `tools/check.py` | Browser check: old app links forward, no console errors, local links answer |
| `tools/seo.py` | Keeps the FAQ JSON-LD, the plan offers, `sitemap.xml` and the shared header/footer in sync with the pages (`make seo`, `make seo-write`) |
| `tools/render_images.py` | `site/og.png` and the campaign images (macOS, SF font) |
| `campaign/` | Launch copy and images. Not published |

```bash
make serve    # http://localhost:8091
make seo      # FAQ JSON-LD, offers, sitemap and header/footer in sync (python3 + git only)
make seo-write # regenerate the FAQ JSON-LD and sitemap.xml after editing a page
make check    # seo, then the browser check; needs uv; Playwright's Chromium is installed once with
              # uv run --no-project --with playwright==1.64.1 playwright install chromium
make shots    # check + desktop/mobile screenshots in shots/
make images   # og.png and campaign/*.png
make live     # the live hosts: redirects, the site, old app links
```

## Hosting

GitHub Pages, published by `.github/workflows/pages.yml` from `site/` on every push to `main`.
DNS is in `du7/dns-zone` (`pauta.tf`): `www.pauta.cc` is a DNS-only CNAME to
`eduelias.github.io`. The apex `pauta.cc`, `pauta.team` and `www.pauta.team` stay on du7's
Caddy as a 301 to `https://www.pauta.cc{uri}`.

## SEO

- `site/index.html` carries JSON-LD for `Organization`, `SoftwareApplication` (the three plans
  as `Offer`s in BRL) and `FAQPage`. The FAQ block, between the `<!-- seo:faq -->` markers, is
  **generated** from the FAQ section's `<details>`: edit the HTML, then `make seo-write`.
  `make seo` (also the first step of `make check`, and the `check` workflow on pull requests)
  fails when the JSON-LD, the offers, the sitemap or a page's header/footer drift.
- `site/sitemap.xml` lists every page but `404.html`; `lastmod` is the date of the last commit
  that touched the page (today while it has uncommitted changes). `make seo-write` regenerates
  it, and the Pages workflow regenerates it again on deploy, so it is never hand-edited.
- Every page: one `<h1>`, a 10-65 character `<title>`, a 50-160 character description, its own
  canonical, and the same header and footer as `index.html` (byte for byte: copy them from
  there). Content pages live in a folder with an `index.html` (clean URLs: `/recursos/pedidos/`),
  use `<main class="page">`, a `.crumbs` breadcrumb plus `BreadcrumbList` JSON-LD, and end with
  a `.page-cta` box. `site/recursos/pedidos/index.html` is the template.
- Check a page with Google's Rich Results Test (https://search.google.com/test/rich-results)
  or https://validator.schema.org/ by pasting the HTML, and `npx lighthouse <url>
  --only-categories=seo` on `make serve`.

### Search Console e Bing

Nothing is registered yet. The owner does this; the repo only has the placeholders.

1. Google: https://search.google.com/search-console → add a **URL-prefix** property for
   `https://www.pauta.cc/` → HTML tag. Paste the tag over the commented
   `google-site-verification` line in `site/index.html`'s `<head>`, push, verify, then submit
   `https://www.pauta.cc/sitemap.xml` under Sitemaps.
2. Bing: https://www.bing.com/webmasters → "Import from Google Search Console" (no tag needed),
   or add the site and paste its `msvalidate.01` tag over the commented line next to Google's.
3. DNS alternative, for a **Domain** property that also covers `app.` and `acc.` without any
   tag on the pages: in `du7/dns-zone` (`pauta.tf`) add a `cloudflare_dns_record` of type
   `TXT` on `pauta.cc` with the `google-site-verification=...` value Search Console shows
   (same shape as the `pauta_spf` record), `terraform apply`, then verify. Bing's DNS option is a
   CNAME `<code>.pauta.cc → verify.bing.com`. Keep the TXT: Google re-checks it.

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
- Contact: info@pauta.cc and edu@pauta.cc forward to the owner (Cloudflare Email Routing, dns-zone pauta.tf). The beta contact is famulus's WhatsApp number (+1 555 474 7185, lead intake on): an automatic
  reply, and the message is forwarded to the owner.
