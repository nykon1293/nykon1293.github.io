/**
 * Portfolio chatbot lead capture webhook for Google Sheets.
 *
 * Deploy as a Google Apps Script Web App and set the resulting URL as
 * LEAD_WEBHOOK_URL in the Vercel project.
 *
 * Script Properties to set in Apps Script:
 * - SHEET_ID: the destination Google Sheet ID
 * - SHEET_NAME: optional tab name, defaults to "Leads"
 * - LEAD_WEBHOOK_SECRET: optional shared secret. If set, Vercel must send
 *   Authorization: Bearer <secret> via its LEAD_WEBHOOK_SECRET env var.
 */

const DEFAULT_SHEET_NAME = "Leads";
const HEADERS = [
  "Received At",
  "Name",
  "Email",
  "Project / Need",
  "Timeline / Budget",
  "Source",
  "Payload Type"
];

function jsonResponse_(status, body) {
  return ContentService
    .createTextOutput(JSON.stringify({ status, ...body }))
    .setMimeType(ContentService.MimeType.JSON);
}

function getOrCreateSheet_() {
  const props = PropertiesService.getScriptProperties();
  const sheetId = props.getProperty("SHEET_ID");
  const sheetName = props.getProperty("SHEET_NAME") || DEFAULT_SHEET_NAME;

  if (!sheetId) {
    throw new Error("Missing Script Property: SHEET_ID");
  }

  const spreadsheet = SpreadsheetApp.openById(sheetId);
  let sheet = spreadsheet.getSheetByName(sheetName);
  if (!sheet) {
    sheet = spreadsheet.insertSheet(sheetName);
  }

  const firstRow = sheet.getRange(1, 1, 1, HEADERS.length).getValues()[0];
  const needsHeaders = firstRow.every((value) => !value);
  if (needsHeaders) {
    sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
    sheet.setFrozenRows(1);
  }

  return sheet;
}

function isAuthorized_(event) {
  const expected = PropertiesService.getScriptProperties().getProperty("LEAD_WEBHOOK_SECRET");
  if (!expected) return true;

  // Apps Script Web Apps do not consistently expose custom Authorization
  // headers in every deployment mode, so also accept ?secret=... as a fallback.
  const providedByQuery = event && event.parameter && event.parameter.secret;
  const headers = (event && event.headers) || {};
  const authHeader = headers.Authorization || headers.authorization || "";
  const providedByHeader = String(authHeader).replace(/^Bearer\s+/i, "");

  return providedByHeader === expected || providedByQuery === expected;
}

function doPost(event) {
  try {
    if (!isAuthorized_(event)) {
      return jsonResponse_("error", { ok: false, error: "Unauthorized" });
    }

    const raw = event && event.postData && event.postData.contents;
    if (!raw) {
      return jsonResponse_("error", { ok: false, error: "Missing request body" });
    }

    const payload = JSON.parse(raw);
    if (payload.type !== "portfolio_chat_lead") {
      return jsonResponse_("error", { ok: false, error: "Unsupported payload type" });
    }

    const lead = payload.lead || {};
    const row = [
      payload.receivedAt || new Date().toISOString(),
      lead.name || "",
      lead.email || "",
      lead.need || "",
      lead.timeline || "",
      lead.source || "portfolio-chat",
      payload.type || ""
    ];

    const sheet = getOrCreateSheet_();
    sheet.appendRow(row);

    return jsonResponse_("ok", { ok: true, appended: true });
  } catch (error) {
    console.error(error);
    return jsonResponse_("error", { ok: false, error: String(error && error.message || error) });
  }
}

function doGet() {
  return jsonResponse_("ok", {
    ok: true,
    service: "portfolio-chat-lead-webhook",
    message: "Use POST from the portfolio chatbot backend."
  });
}
