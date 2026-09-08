# Google Search Console and indexing

Site: **https://nykon1293.github.io/**  
Sitemap: **https://nykon1293.github.io/sitemap.xml**

Indexing is the bottleneck. On-page titles, canonicals, robots, and a sitemap already exist. Google `site:` looking empty means the property still needs verification and a sitemap submit — this repo cannot log into your Google account.

## Josh checklist (do this after the SEO PR is live)

1. Open [Google Search Console](https://search.google.com/search-console).
2. **Verify** the URL-prefix property `https://nykon1293.github.io/` if it is not already verified. This repo already includes the HTML file `google934367059a98780b.html`.
3. **Sitemaps** → submit `https://nykon1293.github.io/sitemap.xml` (or just `sitemap.xml`).
4. **URL inspection** → request indexing for:
   - `https://nykon1293.github.io/`
   - `https://nykon1293.github.io/services/stocky-recovery.html`
   - `https://nykon1293.github.io/pricing.html`
   - `https://nykon1293.github.io/services/hermes-agents.html`
5. Optional: [Bing Webmaster Tools](https://www.bing.com/webmasters/) → add the site, or import from Search Console after Google is verified. Submit the same sitemap.

`site:nykon1293.github.io` can stay empty for days after submit. Recheck in Search Console → Pages, not only `site:` search.

## Optional follow-up (not in this PR)

A custom domain (not `github.io`) often indexes more cleanly than a user Pages hostname. Do not change the domain in this pass.

## Local preview

```bash
python3 -m http.server 8000
# Open http://localhost:8000/ and view source for title, description, and JSON-LD.
```
