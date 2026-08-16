import type { VercelRequest, VercelResponse } from "@vercel/node";
import { generateChatResponse } from "../src/chatApiCore.js";

type RateBucket = { count: number; resetAt: number };
const RATE_LIMIT_WINDOW_MS = 60_000;
const RATE_LIMIT_MAX = Number(process.env.RATE_LIMIT_MAX || 6);
const DAILY_LIMIT_WINDOW_MS = 86_400_000;
const DAILY_LIMIT_MAX = Number(process.env.DAILY_LIMIT_MAX || 60);
const buckets = new Map<string, RateBucket>();
const dailyBuckets = new Map<string, RateBucket>();

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

function clientId(req: VercelRequest) {
  const forwarded = String(req.headers["x-forwarded-for"] || "").split(",")[0].trim();
  const real = String(req.headers["x-real-ip"] || "").trim();
  return forwarded || real || req.socket.remoteAddress || "unknown";
}

function consumeBucket(store: Map<string, RateBucket>, id: string, limit: number, windowMs: number) {
  const now = Date.now();
  const existing = store.get(id);
  if (!existing || existing.resetAt <= now) {
    store.set(id, { count: 1, resetAt: now + windowMs });
    return { allowed: true, remaining: Math.max(0, limit - 1), retryAfter: 0 };
  }
  existing.count += 1;
  const allowed = existing.count <= limit;
  return {
    allowed,
    remaining: Math.max(0, limit - existing.count),
    retryAfter: Math.max(1, Math.ceil((existing.resetAt - now) / 1000))
  };
}

function checkRateLimit(req: VercelRequest) {
  const id = clientId(req);
  const minute = consumeBucket(buckets, id, RATE_LIMIT_MAX, RATE_LIMIT_WINDOW_MS);
  if (!minute.allowed) return { ...minute, limit: RATE_LIMIT_MAX };
  const daily = consumeBucket(dailyBuckets, id, DAILY_LIMIT_MAX, DAILY_LIMIT_WINDOW_MS);
  if (!daily.allowed) return { ...daily, limit: DAILY_LIMIT_MAX };
  return { allowed: true, remaining: Math.min(minute.remaining, daily.remaining), retryAfter: 0, limit: RATE_LIMIT_MAX };
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

  const rate = checkRateLimit(req);
  res.setHeader("X-RateLimit-Limit", String(rate.limit));
  res.setHeader("X-RateLimit-Remaining", String(rate.remaining));
  if (!rate.allowed) {
    res.setHeader("Retry-After", String(rate.retryAfter));
    res.status(429).json({
      error: "Too many requests.",
      response: "I’m getting a lot of questions right now. Please try again shortly, or share a few details for a free 30-minute introductory call."
    });
    return;
  }

  const result = await generateChatResponse(Array.isArray(req.body?.messages) ? req.body.messages : []);
  res.status(result.status).json(result.body);
}
