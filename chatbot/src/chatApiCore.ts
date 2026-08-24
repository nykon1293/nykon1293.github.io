import { GoogleGenAI } from "@google/genai";
import { YONATAN_PROFILE, introCallCta } from "./yonatanProfile.js";

export type ChatMessage = {
  sender?: "user" | "bot";
  role?: "user" | "model";
  text?: string;
  content?: string;
};

const DEFAULT_MODEL = process.env.GEMINI_MODEL || "gemini-3.7-flash";
const MAX_MESSAGE_CHARS = Number(process.env.MAX_MESSAGE_CHARS || 800);
const MAX_HISTORY_MESSAGES = Number(process.env.MAX_HISTORY_MESSAGES || 6);
const CAUTION_TERMS = ["legal", "lawyer", "contract", "tax", "medical", "doctor", "investment advice", "financial advice", "securities"];

function cleanText(value: unknown) {
  return String(value || "").replace(/\s+/g, " ").trim().slice(0, MAX_MESSAGE_CHARS);
}

export function normalizeMessages(messages: ChatMessage[]) {
  return messages
    .slice(-MAX_HISTORY_MESSAGES)
    .map((message) => {
      const role = message.role || (message.sender === "bot" ? "model" : "user");
      const text = cleanText(message.text || message.content);
      return text ? { role: role === "model" ? "model" : "user", parts: [{ text }] } : null;
    })
    .filter(Boolean) as Array<{ role: "user" | "model"; parts: Array<{ text: string }> }>;
}

function hasSkillTerm(text: string, term: string) {
  if (term === "ai") return /\bai\b/.test(text);
  return text.includes(term);
}

export function assessFit(contents: ReturnType<typeof normalizeMessages>) {
  const latest = contents[contents.length - 1]?.parts[0]?.text?.toLowerCase() || "";
  const skillMatches = [
    { skill: "Agentic AI automation", terms: ["hermes", "hermes agent", "hermes agents", "ai", "agent", "agentic", "multi-agent", "multi agent", "automation", "chatbot", "custom gpt", "gpts", "gpt", "chatgpt", "openai", "gemini", "llm", "claude", "workflow"] },
    { skill: "Data platform / dashboards", terms: ["dashboard", "dashboards", "data", "bigquery", "etl", "reporting", "analytics", "data pipeline", "etl pipeline", "spreadsheet", "spreadsheets", "sheets", "source system", "source systems", "numbers"] },
    { skill: "Ecommerce operations", terms: ["ecommerce", "amazon", "ebay", "inventory", "warehouse", "fulfillment", "listing", "seller"] },
    { skill: "PPC / advertising operations", terms: ["ppc", "advertising", "ad spend", "campaign", "campaigns", "acos", "roas", "keyword bid", "budget pacing"] },
    { skill: "Social content operations", terms: ["social media", "instagram", "tiktok", "content calendar", "content workflow", "content operations", "creative approval", "publishing workflow"] },
    { skill: "CRM / sales operations", terms: ["salesforce", "hubspot", "crm", "sales ops", "pipeline"] },
    { skill: "Cloud/backend implementation", terms: ["cloud", "api", "integration", "backend", "next.js", "supabase", "database"] },
    { skill: "Technical operations", terms: ["network", "workstation", "mdm", "android", "samsung", "phonecheck", "it support", "process"] },
    { skill: "Tutoring / coaching / project help", terms: ["tutor", "tutoring", "teach", "teacher", "lesson", "lessons", "student", "mentor", "mentoring", "coach", "coaching", "training", "learn", "help me", "explain"] }
  ];

  const matchedSkills = skillMatches
    .filter((item) => item.terms.some((term) => hasSkillTerm(latest, term)))
    .map((item) => item.skill);

  const needsSpecifics = containsCautionTopic(latest);
  const canHelp = matchedSkills.length && !needsSpecifics ? "yes" : "maybe";

  return {
    canHelp,
    reason: canHelp === "yes"
      ? "The request overlaps with Yonatan's AI, data, ecommerce, PPC/advertising, social content, CRM, cloud/backend, technical operations, tutoring, or project-help work."
      : "Yonatan can review the specifics on a free 30-minute introductory call and either help directly or route the request appropriately.",
    matchedSkills
  };
}

