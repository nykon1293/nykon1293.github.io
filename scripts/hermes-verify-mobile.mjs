import { chromium } from "playwright";

const urls = process.argv.slice(2);
if (!urls.length) {
  console.error("usage: node scripts/hermes-verify-mobile.mjs <url>...");
  process.exit(2);
}

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
const out = [];
for (const url of urls) {
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 20000 });
  const data = await page.evaluate(() => {
    const vw = document.documentElement.clientWidth;
    const sw = document.documentElement.scrollWidth;
    const bodySW = document.body.scrollWidth;
    const lead = document.querySelector(".lead");
    const cs = (el) => (el ? getComputedStyle(el) : null);
    const lum = (c) => {
      const m = c.match(/rgba?\(([^)]+)\)/);
      if (!m) return null;
      const p = m[1].split(",").map((x) => parseFloat(x.trim()));
      const [r, g, b] = p;
      const f = (v) => {
        v /= 255;
        return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
      };
      return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
    };
    const ratio = (fg, bg) => {
      const L1 = lum(fg);
      const L2 = lum(bg);
      if (L1 == null || L2 == null) return null;
      const hi = Math.max(L1, L2);
      const lo = Math.min(L1, L2);
      return (hi + 0.05) / (lo + 0.05);
    };
    const bodyBg = cs(document.body).backgroundColor;
    const leadRatio = lead ? ratio(cs(lead).color, bodyBg) : null;
    return {
      vw,
      sw,
      bodySW,
      overflow: sw > vw + 2 || bodySW > vw + 2,
      leadRatio,
    };
  });
  out.push({ url, ...data });
}
await browser.close();
console.log(JSON.stringify(out));