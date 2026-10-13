# nykon1293.github.io

Personal website hosted with GitHub Pages. Public pages load Cloudflare Web Analytics just before `</body>` (hand-written HTML, and `CLOUDFLARE_WEB_ANALYTICS` in `scripts/seo_schema.py` for generated pages).

## Use cases library

The pages under `use-cases/` are generated. The source of truth is `data/use-cases.json` plus `data/taxonomy.json` (industry and function labels, blurbs, SEO titles, regulated copy, the own-accounts line, and the legacy `#g-*` anchor map).

To add one entry:

1. Edit `data/use-cases.json` and add an object. Copy an existing entry and keep these fields: `slug`, `title`, `industries` (list, first is primary, at most four), `functions` (list, first is primary), `summary`, `problem`, `what_si_does`, `setup`, `human_checks`, `examples` (each with `business_type` and `scenario`), `copy_prompt`, `tools_examples`, `effect`, and `caution` (a string, or `null` if there is nothing extra to flag). Set `"featured": true` only for the twelve hub cards listed in `data/taxonomy.json`.
2. Use industry and function slugs that already appear in `data/taxonomy.json`. Unknown slugs fail the build. Entry slugs `industry` and `function` are reserved. Dedicated vertical entries keep that vertical primary and are not also tagged `any-business`. `slug` is lowercase words separated by hyphens, and it becomes the URL `/use-cases/<slug>/`.
3. From the repo root, run `python3 scripts/build_use_cases.py`.
4. Commit `data/use-cases.json`, `data/taxonomy.json` if you changed it, the generated HTML, `use-cases/search.json`, and the sitemap update.

The hub at `/use-cases/` is a light page: search, function chips, industry tiles, twelve featured cards, and a show-more control that loads the rest from `use-cases/search.json`. Static landings live at `/use-cases/industry/<slug>/` and `/use-cases/function/<slug>/`. GitHub Pages serves those files as they are. SI (Super Intelligence) is the official term; put “AI” next to it in titles, meta, and the first body mention so searches still match. Do not rewrite the rest of the copy. Examples are illustrations, not client results. After data edits, also run `python3 scripts/build-service-pages.py` and `python3 scripts/patch_unique_pages.py` so service pages and shared JSON-LD stay in sync.

After the GitHub Pages workflow (`pages-build-deployment`) succeeds on `main`, `.github/workflows/indexnow.yml` runs `python3 scripts/indexnow_ping.py` to POST changed public URLs (or the sitemap) to IndexNow. Use **Run workflow** (`workflow_dispatch`) to resubmit every sitemap URL. The active key file is `f702ca108ee22cc8602abd433bed3cf5.txt` at the repo root (`scripts/indexnow_ping.py` `ACTIVE_KEY`). Older 32-hex key files may stay at the root so prior verifications do not 404; do not move the active file off the site root.
