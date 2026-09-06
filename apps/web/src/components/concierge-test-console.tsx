"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { createClient } from "@/lib/supabase/client";
import type { ConciergeMessageResult } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface ChatMessage {
  role: "patient" | "ai";
  content: string;
  toolCalls?: string[];
}

export function ConciergeTestConsole({ leadId }: { leadId: string }) {
  const router = useRouter();
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSend(event: React.FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text) return;

    setMessages((prev) => [...prev, { role: "patient", content: text }]);
    setInput("");
    setSending(true);
    setError(null);

    try {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) throw new Error("Session expired — refresh the page.");

      const response = await fetch(`${API_URL}/api/v1/leads/${leadId}/concierge/messages`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: text, conversation_id: conversationId }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.error?.message ?? `Request failed with ${response.status}.`);
      }
      const result: ConciergeMessageResult = await response.json();
      setConversationId(result.conversation_id);
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          content: result.reply,
          toolCalls: result.tool_calls.map((t) => t.name),
        },
      ]);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
      <h2 className="text-sm font-medium text-black dark:text-zinc-50">
        Test the AI concierge as this lead
      </h2>
      <p className="mt-1 text-xs text-zinc-500">
        Simulates the patient&apos;s side of the conversation — same orchestration the public
        widget uses. Use this to check hallucination boundaries and escalation behavior.
      </p>

      <div className="mt-3 flex max-h-80 flex-col gap-2 overflow-y-auto">
        {messages.map((m, i) => (
          <div key={i} className="text-sm">
            <span className="font-medium text-black dark:text-zinc-50">
              {m.role === "patient" ? "Patient: " : "AI: "}
            </span>
            <span className="text-zinc-600 dark:text-zinc-400">{m.content}</span>
            {m.toolCalls && m.toolCalls.length > 0 && (
              <span className="ml-2 text-xs text-zinc-400">
                [{m.toolCalls.join(", ")}]
              </span>
            )}
          </div>
        ))}
        {messages.length === 0 && (
          <p className="text-sm text-zinc-500">No messages yet — say hello below.</p>
        )}
      </div>

      <form onSubmit={handleSend} className="mt-3 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type as the patient…"
          disabled={sending}
          className="flex-1 rounded-lg border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="rounded-full bg-foreground px-4 py-2 text-xs font-medium text-background disabled:opacity-50"
        >
          {sending ? "Sending…" : "Send"}
        </button>
      </form>
      {error && <p className="mt-2 text-xs text-red-600 dark:text-red-400">{error}</p>}
    </div>
  );
}
