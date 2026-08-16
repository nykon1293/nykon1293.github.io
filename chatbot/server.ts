import "dotenv/config";
import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import { YONATAN_PROFILE } from "./src/yonatanProfile";
import { chatbotModel, generateChatResponse } from "./src/chatApiCore";

const PORT = Number(process.env.PORT || 3000);
const RATE_LIMIT_WINDOW_MS = 60_000;
const RATE_LIMIT_MAX = Number(process.env.RATE_LIMIT_MAX || 6);
const DAILY_LIMIT_WINDOW_MS = 24 * 60 * 60 * 1000;
const DAILY_LIMIT_MAX = Number(process.env.DAILY_LIMIT_MAX || 60);
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || "")
  .split(",")
  .map((origin) => origin.trim())
  .filter(Boolean);

type RateBucket = { count: number; resetAt: number };
const buckets = new Map<string, RateBucket>();
const dailyBuckets = new Map<string, RateBucket>();

function isAllowedOrigin(origin?: string) {
  if (ALLOWED_ORIGINS.length === 0) return process.env.NODE_ENV !== "production";
  return Boolean(origin && ALLOWED_ORIGINS.includes(origin));
}

function isLocalAddress(address: string) {
  return address === "::1" || address === "127.0.0.1" || address === "::ffff:127.0.0.1";
}

function pruneExpiredBuckets(now = Date.now()) {
  Array.from(buckets.entries()).forEach(([id, bucket]) => {
    if (bucket.resetAt <= now) buckets.delete(id);
  });
  Array.from(dailyBuckets.entries()).forEach(([id, bucket]) => {
    if (bucket.resetAt <= now) dailyBuckets.delete(id);
  });
}

function clientId(req: express.Request) {
  const remote = (req.socket.remoteAddress || "unknown").trim();
  if (process.env.TRUST_PROXY === "1" || isLocalAddress(remote)) {
    const forwarded = req.headers["x-forwarded-for"];
    const firstForwarded = Array.isArray(forwarded) ? forwarded[0] : forwarded?.split(",")[0];
    return (firstForwarded || remote).trim();
  }
  return remote;
}

function hitBucket(store: Map<string, RateBucket>, id: string, windowMs: number, max: number) {
  const now = Date.now();
  const bucket = store.get(id);
  if (!bucket || bucket.resetAt <= now) {
    store.set(id, { count: 1, resetAt: now + windowMs });
    return { allowed: true, remaining: Math.max(0, max - 1), resetAt: now + windowMs };
  }
  bucket.count += 1;
  return { allowed: bucket.count <= max, remaining: Math.max(0, max - bucket.count), resetAt: bucket.resetAt };
}

function checkRateLimit(req: express.Request) {
  pruneExpiredBuckets();
  const id = clientId(req);
  const minute = hitBucket(buckets, id, RATE_LIMIT_WINDOW_MS, RATE_LIMIT_MAX);
  const daily = hitBucket(dailyBuckets, id, DAILY_LIMIT_WINDOW_MS, DAILY_LIMIT_MAX);
  return {
    allowed: minute.allowed && daily.allowed,
    resetAt: Math.max(minute.resetAt, daily.resetAt),
    remaining: Math.min(minute.remaining, daily.remaining)
  };
}

async function startServer() {
  const app = express();
  app.disable("x-powered-by");
  app.use(express.json({ limit: "8kb" }));

  app.use((req, res, next) => {
    const origin = req.headers.origin;
    const isChatRequest = req.path === "/api/chat";
    if (isChatRequest && !isAllowedOrigin(origin)) {
      res.status(403).json({ error: "Origin not allowed." });
      return;
    }
    if (origin && (ALLOWED_ORIGINS.length === 0 || ALLOWED_ORIGINS.includes(origin))) {
      res.setHeader("Access-Control-Allow-Origin", origin);
      res.setHeader("Vary", "Origin");
    }
    res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");
    if (req.method === "OPTIONS") {
      res.status(204).end();
      return;
    }
    next();
  });

  app.get("/api/health", (_req, res) => {
    res.json({ status: "ok", model: chatbotModel, profile: YONATAN_PROFILE.publicName });
  });

  app.post("/api/chat", async (req, res) => {
    try {
      const rate = checkRateLimit(req);
      res.setHeader("X-RateLimit-Limit", String(RATE_LIMIT_MAX));
      res.setHeader("X-RateLimit-Remaining", String(rate.remaining));
      if (!rate.allowed) {
        res.setHeader("Retry-After", String(Math.max(1, Math.ceil((rate.resetAt - Date.now()) / 1000))));
        res.status(429).json({
          error: "Rate limit exceeded.",
          response: `I’m getting a lot of questions right now. Please try again shortly, or email Yonatan at ${YONATAN_PROFILE.contactEmail}.`
        });
        return;
      }

      const messages = Array.isArray(req.body?.messages) ? req.body.messages : [];
      const result = await generateChatResponse(messages);
      res.status(result.status).json(result.body);
    } catch (err: any) {
      const rawMessage = String(err?.message || err || "Unknown error");
      const envName = ["GEMINI", "API", "KEY"].join("_");
      const key = process.env[envName] || "";
      const safeMessage = key ? rawMessage.split(key).join("[REDACTED]") : rawMessage;
      console.error("Chat API error:", safeMessage);
      res.status(500).json({
        error: "Chat service unavailable.",
        debug: process.env.DEBUG_ERRORS === "1" ? safeMessage.slice(0, 1200) : undefined,
        response: `I’m having trouble answering right now. Please email Yonatan at ${YONATAN_PROFILE.contactEmail} with what you want to build, automate, analyze, learn, or fix.`
      });
    }
  });

  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({ server: { middlewareMode: true }, appType: "spa" });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (_req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Yonatan portfolio chatbot running on http://0.0.0.0:${PORT}`);
  });
}

startServer();