export function containsCautionTopic(text: string) {
  const latest = text.toLowerCase();
  return CAUTION_TERMS.some((term) => latest.includes(term));
}

export function fallbackAnswer(assessment: ReturnType<typeof assessFit>, visitorText: string) {
  if (containsCautionTopic(visitorText)) {
    return `That may need a closer look. Regulated specifics like legal, tax, medical, financial, or investment advice should be handled by a qualified professional, but Yonatan can still review the operational, AI, data, workflow, or implementation context and either help directly or route you. ${introCallCta("that operational context and a few times that work for you")}`;
  }

  if (assessment.canHelp === "yes") {
    const skills = assessment.matchedSkills.slice(0, 3).join(", ");
    return `Yes — this looks aligned with Yonatan’s work${skills ? ` around ${skills}` : ""}. He can help with consulting, contract work, tutoring/coaching, technical troubleshooting, AI automation, data platforms, ecommerce, PPC/advertising, social content operations, dashboards, integrations, and practical implementation. ${introCallCta("the specific goal, current tools, and a few times that work for you")}`;
  }

  return `Hi — I’m Yonatan’s AI Project Scout. Tell me what you’re trying to automate, build, analyze, learn, fix, or understand. Yonatan can help with consulting, tutoring/coaching, AI workflows, data platforms, ecommerce operations, PPC/advertising, social content operations, dashboards, integrations, and technical troubleshooting. ${introCallCta()}`;
}

function hasAny(text: string, patterns: RegExp[]) {
  return patterns.some((pattern) => pattern.test(text));
}

// Refactored: Rules-based approach for maintainability
type CannedRule = {
  name: string;
  test: (text: string, assessment: ReturnType<typeof assessFit>) => boolean;
  answer: (text: string, assessment: ReturnType<typeof assessFit>) => string;
};

