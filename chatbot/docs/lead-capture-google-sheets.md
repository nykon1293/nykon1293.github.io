# Portfolio Chatbot Lead Capture → Google Sheets

The chatbot lead form posts to `/api/lead` in the Vercel chatbot project.

Production is now configured to write leads directly into Google Sheets using Google OAuth credentials stored in Vercel environment variables.

## Production Sheet

- Sheet name: `Portfolio Chatbot Leads`
- Sheet URL: https://docs.google.com/spreadsheets/d/1N9Y6AkZ3rSU0xqjvCdhSKXT-_2gdZl93cWBLorGgzZE/edit
- Tab: `Leads`

## Stored columns

1. `Received At`
2. `Name`
3. `Email`
4. `Phone`
5. `Project / Need`
6. `Timeline / Budget`
7. `Source`
8. `Payload Type`

## Required Vercel env vars

Production needs these env vars:

- `GOOGLE_SHEETS_ID`
- `GOOGLE_SHEETS_TAB`
- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`
- `GOOGLE_OAUTH_REFRESH_TOKEN`

Existing fallback env vars still work:

- `LEAD_WEBHOOK_URL`
- `LEAD_WEBHOOK_SECRET`

Delivery order in `/api/lead`:

1. If `GOOGLE_SHEETS_ID` exists, append directly to Google Sheets.
2. Otherwise, if `LEAD_WEBHOOK_URL` exists, POST the normalized lead payload there.
3. Otherwise, return a `mailto:` fallback for the visitor to manually email Yonatan.

## Verification performed

After deployment, a production POST to `/api/lead` returned:

```json
{
  "ok": true,
  "delivered": true,
  "destination": "google-sheets",
  "message": "Thanks — I sent this to Yonatan."
}
```

The test row was confirmed in Google Sheets, then removed so the sheet is clean for real leads.

## Notes

The Google OAuth refresh token belongs to `josh.gemmi@gmail.com`. Do not print it in logs or commit it to the repository. Keep it only in Vercel environment variables or a local credential store.
