# Sofer On Site International — homepage redesign

A static, mobile-first homepage proposal for [Sofer On Site International](https://www.soferonsite.com), a Torah scribe (sofer) studio in North Miami Beach, Florida. Built as a client-meeting design: parchment and navy, gold accents, real HTML text (nothing baked into images), and clearly labeled slots for photographs that do not exist in this repo.

This is a fresh build. It does not copy the current Xara Web Designer export.

## Open it

No build step, no framework.

- **Double-click** `index.html`, or
- Serve the folder with any static host:

```bash
python3 -m http.server 43123
```

Then visit `http://127.0.0.1:43123`.

## Deploy

Upload the whole folder (`index.html`, `css/`, `js/`, `assets/`, `favicon.svg`) to any static host:

- The studio’s current web host (replace the existing homepage files)
- Netlify, Cloudflare Pages, GitHub Pages, or an S3/CloudFront bucket

Relative paths are used throughout, so the site works from the domain root or a subfolder as long as the folder structure is kept intact.

The contact form is **front-end only**. It does not post. Wire it to Formspree, Netlify Forms, or the studio’s existing mail script before launch.

## Swap placeholders for real assets

| Slot | Where | What to drop in |
| --- | --- | --- |
| Script logo (blue globe + Torah scroll) | `assets/mark.svg` and the header `.brand-mark` | Official logo; keep the type wordmark as a fallback |
| Hero photograph | `.photo-slot` in the hero | A real visit, workshop, or Torah-in-use photo — not stock |
| Open Graph image | `<head>` (commented TODO) | 1200×630 JPG/PNG of the logo lockup or hero |
| Team headshots | `.avatar` initials on each `.person` card | Cropped portraits; keep the gold ring treatment |
| Full staff roster | `#team` (HTML comment) | Live site lists eight people in each group; only eleven names were visible in the page text. Confirm names, titles, and grouping. |
| Testimonials | `#testimonials` cards | Real excerpts from the existing archive. Do not invent quotes. Point “Read testimonials” at the current testimonials page. |
| News & Links tiles | `#news` | Real article, YouTube, TV, and partner URLs |
| Service inner pages | each `.service-card` (HTML comments) | e.g. `services/torah-purchases.html` — cards currently link to `#` so nothing 404s |
| Social URLs | footer `.social` | LinkedIn, X, Facebook, Instagram, YouTube |
| Contact form handler | `#contact-form` | Real endpoint; do not leave the demo submit message in production |

## What’s real vs. what needs confirmation

**From the studio (used as-is, lightly tightened for the web):**

- Name, North Miami Beach address, phone, fax, email, and hours
- Mission / about copy, 40 years, five continents, on-site worldwide, South Florida workshop
- Service names, Torah Journey “Write, Connect, Uplift” copy, testimonials intro line, news intro line, footer STa’M line
- The eleven staff names and titles that appear in the live site’s text
- Hebrew tagline לְמַעַן תְּסַפֵּר (Lema’an T’saper)

**Not invented, but still placeholders:**

- No photographs of people
- No fabricated testimonials, numbers, or press headlines
- No copied artwork from the current site

**Previews** of this proposal at phone, tablet, and desktop widths live in `/previews`.