const cannedRules: CannedRule[] = [
  {
    name: "caution",
    test: (text) => containsCautionTopic(text),
    answer: (visitorText) => fallbackAnswer({ canHelp: "maybe", reason: "", matchedSkills: [] }, visitorText)
  },
  {
    name: "payment-methods",
    test: (text) => hasAny(text, [
      /\b(usdc|bitcoin|\bbtc\b|crypto|cryptocurrency|stablecoin|digital payments?|zelle|bank wire|wire transfer|bank transfer|x money|xmoney)\b/,
      /pay (in|with|via) (crypto|bitcoin|btc|usdc|zelle|wire|x money|xmoney)/,
      /payment methods?/,
      /how (can|do) i pay/,
      /ways? to pay/
    ]),
    answer: () => `Yonatan accepts bank wire, Zelle, X Money, USDC, or Bitcoin (BTC). Other crypto only if he agrees first. Inquire for more info on the free 30-minute introductory call. Account, Zelle, X Money, and wallet details are not posted on the site.`
  },
  {
    name: "pricing-hermes",
    test: (text) => hasAny(text, [/\b(price|pricing|cost|costs|charge|charges|rate|rates|budget|quote|estimate|fee|fees)\b/, /how much/]) && hasAny(text, [/\bhermes\b/, /\bdesk\b/, /\bdesks\b/, /\bagent setup\b/, /\bset up an agent\b/, /\bsetup an agent\b/, /\bagent install\b/]),
    answer: () => `Hermes setups are packaged Desks: Starter Desk $500, Operator Desk $1,500, and Connected Desk $3,500. CRM plus books is Connected, not Starter. The free 30-minute introductory call classifies which Desk fits. ${introCallCta("what you want the agent to do, which tools it should use, and a few times that work")}`
  },
  {
    name: "desk-not-required",
    test: (text) => hasAny(text, [
      /do i (need|have to) (get |buy |use )?(a |an )?(hermes )?(desk|agent)/,
      /have to (get|buy|use) (a |an )?(hermes )?desk/,
      /is (a )?(hermes )?desk (required|mandatory|necessary)/,
      /every (project|build|job) .{0,24}(hermes )?desk/,
      /always (need |get |buy |use )?(a |an )?(hermes )?desk/,
      /not always (a |an )?(hermes )?desk/
    ]),
    answer: () => `No. Discovery and builds are custom work: dashboards, system integrations, reporting systems, workflow automation, and cleanup of tools you already have. A Hermes Desk is not required. Paid discovery ($2,000) maps the work first. The build after that is quoted, usually $4,500–15,000. A Desk is only used when it actually fits. ${introCallCta("the work you want fixed, the tools you already use, and a few times that work")}`
  },
  {
    name: "pricing-custom-gpt",
    test: (text, assessment) => hasAny(text, [/\b(price|pricing|cost|costs|charge|charges|rate|rates|budget|quote|estimate|fee|fees)\b/, /how much/]) && hasAny(text, [/\bcustom gpts?\b/, /\bgpts?\b/, /\bcustom chatgpt\b/, /\bopenai assistant\b/, /\bchatgpt bot\b/]),
    answer: () => `Yes — custom GPTs and GPT-style workflow tools are a strong fit. Pricing depends on what the GPT needs to do, how much source material or process knowledge it needs, whether it needs actions/integrations, how sensitive the data is, and whether you need a quick prototype or a production-ready assistant with testing, documentation, and handoff. Yonatan has built major Custom GPT workflows and can walk through the right version on a free 30-minute introductory call. ${introCallCta("the goal, users, inputs/outputs, and a few times that work")}`
  },
  {
    name: "pricing-ppc-social",
    test: (text) => hasAny(text, [/\b(price|pricing|cost|costs|charge|charges|rate|rates|budget|quote|estimate|fee|fees)\b/, /how much/]) && hasAny(text, [/\b(ppc|advertising|ads?|ad spend|campaigns?|acos|roas|social media|instagram|tiktok|content calendar|content workflow|creative approval)\b/]),
    answer: () => `Pricing for PPC, advertising, or social content operations depends on the channels, campaign or content volume, available data, required integrations, approval process, and whether you need an audit, a workflow build, ongoing optimization support, or a managed operating system. A free 30-minute introductory call is the right place to walk through the current process rather than inventing a flat rate here. ${introCallCta("the channels, bottleneck, and a few times that work")}`
  },
  {
    name: "pricing-ecommerce",
    test: (text) => hasAny(text, [/\b(price|pricing|cost|costs|charge|charges|rate|rates|budget|quote|estimate|fee|fees)\b/, /how much/]) && hasAny(text, [/\b(ecommerce|e-commerce|amazon|ebay|shopify|inventory|warehouse|fulfillment|listing|seller|fba|rma)\b/]),
    answer: () => `Great question! Pricing for ecommerce or inventory operations work depends on the workflow, sales channels, systems involved, data quality, and whether you need advice, cleanup, dashboards, automations, or a production-ready process. For example, a Shopify/Amazon inventory fix is very different from a full fulfillment, listing, PO, and reporting workflow. ${introCallCta("the store/channel, current tools, bottleneck, and a few times that work")}`
  },
  {
    name: "pricing-crm",
    test: (text) => hasAny(text, [/\b(price|pricing|cost|costs|charge|charges|rate|rates|budget|quote|estimate|fee|fees)\b/, /how much/]) && hasAny(text, [/\b(crm|salesforce|hubspot|sales ops|pipeline management|lead routing|vendor)\b/]),
    answer: () => `Great question! Pricing for CRM or sales-ops cleanup depends on the platform, data quality, number of workflows, automations, reporting needs, and how much process mapping is required. A quick HubSpot/Salesforce cleanup is different from rebuilding lead routing, pipeline visibility, dashboards, and team workflows. ${introCallCta("the CRM, pain points, desired outcome, and a few times that work")}`
  },
  {
    name: "pricing-backend",
    test: (text) => hasAny(text, [/\b(price|pricing|cost|costs|charge|charges|rate|rates|budget|quote|estimate|fee|fees)\b/, /how much/]) && hasAny(text, [/\b(api|apis|integration|integrations|backend|database|supabase|cloud|google cloud|cloud run|next\.js|app|web app|internal tool|tooling)\b/]),
    answer: () => `Great question! Pricing for APIs, integrations, backends, or internal tools depends on what needs to connect, the current state of the systems, data/security requirements, deployment needs, and how production-ready the tool must be. A small integration is very different from a reliable internal app with auth, database work, monitoring, and handoff documentation. ${introCallCta("the systems involved, desired workflow, and a few times that work")}`
  },
  {
    name: "pricing-tutoring",
    test: (text) => hasAny(text, [/\b(price|pricing|cost|costs|charge|charges|rate|rates|budget|quote|estimate|fee|fees)\b/, /how much/]) && hasAny(text, [/\b(tutor|tutoring|coach|coaching|teach|teacher|mentor|mentoring|lesson|lessons|learn|training|student)\b/, /help me understand/, /explain .* to me/]),
    answer: () => `Tutoring is $125 per hour, with a 90-minute minimum of $175. That is the only metered service. Larger “help me decide” work is paid discovery, not tutoring. ${introCallCta("what you want to learn or build, your current level, and a few times that work")}`
  },
  {
    name: "pricing-ai",
    test: (text) => hasAny(text, [/\b(price|pricing|cost|costs|charge|charges|rate|rates|budget|quote|estimate|fee|fees)\b/, /how much/]) && hasAny(text, [/\b(ai|gpt|gpts|custom gpt|chatgpt|openai|gemini|claude|llm|agent|agents|agentic|chatbot)\b/, /implement ai/, /use ai/, /ai automation/, /automate with ai/, /custom gpt/, /custom chatgpt/]),
    answer: () => `Great question! Pricing for implementing AI in a company depends on what the AI needs to do, how many workflows or teams are involved, what tools/data it must connect to, how much cleanup is needed, and whether the work is a small pilot, an internal chatbot, an automation layer, or a broader operating system. Company-wide AI work is not a Starter Desk install. It usually starts with a free 30-minute introductory call, then paid discovery, then a quoted build. ${introCallCta("the business process you want improved, current tools, and a few times that work")}`
  },
  {
    name: "pricing-dashboard",
    test: (text) => hasAny(text, [/\b(price|pricing|cost|costs|charge|charges|rate|rates|budget|quote|estimate|fee|fees)\b/, /how much/]) && hasAny(text, [/\b(dashboard|dashboards|data|etl|analytics|reporting|reports|kpi|bigquery|data pipeline|etl pipeline|spreadsheet|spreadsheets|sheets|numbers)\b/]),
    answer: () => `Dashboard and data jobs are quoted after paid discovery, not as a single number from this chat. Published builds sit in a $4,500–15,000 range once the work is scoped. The first step is a free 30-minute introductory call. ${introCallCta("your data sources, current reporting pain, desired metrics, and a few times that work")}`
  },
  {
    name: "pricing-care",
    test: (text) => hasAny(text, [/\bcare retainers?\b/, /\bretainers?\b/, /\bstarter care\b/, /\boperator care\b/, /\bongoing care\b/, /\bmonthly care\b/]) || (/\bcare\b/.test(text) && hasAny(text, [/\b(750|1,?500|month|monthly|desk|fix|fixes|handoff|include|included|cover)\b/])),
    answer: () => `Care starts after a Desk or a build is live. It is month to month, with 30 days' notice to cancel. Starter Care is $750 a month: fixes when something stops working, small edits, a monthly check, help changing the model on the same Desk, and short questions from the people who use it. It does not add new systems. Operator Care is $1,500 a month: everything in Starter Care, plus one small add each month on the system you already have. Care is not unlimited chat, not a new Desk, and not a rebuild. Named setups are on https://nykon1293.github.io/pricing.html#retainers. ${introCallCta("the live system you want kept useful, and a few times that work")}`
  },
  {
    name: "pricing-discovery",
    test: (text) => hasAny(text, [/\b(price|pricing|cost|costs|charge|charges|rate|rates|budget|quote|estimate|fee|fees)\b/, /how much/, /\bwhat is\b/, /\bwhat does\b/]) && hasAny(text, [/\bpaid discovery\b/, /\bdiscovery\b/, /\bbuild after discovery\b/, /\bcustom build\b/]),
    answer: () => `Paid Discovery is $2,000. It maps one workflow so we can quote the custom work: a dashboard, system integration, report, automation, or cleanup. The build after that is quoted, usually $4,500–15,000. A Hermes Desk is only one option, and only when it fits. The free 30-minute introductory call is only a scan. ${introCallCta("the work you want diagnosed, current tools, and a few times that work")}`
  },
  {
    name: "general-pricing",
    test: (text) => hasAny(text, [/\b(price|pricing|cost|costs|charge|charges|rate|rates|budget|quote|estimate|fee|fees)\b/, /how much/]),
    answer: () => `Yonatan publishes named setups: Hermes Starter Desk $500, Operator Desk $1,500, Connected Desk $3,500; Paid Discovery $2,000; Care $750 or $1,500 a month; Advisory Light $4,500 a month; Fractional CTO $7,500 a month; tutoring $125/hr. Custom builds after discovery are for dashboards, system integrations, reporting, and similar custom work — not always a Desk. The free 30-minute introductory call classifies which one applies. Details are on https://nykon1293.github.io/pricing.html. ${introCallCta("the goal, current tools, and a few times that work")}`
  },
  {
    name: "contact",
    test: (text) => hasAny(text, [/\b(contact|email|reach|book|schedule|get in touch|talk to|call)\b/, /how do i get in touch/]),
    answer: () => `The best next step is a free 30-minute introductory call. Share what you want to build, fix, learn, or automate; the tools or systems involved; and a few times that work. Yonatan will use that to prepare and confirm a time.`
  },
  {
    name: "availability",
    test: (text) => hasAny(text, [/\b(available|availability|when can|timeline|start|taking clients|open to work|hire|hiring)\b/]),
    answer: () => `Yonatan is available for consulting, contract work, tutoring/coaching, technical troubleshooting, AI implementation, dashboards, ecommerce operations, CRM/workflow cleanup, and operator-builder engagements. Availability depends on the scope and timing. ${introCallCta("the project details, desired timeline, and a few times that work")}`
  },
  {
    name: "resume",
    test: (text) => hasAny(text, [/\b(resume|cv|work history|experience|background|career|jobs|roles)\b/, /where has .* worked/]),
    answer: () => `Yonatan has 9+ years across technical operations, ecommerce systems, data platforms, AI-assisted development, CRM/sales ops, and hands-on implementation. Recent work includes building data platforms and operations cockpits for multi-brand ecommerce environments, plus prior leadership in serialized inventory, ecommerce, CRM cleanup, and technical operations. For a resume or deeper background, email ${YONATAN_PROFILE.contactEmail} or view his LinkedIn: ${YONATAN_PROFILE.linkedInUrl}. To talk through a project, ${introCallCta("what you need and a few times that work", true)}`
  },
  {
    name: "projects",
    test: (text) => hasAny(text, [/\b(project|projects|portfolio|case stud|built|examples|show me|proof)\b/]),
    answer: () => `Examples of Yonatan’s work include production data platforms, ecommerce operations cockpits, PPC audit and campaign-management workflows, approval-led social content operations, ETL/reporting pipelines, inventory and PO sync automation, GPT-powered listing workflows, CRM/process cleanup, and technical troubleshooting systems. The most relevant examples depend on what you are trying to build. ${introCallCta("the use case and a few times that work")}`
  },
  {
    name: "skills",
    test: (text) => hasAny(text, [/\b(skill|skills|tech stack|technologies|tools|programming|code|developer|engineer)\b/]),
    answer: () => `Yonatan’s strongest areas are AI-augmented development, workflow automation, dashboards/data platforms, BigQuery, Google Cloud, Cloud Run, ETL pipelines, Next.js-style app work, REST/GraphQL integrations, Salesforce/HubSpot workflows, ecommerce operations, PPC audit and campaign-management workflows, social content operations, and technical operations. If you have a specific tool or stack in mind, ${introCallCta("that context and a few times that work", true)}`
  },
  {
    name: "links",
    test: (text) => hasAny(text, [/\b(github|git hub|linkedin|linked in|links|profile)\b/]),
    answer: () => `You can find Yonatan on LinkedIn at ${YONATAN_PROFILE.linkedInUrl} and GitHub at ${YONATAN_PROFILE.githubUrl}. For a project conversation, ${introCallCta("a short note about what you need and a few times that work", true)}`
  },
  {
    name: "credentials",
    test: (text) => hasAny(text, [/\b(education|degree|school|college|university|certification|certifications|certified|credential|credentials)\b/]),
    answer: () => `Yonatan’s approved public credentials include Salesforce Trailhead Mountaineer, Android Enterprise Certified Professional, Samsung Knox Professional, Galaxy Business Associate / Samsung Tactical Edition, Phonecheck Implementation Certified, HubSpot Sales Certification, and Advanced Google Sheets systems development. If you need formal background details for a role or engagement, ${introCallCta("what you are hiring for and a few times that work", true)}`
  },
  {
    name: "tutoring",
    test: (text) => hasAny(text, [/\b(tutor|tutoring|coach|coaching|teach|teacher|mentor|mentoring|lesson|lessons|learn|training|student)\b/, /help me understand/, /explain .* to me/]),
    answer: () => `Yes — Yonatan offers tutoring, coaching, and hands-on project help. This can include learning AI tools, understanding automations, building dashboards, improving ecommerce workflows, troubleshooting technical issues, or getting guided help on a project. ${introCallCta("what you want to learn or build and a few times that work")}`
  },
  {
    name: "ecommerce",
    test: (text) => hasAny(text, [/\b(ecommerce|e-commerce|amazon|ebay|shopify|inventory|warehouse|fulfillment|listing|seller|fba|rma|ppc|advertising|campaign|acos|roas)\b/]),
    answer: () => `Yes — ecommerce operations are a strong fit. Yonatan has hands-on experience with Amazon/eBay operations, inventory and warehouse workflows, listing automation, fulfillment processes, PPC audit and campaign-management workspaces, and dashboards that make messy operational data usable. ${introCallCta("the store, workflow, bottleneck, and a few times that work")}`
  },
  {
    name: "dashboard",
    test: (text) => hasAny(text, [/\b(dashboard|dashboards|data|etl|analytics|reporting|reports|kpi|bigquery|data pipeline|etl pipeline|spreadsheet|spreadsheets|sheets|numbers)\b/]),
    answer: () => `Yes — optimizing a stack of spreadsheets is a strong fit. A good first pass is usually to map which sheets feed which decisions, identify the source of truth, remove duplicate/manual entry, standardize the key fields, then turn the important outputs into a cleaner dashboard, reporting flow, or lightweight data platform. Helpful specifics are: how many spreadsheets there are, who updates them, what systems they come from, where mistakes happen, and what decisions the reporting needs to support. ${introCallCta("those details and a few times that work")}`
  },
  {
    name: "crm",
    test: (text) => hasAny(text, [/\b(crm|salesforce|hubspot|sales ops|pipeline management|lead routing|vendor)\b/]),
    answer: () => `Yes — CRM and sales-operations workflow cleanup may be a fit. Yonatan can help map the actual process, clean up Salesforce/HubSpot-style workflows, improve visibility, and connect CRM work to reporting or automation. ${introCallCta("the current CRM, pain points, desired outcome, and a few times that work")}`
  },
  {
    name: "tech-ops",
    test: (text) => hasAny(text, [/\b(network|workstation|computer|mdm|android|samsung|phonecheck|technical support|troubleshooting|it support)\b/]),
    answer: () => `Yes — small-business technical operations and troubleshooting may be a fit. Yonatan has experience across workstation setup, network/process troubleshooting, MDM/mobile-device operations, diagnostics workflows, and practical implementation. ${introCallCta("the environment, the issue, and a few times that work")}`
  },
  {
    name: "what-is-hermes",
    test: (text) => hasAny(text, [
      /what(?:'s| is) hermes/,
      /explain hermes/,
      /what does hermes do/,
      /what(?:'s| is) a hermes agent/,
      /what(?:'s| is) a hermes desk/
    ]),
    answer: () => `Hermes is an AI agent you run on your own computer. ChatGPT and Claude are chat boxes. Hermes is the software around them: it uses the model you choose, works with your files and tools, follows written limits, and remembers your rules. Yonatan installs it as a named Desk — Starter, Operator, or Connected — then hands it off so you can run it. ${introCallCta("what you want the agent to do, which tools it should use, and a few times that work")}`
  },
  {
    name: "hermes-agents",
    test: (text) => hasAny(text, [/\bhermes\b/, /\bagentic ai\b/, /\bagent setup\b/, /\bset up an agent\b/, /\bsetup an agent\b/]),
    answer: () => `Yes — setting up Hermes Agents is a strong fit. Hermes is an AI agent on your computer, not another chat tab. Yonatan installs it as a named Desk — Starter, Operator, or Connected — then hands it off so you can run it. The free 30-minute introductory call classifies which Desk fits. ${introCallCta("what you want the agent to do, which tools it should use, and a few times that work")}`
  },
  {
    name: "custom-gpt",
    test: (text) => hasAny(text, [/\bcustom gpts?\b/, /\bgpts?\b/, /\bcustom chatgpt\b/, /\bopenai assistant\b/, /\bchatgpt bot\b/]),
    answer: () => `Yes — custom GPTs and GPT-style assistants are a strong fit. Yonatan has built major Custom GPT workflows and can help design the knowledge structure, instructions, workflows, actions/integrations, testing loop, and handoff so the assistant is actually useful in a real process. ${introCallCta("what the GPT should do, who will use it, and a few times that work")}`
  },
  {
    name: "ai-general",
    test: (text) => hasAny(text, [/\b(ai|gpt|gpts|custom gpt|chatgpt|openai|gemini|claude|llm|agent|agents|agentic|chatbot|automation|automate|workflow)\b/]),
    answer: () => `Yes — AI automation and practical workflow implementation are a strong fit. Yonatan can help design and build chatbot workflows, Custom GPTs, LLM-assisted processes, agentic development workflows, reporting automation, research/drafting systems, and operational tools that plug into real business processes. ${introCallCta("the workflow you want to improve, the tools you use today, and a few times that work")}`
  },
  {
    name: "backend",
    test: (text) => hasAny(text, [/\b(api|apis|integration|integrations|backend|database|supabase|cloud|google cloud|cloud run|bigquery|next\.js|app|web app|internal tool|tooling)\b/]),
    answer: () => `Yes — backend, integration, and internal-tool work can be a fit when it connects to a real workflow or operational problem. Yonatan can help with APIs, databases, Cloud Run/Google Cloud-style deployments, data flows, dashboards, and practical internal tools. ${introCallCta("what needs to connect, what currently exists, and a few times that work")}`
  },
  {
    name: "services",
    test: (text) => hasAny(text, [/\b(services|offer|offers|paid help|consulting|contract work|project help|what can|what kind|what kinds)\b/]),
    answer: () => `Yonatan offers Hermes Agent setup, consulting, contract work, tutoring/coaching, AI implementation, data platforms, dashboards, ecommerce operations, CRM/workflow cleanup, technical troubleshooting, and hands-on project help. The best fit is messy real-world work where he can understand the process, build or fix the system, train people, and verify the result. ${introCallCta("the specific goal, current tools, and a few times that work")}`
  }
];

export function localCannedAnswer(assessment: ReturnType<typeof assessFit>, visitorText: string) {
  const text = visitorText.toLowerCase();

  for (const rule of cannedRules) {
    if (rule.test(text, assessment)) {
      return rule.answer(visitorText, assessment);
    }
  }

  return null;
}

function buildSystemInstruction() {
  const skills = Object.entries(YONATAN_PROFILE.coreSkills)
    .map(([category, items]) => `- ${category}: ${items.join(", ")}`)
    .join("\n");
  const experience = YONATAN_PROFILE.experience
    .map((job) => `${job.company} (${job.role}, ${job.period}): ${job.highlights.join(" ")}`)
    .join("\n");

  return `You are Yonatan’s AI Project Scout for ${YONATAN_PROFILE.publicName}.

Positioning: ${YONATAN_PROFILE.positioning}
Availability: ${YONATAN_PROFILE.availability}
Contact: ${YONATAN_PROFILE.contactEmail}
LinkedIn: ${YONATAN_PROFILE.linkedInUrl}

Summary:
${YONATAN_PROFILE.summary.map((item) => `- ${item}`).join("\n")}

Core skills:
${skills}

Experience facts:
${experience}

Credentials:
${YONATAN_PROFILE.credentials.map((item) => `- ${item}`).join("\n")}

Good fit:
${YONATAN_PROFILE.goodFit.map((item) => `- ${item}`).join("\n")}

Potential limits:
${YONATAN_PROFILE.notFit.map((item) => `- ${item}`).join("\n")}

Rules:
${YONATAN_PROFILE.answerRules.map((item) => `- ${item}`).join("\n")}

Answer in 2-5 short sentences. Be helpful and direct. Never ask for private credentials or sensitive data. Always close by inviting a free 30-minute introductory call: ask the visitor to share the problem, current tools or systems, and a few times that work so Yonatan can confirm a time. Do not tell them to email in order to schedule. Do not invent prices.`;
}

function isTransientAiError(message: string) {
  return ["UNAVAILABLE", "RESOURCE_EXHAUSTED", "503", "502", "504", "429", "high demand", "try again later"]
    .some((token) => message.toLowerCase().includes(token.toLowerCase()));
}

async function sleep(ms: number) {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

function getGeminiClient() {
  const envName = ["GEMINI", "API", "KEY"].join("_");
  const apiKey = process.env[envName];
  if (!apiKey) throw new Error(`${envName} is not configured.`);
  return new GoogleGenAI({ apiKey });
}

export async function generateChatResponse(messages: ChatMessage[]) {
  const contents = normalizeMessages(messages);
  if (contents.length === 0 || contents[contents.length - 1].role !== "user") {
    return { status: 400, body: { error: "A visitor message is required." } };
  }

  const assessment = assessFit(contents);
  const visitorText = contents[contents.length - 1].parts[0].text;
  const cannedAnswer = localCannedAnswer(assessment, visitorText);
  if (cannedAnswer) {
    return { status: 200, body: { response: cannedAnswer, helpAssessment: assessment, source: "local-canned" } };
  }

  try {
    let answer = "";
    for (let attempt = 1; attempt <= 3; attempt += 1) {
      try {
        const client = getGeminiClient();
        const response = await client.models.generateContent({
          model: DEFAULT_MODEL,
          contents,
          config: {
            systemInstruction: buildSystemInstruction(),
            temperature: 0.4,
            maxOutputTokens: 350,
            thinkingConfig: { thinkingBudget: 0 }
          }
        });
        answer = (response.text || "").trim();
        break;
      } catch (err: any) {
        const rawMessage = String(err?.message || err || "Unknown error");
        if (!isTransientAiError(rawMessage) || attempt === 3) throw err;
        await sleep(350 * attempt);
      }
    }

    return {
      status: 200,
      body: {
        response: answer || fallbackAnswer(assessment, visitorText),
        helpAssessment: assessment,
        source: "gemini"
      }
    };
  } catch (err: any) {
    const rawMessage = String(err?.message || err || "Unknown error");
    const noConfiguredKey = rawMessage.includes("GEMINI_API_KEY is not configured");
    const status = isTransientAiError(rawMessage) || noConfiguredKey ? 200 : 500;
    return {
      status,
      body: {
        error: status === 500 ? "Chat service unavailable." : undefined,
        debug: process.env.DEBUG_ERRORS === "1" ? rawMessage.slice(0, 1200) : undefined,
        response: fallbackAnswer(assessment, visitorText),
        helpAssessment: assessment,
        source: "local-fallback"
      }
    };
  }
}

export const chatbotModel = DEFAULT_MODEL;