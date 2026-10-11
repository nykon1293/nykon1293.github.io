# Google Search Console and indexing

Site: **https://gemmisi.com/**  
Sitemap: **https://gemmisi.com/sitemap.xml**

Verification source of truth: HTML file **`google8e4f316483f6a346.html`** at the site root (merged in PR #2). Do not add a meta tag that conflicts with that file.

Indexing is the bottleneck. This repo cannot log into Google.

## Josh checklist (after the SEO PR is live)

1. Open [Google Search Console](https://search.google.com/search-console).
2. **Verify** the URL-prefix property `https://gemmisi.com/` with the HTML file `google8e4f316483f6a346.html` if it is not already verified.
3. **Sitemaps** → submit `https://gemmisi.com/sitemap.xml`.
4. **URL inspection** → request indexing for every public offer page:
   - `https://gemmisi.com/`
   - `https://gemmisi.com/pricing.html`
   - `https://gemmisi.com/services/hermes-agents.html`
   - `https://gemmisi.com/services/ai-automation.html`
   - `https://gemmisi.com/services/dashboards-reporting.html`
   - `https://gemmisi.com/services/ecommerce-operations.html`
   - `https://gemmisi.com/services/stocky-recovery.html`
   - `https://gemmisi.com/services/tutoring-project-help.html`
   - `https://gemmisi.com/advisory.html`
   - `https://gemmisi.com/work/governed-ai-content-engine.html`
5. Optional: [Bing Webmaster Tools](https://www.bing.com/webmasters/) → import from GSC, same sitemap.

`site:gemmisi.com` can stay empty for days after submit. Use Search Console → Pages, not only `site:` search.

## Optional follow-up (not in this PR)

A custom domain (not `github.io`) often indexes more cleanly than a user Pages hostname.

## Local preview

```bash
python3 -m http.server 8000
# Open http://localhost:8000/ and view source for title, description, and JSON-LD.
```
