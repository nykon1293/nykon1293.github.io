# Google Search Console setup (Phase 1)

Site: **https://nykon1293.github.io/**  
Sitemap: **https://nykon1293.github.io/sitemap.xml**

Hermes cannot sign in to your Google account. Complete these steps once in your browser (about 10 minutes).

## 1. Add the property

1. Open [Google Search Console](https://search.google.com/search-console).
2. Click **Add property** → choose **URL prefix**.
3. Enter: `https://nykon1293.github.io/`

## 2. Verify ownership (HTML tag — works with GitHub Pages)

1. In Search Console, pick **HTML tag** verification.
2. Copy the meta tag Google gives you. It looks like:
   ```html
   <meta name="google-site-verification" content="XXXXXXXX" />
   ```
3. Paste that line in `index.html` inside `<head>`, after `<meta charset="utf-8" />`.
4. Commit and push to `main`, wait for GitHub Pages to deploy (check the Actions tab).
5. In Search Console, click **Verify**.

You can remove the verification meta tag after verification succeeds (optional; leaving it is fine).

## 3. Submit the sitemap

1. In Search Console → **Sitemaps**.
2. Enter: `sitemap.xml`
3. Submit.

## 4. Optional: Bing Webmaster Tools

1. [Bing Webmaster](https://www.bing.com/webmasters/) → add site.
2. You can **import from Google Search Console** after Google is verified.

## 5. What to check after a week

- **Performance** → queries containing your name or “AI automation Miami”.
- **Pages** → confirm `/` is indexed.
- **Enhancements** → FAQ rich results may appear after Google recrawls (not guaranteed).

## Local preview before push

```bash
cd /Users/yonatangemmi/personal-github-pages-site
python3 -m http.server 8000
# Open http://localhost:8000/ and view source to confirm title, description, and JSON-LD.
```