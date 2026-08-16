import type { VercelRequest, VercelResponse } from "@vercel/node";
import { YONATAN_PROFILE } from "../src/yonatanProfile.js";

type LeadPayload = {
  name?: unknown;
  email?: unknown;
  phone?: unknown;
  need?: unknown;
  timeline?: unknown;
  source?: unknown;
  website?: unknown;
};

function allowedOrigins() {
  return (process.env.ALLOWED_ORIGINS || "")
    .split(",")
    .map((origin) => origin.trim().replace(/\/$/, ""))
    .filter(Boolean);
}

function isAllowedOrigin(origin?: string) {
  const allowed = allowedOrigins();
  if (!origin) return process.env.NODE_ENV !== "production";
  if (allowed.length === 0) return process.env.NODE_ENV !== "production";
  return allowed.includes(origin.replace(/\/$/, ""));
}

function clean(value: unknown, max = 800) {
  return String(value || "").replace(/\s+/g, " ").trim().slice(0, max);
}

function validEmail(value: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(value);
}

function mailtoUrl(lead: Required<Pick<LeadPayload, "name" | "email" | "need">> & { phone: string; timeline: string }) {
  const subject = `Intro call request from ${lead.name}`;
  const body = [
    "Hi Yonatan,",
    "",
    "A visitor is requesting a free 30-minute introductory call.",
    "",
    `Name: ${lead.name}`,
    `Email: ${lead.email}`,
    `Phone: ${lead.phone || "Not specified"}`,
    `What to cover: ${lead.need}`,
    `Times that work: ${lead.timeline || "Not specified"}`,
    "",
    "Please follow up to confirm a time."
  ].join("\n");

  return `mailto:${encodeURIComponent(YONATAN_PROFILE.contactEmail)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

type Lead = { name: string; email: string; phone: string; need: string; timeline: string; source: string };

type DeliveryResult = { delivered: boolean; destination?: "google-sheets" | "webhook" };

function leadPayload(lead: Lead) {
  return {
    type: "portfolio_chat_lead",
    receivedAt: new Date().toISOString(),
    lead
  };
}

async function getGoogleAccessToken() {
  const clientId = process.env.GOOGLE_OAUTH_CLIENT_ID;
  const clientSecret = process.env.GOOGLE_OAUTH_CLIENT_SECRET;
  const refreshToken = process.env.GOOGLE_OAUTH_REFRESH_TOKEN;

  if (!clientId || !clientSecret || !refreshToken) {
    throw new Error("Missing Google OAuth environment variables.");
  }

  const response = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      client_id: clientId,
      client_secret: clientSecret,
      refresh_token: refreshToken,
      grant_type: "refresh_token"
    })
  });

  if (!response.ok) {
    throw new Error(`Google OAuth refresh failed with ${response.status}`);
  }

  const data = (await response.json()) as { access_token?: string };
  if (!data.access_token) {
    throw new Error("Google OAuth refresh did not return an access token.");
  }

  return data.access_token;
}

async function appendToGoogleSheet(lead: Lead): Promise<DeliveryResult> {
  const spreadsheetId = process.env.GOOGLE_SHEETS_ID;
  if (!spreadsheetId) return { delivered: false };

  const accessToken = await getGoogleAccessToken();
  const payload = leadPayload(lead);
  const row = [
    payload.receivedAt,
    lead.name,
    lead.email,
    lead.phone,
    lead.need,
    lead.timeline,
    lead.source,
    payload.type
  ];

  const sheetName = process.env.GOOGLE_SHEETS_TAB || "Leads";
  const url = `https://sheets.googleapis.com/v4/spreadsheets/${encodeURIComponent(spreadsheetId)}/values/${encodeURIComponent(sheetName)}!A:H:append?valueInputOption=RAW&insertDataOption=INSERT_ROWS`;
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${accessToken}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ values: [row] })
  });

  if (!response.ok) {
    throw new Error(`Google Sheets append failed with ${response.status}`);
  }

  return { delivered: true, destination: "google-sheets" };
}

async function forwardToWebhook(lead: Lead): Promise<DeliveryResult> {
  const webhookUrl = process.env.LEAD_WEBHOOK_URL;
  if (!webhookUrl) return { delivered: false };

  const response = await fetch(webhookUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(process.env.LEAD_WEBHOOK_SECRET ? { "Authorization": `Bearer ${process.env.LEAD_WEBHOOK_SECRET}` } : {})
    },
    body: JSON.stringify(leadPayload(lead))
  });

  if (!response.ok) {
    throw new Error(`Lead webhook failed with ${response.status}`);
  }

  return { delivered: true, destination: "webhook" };
}

