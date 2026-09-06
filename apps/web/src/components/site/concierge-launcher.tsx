"use client";

import { useState } from "react";

import { ApiError, publicApiPost } from "@/lib/api";
import { getStoredLeadId } from "@/lib/tracking";
import type { ConciergeMessageResult } from "@/lib/types";

interface ChatMessage {
  role: "patient" | "ai";
  content: string;
}

// Requires an existing lead (set by appointment-form.tsx on a successful
// enquiry submission) — Conversation.lead_id is required in the data
// model, and the concierge follows up on an enquiry rather than
// cold-opening with a fully anonymous visitor (CLAUDE.md §4's flow has
// "Lead Created" before "AI Concierge" contact).
export function ConciergeLauncher({ clinicName }: { clinicName: string }) {
  const [open, setOpen] = useState(false);
  const [leadId, setLeadId] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleOpen() {
    setLeadId(getStoredLeadId());
    setOpen(true);
  }

  async function handleSend(event: React.FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || !leadId) return;

    setMessages((prev) => [...prev, { role: "patient", content: text }]);
    setInput("");
    setSending(true);
    setError(null);

    try {
      const result = await publicApiPost<ConciergeMessageResult>("/concierge/messages", {
        lead_id: leadId,
        message: text,
        conversation_id: conversationId,
      });
      setConversationId(result.conversation_id);
      setMessages((prev) => [...prev, { role: "ai", content: result.reply }]);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Couldn't reach the concierge — please try WhatsApp instead."
      );
    } finally {
      setSending(false);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={handleOpen}
        aria-label="Open AI concierge"
        className="fixed bottom-6 right-24 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-gold text-ivory shadow-lg transition-transform hover:scale-105"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          className="h-6 w-6"
          stroke="currentColor"
          strokeWidth={1.8}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 3c-4.97 0-9 3.5-9 7.8 0 2.3 1.13 4.36 2.94 5.79-.1.98-.46 2.17-1.24 3.36 1.62-.2 3.02-.8 4.1-1.55A10.5 10.5 0 0 0 12 18.6c4.97 0 9-3.5 9-7.8S16.97 3 12 3Z"
          />
        </svg>
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-end justify-end bg-charcoal/30 sm:items-center sm:p-6">
          <div className="flex h-full w-full flex-col bg-ivory shadow-2xl sm:h-[min(640px,90vh)] sm:max-w-sm sm:rounded-2xl">
            <div className="flex items-center justify-between border-b border-ivory-soft bg-emerald px-5 py-4 sm:rounded-t-2xl">
              <div>
                <p className="text-sm font-semibold text-ivory">{clinicName} AI Concierge</p>
                <p className="text-xs text-ivory/70">
                  {leadId ? "Usually replies in seconds" : "Enquiry required"}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Close"
                className="text-ivory/80 hover:text-ivory"
              >
                ✕
              </button>
            </div>

            {leadId ? (
              <>
                <div className="flex flex-1 flex-col gap-3 overflow-y-auto px-5 py-5">
                  {messages.length === 0 && (
                    <div className="max-w-[85%] rounded-2xl rounded-tl-sm bg-white px-4 py-3 text-sm text-charcoal-soft">
                      Hi! Ask me about treatments, pricing, doctors, or booking — I&apos;ll answer
                      from what the clinic has approved, and loop in the team for anything else.
                    </div>
                  )}
                  {messages.map((m, i) => (
                    <div
                      key={i}
                      className={
                        m.role === "patient"
                          ? "max-w-[85%] self-end rounded-2xl rounded-tr-sm bg-charcoal px-4 py-3 text-sm text-ivory"
                          : "max-w-[85%] rounded-2xl rounded-tl-sm bg-white px-4 py-3 text-sm text-charcoal-soft"
                      }
                    >
                      {m.content}
                    </div>
                  ))}
                  {sending && (
                    <div className="max-w-[85%] rounded-2xl rounded-tl-sm bg-white px-4 py-3 text-sm text-charcoal-soft/60">
                      Typing…
                    </div>
                  )}
                  {error && <p className="text-xs text-red-600">{error}</p>}
                </div>
                <form
                  onSubmit={handleSend}
                  className="flex items-center gap-2 border-t border-ivory-soft p-4"
                >
                  <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Type a message…"
                    disabled={sending}
                    className="flex-1 rounded-full border border-ivory-soft bg-white px-4 py-2.5 text-sm text-charcoal focus:border-gold focus:outline-none disabled:opacity-60"
                  />
                  <button
                    type="submit"
                    disabled={sending || !input.trim()}
                    className="rounded-full bg-charcoal px-4 py-2.5 text-sm font-medium text-ivory disabled:opacity-50"
                  >
                    Send
                  </button>
                </form>
              </>
            ) : (
              <div className="flex flex-1 flex-col items-center justify-center gap-3 px-6 text-center">
                <p className="text-sm text-charcoal-soft">
                  Submit an enquiry below first — the concierge picks up right where your
                  enquiry leaves off, so it always knows who it&apos;s talking to.
                </p>
                <a
                  href="#book"
                  onClick={() => setOpen(false)}
                  className="rounded-full bg-charcoal px-5 py-2.5 text-sm font-medium text-ivory"
                >
                  Go to the enquiry form
                </a>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
