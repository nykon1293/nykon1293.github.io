import React, { useEffect, useRef, useState } from "react";
import { Bot, CheckCircle, HelpCircle, Loader2, MessageCircle, Send, Sparkles, Trash2, User, X } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { Message } from "../types";

const SUGGESTIONS = [
  "Does Yonatan offer tutoring or coaching?",
  "Can Yonatan help automate our ecommerce operations?",
  "We need dashboards from messy data sources. Is that a fit?",
  "What kinds of help does he offer?"
];

const WELCOME_MESSAGE = "Hi — I’m Yonatan’s AI Project Scout. Tell me what you’re trying to automate, build, analyze, learn, fix, or understand. Share a few details and we can set up a free 30-minute introductory call.";

type LeadDraft = {
  name: string;
  email: string;
  need: string;
  timeline: string;
};

const EMPTY_LEAD: LeadDraft = { name: "", email: "", need: "", timeline: "" };

function nowStamp() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function botMessage(text: string, extras: Partial<Message> = {}): Message {
  return {
    id: `bot-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    sender: "bot",
    text,
    timestamp: nowStamp(),
    ...extras
  };
}

function isValidEmail(value: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(value.trim());
}

function isPositiveLeadReply(text: string) {
  const value = text.trim();
  return /^(yes|yeah|yep|sure|ok|okay|please|send|send note|send a note|yes[,.!]?\s*send (a )?note|request a call|book a call|let'?s talk|contact me|have him contact me|let'?s do it|start)$/i.test(value);
}

function isNegativeLeadReply(text: string) {
  return /^(no|nope|not now|later|skip|cancel|never mind)$/i.test(text.trim());
}

function isLeadWorthyPrompt(text: string) {
  return /\b(hire|hiring|available|availability|contact|email|call|schedule|book|quote|estimate|pricing|price|cost|budget|project|consulting|contract|client|follow up|reach out)\b/i.test(text);
}

function shouldOfferLeadCapture(question: string, answer: string, assessment: Message["helpAssessment"] | null) {
  if (assessment?.canHelp === "yes") return true;
  if (isLeadWorthyPrompt(question)) return true;
  return /email\s+[^\s]+@[^\s]+|email Yonatan|reach out|introductory call|30-minute|quote|budget range/i.test(answer);
}

export default function ChatSimulator() {
  const embeddedMode = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("embedded") === "1";
  const [isOpen, setIsOpen] = useState(embeddedMode);
  const [hasUnread, setHasUnread] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      sender: "bot",
      text: WELCOME_MESSAGE,
      timestamp: nowStamp()
    }
  ]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [lastAssessment, setLastAssessment] = useState<Message["helpAssessment"] | null>(null);
  const [showLeadForm, setShowLeadForm] = useState(false);
  const [leadDraft, setLeadDraft] = useState<LeadDraft>(EMPTY_LEAD);
  const [leadError, setLeadError] = useState("");
  const [leadCtaDismissed, setLeadCtaDismissed] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (messages.length > 1 || isLoading || showLeadForm) {
      messagesEndRef.current?.scrollIntoView({ behavior: "auto" });
    }
  }, [messages, isLoading, isOpen, showLeadForm]);

  useEffect(() => {
    if (isOpen) {
      setHasUnread(false);
      window.setTimeout(() => inputRef.current?.focus(), 180);
    }
  }, [isOpen]);

  const appendBot = (message: Message) => {
    setMessages((prev) => [...prev, message]);
    if (!isOpen) setHasUnread(true);
  };

  const beginLeadFlow = () => {
    setLeadDraft(EMPTY_LEAD);
    setLeadError("");
    setShowLeadForm(true);
    appendBot(botMessage("Sure — add the basics below so Yonatan can prepare a free 30-minute introductory call."));
  };

  const submitLead = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLeadError("");

    const draft = {
      name: leadDraft.name.trim(),
      email: leadDraft.email.trim(),
      need: leadDraft.need.trim(),
      timeline: leadDraft.timeline.trim()
    };

    if (draft.name.length < 2) {
      setLeadError("Please add your name.");
      return;
    }
    if (!isValidEmail(draft.email)) {
      setLeadError("Please add a valid email.");
      return;
    }
    if (draft.need.length < 8) {
      setLeadError("Please add a short note about what we should cover on the call.");
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch("/api/lead", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...draft, source: "portfolio-chat", website: "" })
      });
      const data = await response.json().catch(() => ({}));

      if (!response.ok && !data.mailtoUrl) {
        throw new Error(data.error || "Lead submission failed.");
      }

      if (data.mailtoUrl) {
        window.location.href = data.mailtoUrl;
      }

      setShowLeadForm(false);
      setLeadDraft(EMPTY_LEAD);
      setLeadCtaDismissed(true);
      appendBot(botMessage(data.message || "Thanks — Yonatan will use this to prepare a free 30-minute introductory call. If your email app opened, just hit send so he receives it.", {
        quickReplies: [{ label: "Request another call", value: "send another note" }]
      }));
    } catch (error: any) {
      setLeadError(error?.message || "I couldn’t submit that. Try again, or add a bit more detail about what we should cover.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLeadInput = async (cleanText: string): Promise<boolean> => {
    if (isNegativeLeadReply(cleanText)) {
      setLeadCtaDismissed(true);
      setShowLeadForm(false);
      appendBot(botMessage("No problem — you can keep asking questions here."));
      return true;
    }
    if (isPositiveLeadReply(cleanText) || /send another note/i.test(cleanText)) {
      beginLeadFlow();
      return true;
    }
    return false;
  };

  const sendMessage = async (textToSend: string) => {
    const cleanText = textToSend.trim();
    if (!cleanText || isLoading) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: cleanText.slice(0, 1200),
      timestamp: nowStamp()
    };

    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setInputText("");

    if (await handleLeadInput(cleanText)) return;

    setIsLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: nextMessages })
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.response || data.error || "Chat service unavailable.");
      }

      const helpAssessment = data.helpAssessment || data.assessment || null;
      const botMsg: Message = {
        id: `bot-${Date.now()}`,
        sender: "bot",
        text: data.response || "I can help route that. Share a few details below for a free 30-minute introductory call.",
        timestamp: nowStamp(),
        helpAssessment
      };

      const shouldOffer = !leadCtaDismissed && !showLeadForm && shouldOfferLeadCapture(cleanText, botMsg.text, helpAssessment);
      if (shouldOffer) {
        setLeadDraft(EMPTY_LEAD);
        setLeadError("");
        setShowLeadForm(true);
      }
      setMessages((prev) => [
        ...prev,
        botMsg,
        ...(shouldOffer ? [botMessage("Share a few details below and Yonatan will confirm a free 30-minute introductory call.")] : [])
      ]);
      setLastAssessment(helpAssessment);
      if (!isOpen) setHasUnread(true);
    } catch (error: any) {
      const fallback = error?.message || "The assistant is temporarily unavailable. Share a few details below if the form is open, or try again in a moment.";
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          sender: "bot",
          text: fallback,
          timestamp: nowStamp()
        }
      ]);
      setLastAssessment(null);
      if (!isOpen) setHasUnread(true);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: "welcome",
        sender: "bot",
        text: WELCOME_MESSAGE,
        timestamp: nowStamp()
      }
    ]);
    setLastAssessment(null);
    setShowLeadForm(false);
    setLeadDraft(EMPTY_LEAD);
    setLeadError("");
    setLeadCtaDismissed(false);
    setHasUnread(false);
  };

  const statusColor = lastAssessment?.canHelp === "yes"
    ? "border-[#9bbf7a]/45 bg-[#152012]/88 text-[#dceecb]"
    : "border-[#d3aa55]/45 bg-[#21180c]/90 text-[#f1dfb4]";

  const statusLabel = lastAssessment?.canHelp === "yes" ? "Strong fit" : "Share details for an intro call";
  const inputPlaceholder = "Describe the workflow or problem…";

  return (
    <div className={`${embeddedMode ? "flex min-h-screen items-end justify-end bg-transparent p-3" : "fixed bottom-4 right-4 z-[9999] sm:bottom-6 sm:right-6"} font-sans text-[#efe7d6]`} id="chatbot-simulator-container">
      <AnimatePresence>
        {isOpen && (
          <motion.section
            key="chat-panel"
            initial={{ opacity: 0, y: 20, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.96 }}
            transition={{ duration: 0.18, ease: "easeOut" }}
            className={`${embeddedMode ? "h-[calc(100vh-1.5rem)]" : "mb-4 h-[min(680px,calc(100vh-112px))]"} flex w-[calc(100vw-2rem)] max-w-[390px] flex-col overflow-hidden rounded-3xl border border-[#d3aa55]/28 bg-[#080b0a] shadow-[0_22px_80px_rgba(0,0,0,0.55)] ring-1 ring-[#d3aa55]/12 sm:w-[390px]`}
            aria-label="Yonatan Gemmi portfolio chat assistant"
          >
            <div className="border-b border-[#d3aa55]/18 bg-[#0d0f0d]/95 px-4 py-3 backdrop-blur">
              <div className="flex items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border border-[#d3aa55]/45 bg-[#d3aa55]/15 text-[#f1dfb4] shadow-[0_0_24px_rgba(211,170,85,0.18)]">
                    <Bot className="h-5 w-5" />
                  </div>
                  <div className="min-w-0">
                    <h1 className="flex items-center gap-2 truncate text-sm font-semibold tracking-tight text-[#fff7e8]">
                      AI Project Scout
                      <span className="inline-flex h-2 w-2 shrink-0 rounded-full bg-[#9bbf7a]" />
                    </h1>
                    <p className="truncate text-[11px] font-medium text-[#b8ab91]">Free 30-min intro call</p>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button onClick={clearChat} className="rounded-lg p-2 text-[#b8ab91] transition hover:bg-[#21180c] hover:text-[#f4c99a]" title="Clear chat" type="button">
                    <Trash2 className="h-4 w-4" />
                  </button>
                  <button onClick={() => setIsOpen(false)} className={`${embeddedMode ? "hidden" : ""} rounded-lg p-2 text-[#b8ab91] transition hover:bg-[#21180c] hover:text-[#fff7e8]`} title="Close chat" type="button">
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {lastAssessment && (
                <div className={`mt-3 rounded-2xl border px-3 py-2 text-xs ${statusColor}`}>
                  <div className="flex items-start gap-2">
                    {lastAssessment.canHelp === "yes" ? <CheckCircle className="mt-0.5 h-4 w-4 shrink-0" /> : <HelpCircle className="mt-0.5 h-4 w-4 shrink-0" />}
                    <div>
                      <p className="font-semibold uppercase tracking-wide">{statusLabel}</p>
                      <p className="mt-0.5 text-[#efe7d6]/90">{lastAssessment.reason}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="flex-1 space-y-4 overflow-y-auto bg-[radial-gradient(circle_at_top,rgba(211,170,85,0.12),transparent_34%),#080b0a] p-4">
              {messages.length === 1 && (
                <div className="grid gap-2">
                  {SUGGESTIONS.map((suggestion) => (
                    <button
                      key={suggestion}
                      type="button"
                      onClick={() => sendMessage(suggestion)}
                      className="rounded-2xl border border-[#d3aa55]/18 bg-[#17120b]/78 px-3 py-2 text-left text-[11px] leading-relaxed text-[#d8cdb8] transition hover:border-[#d3aa55]/60 hover:bg-[#21180c] hover:text-[#fff7e8]"
                    >
                      <Sparkles className="mb-1 h-3.5 w-3.5 text-[#d3aa55]" />
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}

              <AnimatePresence initial={false}>
                {messages.map((msg) => (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    className={`flex items-start gap-3 ${msg.sender === "user" ? "flex-row-reverse" : "flex-row"}`}
                  >
                    <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border ${msg.sender === "user" ? "border-[#d3aa55]/20 bg-[#17120b] text-[#d8cdb8]" : "border-[#d3aa55]/35 bg-[#21180c] text-[#d3aa55]"}`}>
                      {msg.sender === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                    </div>
                    <div className={`max-w-[82%] rounded-2xl border px-4 py-3 text-xs leading-relaxed ${msg.sender === "user" ? "rounded-tr-none border-[#d3aa55]/48 bg-[#d3aa55] text-[#121006]" : "rounded-tl-none border-[#d3aa55]/16 bg-[#17120b] text-[#efe7d6]"}`}>
                      <p className="whitespace-pre-wrap">{msg.text}</p>
                      {msg.quickReplies?.length ? (
                        <div className="mt-3 flex flex-wrap gap-2 border-t border-[#d3aa55]/16 pt-3">
                          {msg.quickReplies.map((reply) => (
                            <button
                              key={`${msg.id}-${reply.value}`}
                              type="button"
                              onClick={() => sendMessage(reply.value)}
                              className="rounded-full border border-[#d3aa55]/50 bg-[#d3aa55]/10 px-3 py-1.5 text-[10px] font-semibold text-[#f1dfb4] transition hover:border-[#f1dfb4] hover:bg-[#d3aa55]/22 disabled:cursor-not-allowed disabled:opacity-50"
                              disabled={isLoading}
                            >
                              {reply.label}
                            </button>
                          ))}
                        </div>
                      ) : null}
                      {msg.sender === "bot" && msg.helpAssessment?.matchedSkills?.length ? (
                        <div className="mt-3 flex flex-wrap gap-1 border-t border-[#d3aa55]/16 pt-2">
                          {msg.helpAssessment.matchedSkills.slice(0, 5).map((skill) => (
                            <span key={skill} className="rounded-full border border-[#9bbf7a]/45 bg-[#152012]/70 px-2 py-0.5 text-[10px] text-[#dceecb]">{skill}</span>
                          ))}
                        </div>
                      ) : null}
                      <p className="mt-1 text-[9px] uppercase tracking-wide text-[#fff7e8]0">{msg.timestamp}</p>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>


              {showLeadForm && (
                <form onSubmit={submitLead} className="rounded-2xl border border-[#d3aa55]/28 bg-[#0d0f0d]/95 p-3 shadow-lg">
                  <div className="mb-3 flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-[#fff7e8]">Request a free intro call</p>
                      <p className="mt-1 text-[11px] text-[#b8ab91]">Share a few details so Yonatan can prepare for a 30-minute conversation.</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => { setShowLeadForm(false); setLeadError(""); setLeadCtaDismissed(true); }}
                      className="rounded-lg px-2 py-1 text-xs text-[#b8ab91] transition hover:bg-[#21180c] hover:text-[#fff7e8]"
                    >
                      Cancel
                    </button>
                  </div>
                  <div className="grid gap-2">
                    <input
                      value={leadDraft.name}
                      onChange={(event) => setLeadDraft((draft) => ({ ...draft, name: event.target.value }))}
                      maxLength={120}
                      placeholder="Name"
                      className="rounded-xl border border-[#d3aa55]/18 bg-[#17120b] px-3 py-2 text-sm text-[#fff7e8] outline-none transition placeholder:text-[#8f8168] focus:border-[#d3aa55]"
                    />
                    <input
                      value={leadDraft.email}
                      onChange={(event) => setLeadDraft((draft) => ({ ...draft, email: event.target.value }))}
                      maxLength={160}
                      placeholder="Email"
                      type="email"
                      className="rounded-xl border border-[#d3aa55]/18 bg-[#17120b] px-3 py-2 text-sm text-[#fff7e8] outline-none transition placeholder:text-[#8f8168] focus:border-[#d3aa55]"
                    />
                    <textarea
                      value={leadDraft.need}
                      onChange={(event) => setLeadDraft((draft) => ({ ...draft, need: event.target.value }))}
                      maxLength={900}
                      placeholder="What should we cover on the call?"
                      rows={3}
                      className="resize-none rounded-xl border border-[#d3aa55]/18 bg-[#17120b] px-3 py-2 text-sm text-[#fff7e8] outline-none transition placeholder:text-[#8f8168] focus:border-[#d3aa55]"
                    />
                    <input
                      value={leadDraft.timeline}
                      onChange={(event) => setLeadDraft((draft) => ({ ...draft, timeline: event.target.value }))}
                      maxLength={240}
                      placeholder="Times that work for a 30-min call (optional)"
                      className="rounded-xl border border-[#d3aa55]/18 bg-[#17120b] px-3 py-2 text-sm text-[#fff7e8] outline-none transition placeholder:text-[#8f8168] focus:border-[#d3aa55]"
                    />
                  </div>
                  {leadError && <p className="mt-2 text-[11px] text-rose-300">{leadError}</p>}
                  <button
                    disabled={isLoading}
                    className="mt-3 inline-flex w-full items-center justify-center rounded-xl bg-[#d3aa55] px-4 py-2.5 text-sm font-semibold text-[#121006] transition hover:bg-[#e1bd6f] disabled:cursor-not-allowed disabled:opacity-50"
                    type="submit"
                  >
                    {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                    Request intro call
                  </button>
                </form>
              )}

              {isLoading && (
                <div className="flex items-center gap-3 text-xs text-[#b8ab91]">
                  <Loader2 className="h-4 w-4 animate-spin text-[#d3aa55]" />
                  {showLeadForm ? "Sending your request…" : "Thinking through project fit…"}
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <form onSubmit={(event) => { event.preventDefault(); sendMessage(inputText); }} className="border-t border-[#d3aa55]/16 bg-[#0d0f0d] p-3">
              <div className="flex gap-2">
                <input
                  ref={inputRef}
                  value={inputText}
                  onChange={(event) => setInputText(event.target.value)}
                  maxLength={1200}
                  placeholder={inputPlaceholder}
                  className="min-w-0 flex-1 rounded-2xl border border-[#d3aa55]/18 bg-[#17120b] px-3 py-3 text-sm text-[#fff7e8] outline-none transition placeholder:text-[#8f8168] focus:border-[#d3aa55]"
                />
                <button disabled={isLoading || !inputText.trim()} className="inline-flex items-center justify-center rounded-2xl bg-[#d3aa55] px-4 py-3 text-[#121006] transition hover:bg-[#e1bd6f] disabled:cursor-not-allowed disabled:opacity-50" type="submit" aria-label="Send message">
                  {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                </button>
              </div>
              <p className="mt-2 text-[10px] text-[#fff7e8]0">Share a few details here for a free 30-minute intro call.</p>
            </form>
          </motion.section>
        )}
      </AnimatePresence>

      {!embeddedMode && (
        <button
          type="button"
          onClick={() => setIsOpen((value) => !value)}
          className="group relative ml-auto flex h-16 items-center gap-3 rounded-full border border-[#d3aa55]/36 bg-[#080b0a] px-4 pr-5 text-left shadow-[0_18px_60px_rgba(0,0,0,0.45)] ring-1 ring-[#d3aa55]/12 transition hover:-translate-y-0.5 hover:border-[#d3aa55]/65 hover:bg-[#17120b]"
          aria-expanded={isOpen}
          aria-controls="chatbot-simulator-container"
        >
          <span className="flex h-11 w-11 items-center justify-center rounded-full bg-[#d3aa55] text-[#121006] shadow-[0_0_30px_rgba(211,170,85,0.32)]">
            {isOpen ? <X className="h-5 w-5" /> : <MessageCircle className="h-5 w-5" />}
          </span>
          <span className="hidden sm:block">
            <span className="block text-sm font-semibold text-[#fff7e8]">AI Project Scout</span>
            <span className="block text-[11px] text-[#b8ab91]">Free 30-min intro call</span>
          </span>
          {hasUnread && <span className="absolute right-2 top-2 h-3 w-3 rounded-full border-2 border-[#080b0a] bg-[#9bbf7a]" />}
        </button>
      )}
    </div>
  );
}