async function deliverLead(lead: Lead): Promise<DeliveryResult> {
  const googleSheetsDelivery = await appendToGoogleSheet(lead);
  if (googleSheetsDelivery.delivered) return googleSheetsDelivery;
  return forwardToWebhook(lead);
}

// === NEW: Telegram notification when a lead is successfully saved to the sheet ===
async function sendTelegramNotification(lead: Lead) {
  const token = process.env.TELEGRAM_BOT_TOKEN;
  const chatId = process.env.TELEGRAM_CHAT_ID;
  const sheetsId = process.env.GOOGLE_SHEETS_ID;

  if (!token || !chatId) {
    return { delivered: false };
  }

  const text = [
    "🆕 <b>New intro-call request from your portfolio</b>",
    "",
    `<b>Name:</b> ${lead.name}`,
    `<b>Email:</b> ${lead.email}`,
    lead.phone ? `<b>Phone:</b> ${lead.phone}` : null,
    `<b>What to cover:</b> ${lead.need}`,
    lead.timeline ? `<b>Times that work:</b> ${lead.timeline}` : null,
    `<b>Source:</b> ${lead.source}`,
    "",
    sheetsId ? `📄 <a href="https://docs.google.com/spreadsheets/d/${sheetsId}">Open Google Sheet</a>` : null
  ].filter(Boolean).join("\n");

  try {
    const res = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: chatId,
        text,
        parse_mode: "HTML",
        disable_web_page_preview: true
      })
    });

    if (!res.ok) {
      const err = await res.text().catch(() => "");
      console.error("Telegram notification failed:", res.status, err);
    }

    return { delivered: res.ok };
  } catch (error) {
    console.error("Telegram notification error:", error);
    return { delivered: false };
  }
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  const origin = String(req.headers.origin || "");
  if (!isAllowedOrigin(origin)) {
    res.status(403).json({ error: "Origin not allowed." });
    return;
  }

  if (origin) res.setHeader("Access-Control-Allow-Origin", origin);
  res.setHeader("Vary", "Origin");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") {
    res.status(204).end();
    return;
  }
  if (req.method !== "POST") {
    res.status(405).json({ error: "Method not allowed." });
    return;
  }

  const payload = (req.body || {}) as LeadPayload;
  if (clean(payload.website)) {
    res.status(200).json({ ok: true, delivered: false });
    return;
  }

  const lead = {
    name: clean(payload.name, 120),
    email: clean(payload.email, 160),
    phone: clean(payload.phone, 80),
    need: clean(payload.need, 900),
    timeline: clean(payload.timeline, 240),
    source: clean(payload.source, 120) || "portfolio-chat"
  };

  if (lead.name.length < 2) {
    res.status(400).json({ error: "Please include a name." });
    return;
  }
  if (!validEmail(lead.email)) {
    res.status(400).json({ error: "Please include a valid email." });
    return;
  }
  if (lead.need.length < 8) {
    res.status(400).json({ error: "Please include a short project description." });
    return;
  }

  try {
    const delivery = await deliverLead(lead);

    // Send Telegram notification when we successfully wrote to the sheet
    if (delivery.delivered && delivery.destination === "google-sheets") {
      // Fire and forget the notification so it doesn't slow down the response
      sendTelegramNotification(lead).catch(() => {});
    }

    res.status(200).json({
      ok: true,
      delivered: delivery.delivered,
      destination: delivery.destination,
      fallback: delivery.delivered ? undefined : "mailto",
      mailtoUrl: delivery.delivered ? undefined : mailtoUrl(lead),
      message: delivery.delivered
        ? "Thanks — I sent this to Yonatan so he can prepare a free 30-minute introductory call."
        : "Thanks — I prepared an email to Yonatan with these details for a free 30-minute introductory call. Send it when you’re ready."
    });
  } catch (error) {
    res.status(502).json({
      error: "Lead delivery failed.",
      fallback: "mailto",
      mailtoUrl: mailtoUrl(lead),
      message: "I could not send it automatically, but I prepared an email to Yonatan with these details for a free 30-minute introductory call."
    });
  }
}
