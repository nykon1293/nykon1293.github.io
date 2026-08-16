import assert from "node:assert/strict";
import { generateChatResponse } from "../src/chatApiCore.ts";

async function withoutGeminiKey(prompt: string) {
  const previousKey = process.env.GEMINI_API_KEY;
  delete process.env.GEMINI_API_KEY;
  const result = await generateChatResponse([{ sender: "user", text: prompt }]);
  if (previousKey) process.env.GEMINI_API_KEY = previousKey;
  return result;
}

async function assertLocalCanned(prompt: string, expected: RegExp) {
  const result = await withoutGeminiKey(prompt);
  assert.equal(result.status, 200, prompt);
  assert.equal("error" in result.body, false, prompt);
  assert.equal(result.body.source, "local-canned", prompt);
  assert.match(String(result.body.response), expected, prompt);
  return String(result.body.response);
}

async function testDashboardPricingIsSpecificButNoInventedRate() {
  const response = await assertLocalCanned(
    "How much for a dashboard?",
    /great question|pricing|dashboard|complexity|scope|requirements|introductory call/i
  );
  assert.doesNotMatch(response, /\$\d|per hour|hourly rate/i);
  assert.doesNotMatch(response, /email josh\.gemmi@gmail\.com/i);
}

async function testCompoundPricingAnswersAreSpecificButNoInventedRate() {
  const examples: Array<[string, RegExp]> = [
    ["How much to implement AI in my company?", /Pricing for implementing AI in a company[\s\S]*workflows[\s\S]*flat rate[\s\S]*Share/i],
    ["How much for a custom GPT?", /custom GPTs[\s\S]*strong fit[\s\S]*Pricing depends[\s\S]*major Custom GPT workflows[\s\S]*Share/i],
    ["What would it cost to fix our Shopify inventory workflow?", /Pricing for ecommerce[\s\S]*Shopify\/Amazon inventory[\s\S]*Share[\s\S]*store\/channel/i],
    ["How much to clean up HubSpot and our sales pipeline?", /Pricing for CRM[\s\S]*HubSpot\/Salesforce[\s\S]*lead routing[\s\S]*Share/i],
    ["What is the cost for an API integration or internal app?", /Pricing for APIs[\s\S]*internal tools[\s\S]*Share[\s\S]*systems involved/i],
    ["How much for AI tutoring sessions?", /Pricing for tutoring[\s\S]*AI tools[\s\S]*Share[\s\S]*current level/i]
  ];

  for (const [prompt, expected] of examples) {
    const response = await assertLocalCanned(prompt, expected);
    assert.match(response, /30-minute introductory call/i, prompt);
    assert.doesNotMatch(response, /email josh\.gemmi@gmail\.com/i, prompt);
    assert.doesNotMatch(response, /\$\d|per hour|hourly rate/i, prompt);
  }
}

async function testCommonIntentAnswersAvoidGeminiKey() {
  await assertLocalCanned("Does Yonatan offer tutoring or coaching for learning AI tools?", /tutoring|coaching|learn|introductory call/i);
  await assertLocalCanned("Can Yonatan help automate our ecommerce inventory and fulfillment workflow?", /ecommerce|inventory|fulfillment|autom/i);
  await assertLocalCanned("Our business is drowning in spreadsheets and nobody trusts the numbers.", /dashboard|data|spreadsheet|reporting/i);
  await assertLocalCanned("Can he clean up HubSpot and our sales pipeline?", /crm|hubspot|sales|pipeline/i);
  await assertLocalCanned("Can Yonatan build an API integration or internal web app?", /backend|integration|api|internal-tool|tool/i);
  await assertLocalCanned("What services does Yonatan offer?", /consulting|contract|tutoring|dashboards|ecommerce/i);
}

