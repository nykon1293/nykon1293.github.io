# Yonatan Portfolio Chatbot

Production-safe AI assistant backend and embeddable frontend for Yonatan Gemmi's GitHub Pages portfolio.

## What this is

- React/Vite chat UI for visitors.
- Express `/api/chat` backend using Google Gemini through `@google/genai`.
- Resume-backed server-side profile in `src/yonatanProfile.ts`.
- No profile editor or public system-prompt configuration UI.
- No API key in browser code.

## Required environment variables

```bash
GEMINI_API_KEY=your_fresh_key_here
GEMINI_MODEL=gemini-3.7-flash
PORT=3000
ALLOWED_ORIGINS=https://nykon1293.github.io
RATE_LIMIT_MAX=12
```

Do **not** commit `.env` with a real key. Store `GEMINI_API_KEY` in the deployment provider's secret/environment variable UI.

## Local development

```bash
npm install
cp .env.example .env
# Add a fresh GEMINI_API_KEY to .env locally if you want live Gemini testing.
npm run dev
```

Health check:

```bash
curl http://localhost:3000/api/health
```

## Production build

```bash
npm run lint
npm run build
npm start
```

## Cloud Run outline

From this directory:

```bash
gcloud run deploy yonatan-portfolio-chatbot \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_MODEL=gemini-3.7-flash,ALLOWED_ORIGINS=https://nykon1293.github.io,RATE_LIMIT_MAX=12 \
  --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest
```

Then update the GitHub Pages script tag in `/Users/yonatangemmi/personal-github-pages-site/index.html`:

```html
<script src="assets/portfolio-chatbot.js" data-chatbot-url="https://YOUR-CLOUD-RUN-URL" defer></script>
```

## Safety/cost controls included

- API key read only from backend environment.
- CORS origin allow-list through `ALLOWED_ORIGINS`.
- JSON body size limit: 16 KB.
- Max conversation history sent to model: 8 messages.
- Max user message characters: 1200.
- Gemini output capped with `maxOutputTokens: 500`.
- Simple per-IP rate limit: default 12 requests/minute.
- Public responses grounded in resume/profile facts; bot is instructed not to invent claims.
- Visitor fallback routes to `josh.gemmi@gmail.com` if the AI service is unavailable.
