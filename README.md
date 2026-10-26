# nykon1293.github.io

Personal website hosted with GitHub Pages. Public pages load Cloudflare Web Analytics just before `</body>` (hand-written HTML, and `CLOUDFLARE_WEB_ANALYTICS` in `scripts/seo_schema.py` for generated pages).

## Use cases library

The pages under `use-cases/` are generated. The source of truth is `data/use-cases.json` plus `data/taxonomy.json` (industry and function labels, blurbs, SEO titles, regulated copy, the own-accounts line, and the legacy `#g-*` anchor map).

To add one entry:

1. Edit `data/use-cases.json` and add an object. Copy an existing entry and keep these fields: `slug`, `title`, `industries` (list, first is primary, at most six), `functions` (list, first is primary; these are plain-language problems), `summary`, `problem`, `what_si_does`, `setup`, `human_checks`, `examples` (each with `business_type` and `scenario`), `copy_prompt`, `tools_examples`, `effect`, and `caution` (a string, or `null` if there is nothing extra to flag). Put an industry's top three in `start_here` in `data/taxonomy.json`. Optional `video` is an embed URL; leave it empty to hide the player.
2. Use industry and function slugs that already appear in `data/taxonomy.json`. Unknown slugs fail the build. Entry slugs `industry` and `function` are reserved. Dedicated vertical entries keep that vertical primary and are not also tagged `any-business`. `slug` is lowercase words separated by hyphens, and it becomes the URL `/use-cases/<slug>/`.
3. From the repo root, run `python3 scripts/build_use_cases.py`.
4. Commit `data/use-cases.json`, `data/taxonomy.json` if you changed it, the generated HTML, `use-cases/search.json`, and the sitemap update.

The hub at `/use-cases/` is a light page: search, problem chips, one row of industry links with counts, a start-here card for each industry, and a show-more control that loads the rest from `use-cases/search.json`. Static landings live at `/use-cases/industry/<slug>/` and `/use-cases/function/<slug>/`. Old slugs redirect with a canonical to the merged page. GitHub Pages serves those files as they are. SI (Super Intelligence) is the official term; put “AI” next to it in titles, meta, and the first body mention so searches still match. Do not rewrite the rest of the copy. Examples are illustrations, not client results. After data edits, also run `python3 scripts/build-service-pages.py` and `python3 scripts/patch_unique_pages.py` so service pages and shared JSON-LD stay in sync.

After the GitHub Pages workflow (`pages-build-deployment`) succeeds on `main`, `.github/workflows/indexnow.yml` runs `python3 scripts/indexnow_ping.py` to POST changed public URLs (or the sitemap) to IndexNow. Use **Run workflow** (`workflow_dispatch`) to resubmit every sitemap URL. The active key file is `f702ca108ee22cc8602abd433bed3cf5.txt` at the repo root (`scripts/indexnow_ping.py` `ACTIVE_KEY`). Older 32-hex key files may stay at the root so prior verifications do not 404; do not move the active file off the site root.

## Social tracking short links

Cloudflare Web Analytics ignores query strings, so campaign clicks are counted by path (`/fb1101`, `/li1025`, `/wa`, …) instead of `?utm=`. Each slug is a tiny noindex page at `<slug>/index.html`. GitHub Pages serves `/<slug>/` and 301s `/<slug>` there, so both URLs work. The page loads the same Cloudflare JS beacon used on public pages (`CLOUDFLARE_WEB_ANALYTICS` in `scripts/seo_schema.py`; token `c9c911628ffd4644bce7bea8d47eb16c`), waits about 300ms, then `location.replace`s to that post’s destination. A 1-second meta refresh is the no-JS fallback. These URLs stay out of `sitemap.xml` and IndexNow.

Analytics is the HTML snippet, not Cloudflare HTML auto-injection (the live site is served by GitHub Pages). Do not omit the beacon or these visits will not be counted.

To add a slug:

1. Edit `data/tracking-links.json`. For a dated Facebook/LinkedIn pair, add `"MMDD": "/destination/"` under `posts` (that creates both `/fbMMDD` and `/liMMDD`). A second post on the same day uses a letter suffix, e.g. `"1026b"` → `/fb1026b` and `/li1026b`. For a generic channel link, add `"wa": "/"` (or `fb` / `li`) under `generic`. Destinations are site paths that already exist as real pages, not moved stubs.
2. From the repo root, run `python3 scripts/build_tracking_links.py`.
3. Commit the JSON and the new `<slug>/index.html`. Removing a slug and re-running the generator deletes that folder. `python3 scripts/build_tracking_links.py --check` confirms committed pages match the list. Do not add these paths to `sitemap.xml`.
