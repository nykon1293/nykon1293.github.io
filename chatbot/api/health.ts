import type { VercelRequest, VercelResponse } from "@vercel/node";
import { chatbotModel } from "../src/chatApiCore.js";
import { YONATAN_PROFILE } from "../src/yonatanProfile.js";

export default function handler(_req: VercelRequest, res: VercelResponse) {
  res.status(200).json({ status: "ok", model: chatbotModel, profile: YONATAN_PROFILE.publicName });
}