async function testSpreadsheetOptimizationGivesUsefulApproach() {
  const result = await withoutGeminiKey("We currently work out of many different spreadsheets, how can this get optimized?");
  assert.equal(result.status, 200);
  assert.equal(result.body.source, "local-canned");
  assert.equal(result.body.helpAssessment.canHelp, "yes");
  assert.deepEqual(result.body.helpAssessment.matchedSkills, ["Data platform / dashboards"]);
  const response = String(result.body.response);
  assert.match(response, /optimizing a stack of spreadsheets|source of truth|dashboard|data platform/i);
  assert.match(response, /30-minute introductory call/i);
  assert.doesNotMatch(response, /Email josh\.gemmi@gmail\.com/i);
}

async function testProfileIntentAnswersAvoidGeminiKey() {
  await assertLocalCanned("Where can I see his resume or work experience?", /9\+ years|experience|linkedin|resume/i);
  await assertLocalCanned("What projects has Yonatan built?", /projects|data platforms|etl|inventory|crm/i);
  await assertLocalCanned("What skills and tech stack does he have?", /skills|bigquery|cloud run|integrations|ecommerce/i);
  await assertLocalCanned("What are his GitHub and LinkedIn links?", /github\.com|linkedin\.com|introductory call/i);
  await assertLocalCanned("Does he have certifications or credentials?", /salesforce|android enterprise|hubspot|credential/i);
  await assertLocalCanned("Is Yonatan available to hire?", /available|consulting|contract|timeline|30-minute introductory call/i);
  const contact = await assertLocalCanned("How do I get in touch?", /30-minute introductory call/i);
  assert.doesNotMatch(contact, /email|josh\.gemmi@gmail\.com/i);
}

async function testCustomGPTIsStrongFit() {
  const result = await withoutGeminiKey("How much for a custom GPT?");
  assert.equal(result.status, 200);
  assert.equal(result.body.source, "local-canned");
  assert.equal(result.body.helpAssessment.canHelp, "yes");
  assert.deepEqual(result.body.helpAssessment.matchedSkills, ["Agentic AI automation"]);
  assert.match(String(result.body.response), /custom GPTs|major Custom GPT workflows|strong fit/i);
}

async function testUncoveredQuestionFallsBackCleanlyWithoutGeminiKey() {
  const result = await withoutGeminiKey("What color should I paint my kitchen cabinets? Be specific.");
  assert.equal(result.status, 200);
  assert.equal(result.body.source, "local-fallback");
  assert.match(String(result.body.response), /30-minute introductory call|share/i);
  assert.deepEqual(result.body.helpAssessment.matchedSkills, []);
}

async function testLatestQuestionControlsIntentAfterDashboardContext() {
  const previousKey = process.env.GEMINI_API_KEY;
  delete process.env.GEMINI_API_KEY;
  const result = await generateChatResponse([
    { sender: "user", text: "How much for a dashboard?" },
    { sender: "bot", text: "Dashboard pricing depends on scope." },
    { sender: "user", text: "Can Yonatan help implement AI in my business operations?" }
  ]);
  if (previousKey) process.env.GEMINI_API_KEY = previousKey;

  assert.equal(result.status, 200);
  assert.equal(result.body.source, "local-canned");
  assert.match(String(result.body.response), /AI automation|workflow implementation/i);
  assert.doesNotMatch(String(result.body.response), /^Yes — dashboards/i);
  assert.deepEqual(result.body.helpAssessment.matchedSkills, ["Agentic AI automation"]);
}

await testDashboardPricingIsSpecificButNoInventedRate();
await testCompoundPricingAnswersAreSpecificButNoInventedRate();
await testCommonIntentAnswersAvoidGeminiKey();
await testSpreadsheetOptimizationGivesUsefulApproach();
await testProfileIntentAnswersAvoidGeminiKey();
await testCustomGPTIsStrongFit();
await testUncoveredQuestionFallsBackCleanlyWithoutGeminiKey();
await testLatestQuestionControlsIntentAfterDashboardContext();
console.log("chatApiCore canned answer tests passed");
