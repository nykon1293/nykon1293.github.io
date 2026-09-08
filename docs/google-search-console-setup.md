# Google Search Console and indexing

Site: **https://nykon1293.github.io/**  
Sitemap: **https://nykon1293.github.io/sitemap.xml**

Verification source of truth: HTML file **`google8e4f316483f6a346.html`** at the site root (merged in PR #2). Do not add a meta tag that conflicts with that file.

Indexing is the bottleneck. This repo cannot log into Google.

## Josh checklist (after the SEO PR is live)

1. Open [Google Search Console](https://search.google.com/search-console).
2. **Verify** the URL-prefix property `https://nykon1293.github.io/` with the HTML file `google8e4f316483f6a346.html` if it is not already verified.
3. **Sitemaps** → submit `https://nykon1293.github.io/sitemap.xml`.
4. **URL inspection** → request indexing for every public offer page:
   - `https://nykon1293.github.io/`
   - `https://nykon1293.github.io/pricing.html`
   - `https://nykon1293.github.io/services/hermes-agents.html`
   - `https://nykon1293.github.io/services/ai-automation.html`
   - `https://nykon1293.github.io/services/dashboards-reporting.html`
   - `https://nykon1293.github.io/services/ecommerce-operations.html`
   - `https://nykon1293.github.io/services/stocky-recovery.html`
   - `https://nykon1293.github.io/services/tutoring-project-help.html`
   - `https://nykon1293.github.io/advisory.html`
   - `https://nykon1293.github.io/work/governed-ai-content-engine.html`
5. Optional: [Bing Webmaster Tools](https://www.bing.com/webmasters/) → import from GSC, same sitemap.

`site:nykon1293.github.io` can stay empty for days after submit. Use Search Console → Pages, not only `site:` search.

## Optional follow-up (not in this PR)

A custom domain (not `github.io`) often indexes more cleanly than a user Pages hostname.

## Local preview

```bash
python3 -m http.server 8000
# Open http://localhost:8000/ and view source for title, description, and JSON-LD.
```
