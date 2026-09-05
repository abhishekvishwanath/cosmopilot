"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { createClient } from "@/lib/supabase/client";
import type { KnowledgeAnswer, KnowledgeDocument } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function authedFetch(path: string, init?: RequestInit) {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session) throw new Error("Session expired — refresh the page.");

  const response = await fetch(`${API_URL}/api/v1${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${session.access_token}`,
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.error?.message ?? `Request failed with ${response.status}.`);
  }
  return response.json();
}

export function KnowledgeConsole({ initialDocuments }: { initialDocuments: KnowledgeDocument[] }) {
  const router = useRouter();
  const [documents, setDocuments] = useState(initialDocuments);
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  const [docTitle, setDocTitle] = useState("");
  const [docType, setDocType] = useState("policy");
  const [docText, setDocText] = useState("");
  const [ingesting, setIngesting] = useState(false);
  const [ingestError, setIngestError] = useState<string | null>(null);

  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [askError, setAskError] = useState<string | null>(null);
  const [answer, setAnswer] = useState<KnowledgeAnswer | null>(null);

  async function handleSync() {
    setSyncing(true);
    setSyncMessage(null);
    try {
      const result = await authedFetch("/knowledge/sync", { method: "POST" });
      setSyncMessage(`Synced ${result.chunks_created} chunks from clinic data.`);
      router.refresh();
    } catch (err) {
      setSyncMessage(err instanceof Error ? err.message : "Sync failed.");
    } finally {
      setSyncing(false);
    }
  }

  async function handleIngest(event: React.FormEvent) {
    event.preventDefault();
    setIngesting(true);
    setIngestError(null);
    try {
      await authedFetch("/knowledge/documents", {
        method: "POST",
        body: JSON.stringify({ title: docTitle, type: docType, text: docText }),
      });
      const refreshed: KnowledgeDocument[] = await authedFetch("/knowledge/documents");
      setDocuments(refreshed);
      setDocTitle("");
      setDocText("");
    } catch (err) {
      setIngestError(err instanceof Error ? err.message : "Ingestion failed.");
    } finally {
      setIngesting(false);
    }
  }

  async function handleAsk(event: React.FormEvent) {
    event.preventDefault();
    setAsking(true);
    setAskError(null);
    setAnswer(null);
    try {
      const result: KnowledgeAnswer = await authedFetch("/knowledge/ask", {
        method: "POST",
        body: JSON.stringify({ question }),
      });
      setAnswer(result);
    } catch (err) {
      setAskError(err instanceof Error ? err.message : "Request failed.");
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-black dark:text-zinc-50">
            Sync from clinic data
          </h2>
          <button
            type="button"
            onClick={handleSync}
            disabled={syncing}
            className="rounded-full bg-foreground px-4 py-1.5 text-xs font-medium text-background disabled:opacity-50"
          >
            {syncing ? "Syncing…" : "Sync now"}
          </button>
        </div>
        <p className="mt-1 text-xs text-zinc-500">
          Re-embeds clinic info, locations, doctors, and treatments (incl. FAQs) into the
          knowledge base. Run this after editing any of that content.
        </p>
        {syncMessage && <p className="mt-2 text-xs text-zinc-600 dark:text-zinc-400">{syncMessage}</p>}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
          <h2 className="text-sm font-medium text-black dark:text-zinc-50">Upload a document</h2>
          <form onSubmit={handleIngest} className="mt-3 flex flex-col gap-3">
            <input
              value={docTitle}
              onChange={(e) => setDocTitle(e.target.value)}
              placeholder="Title (e.g. Booking Policies)"
              required
              className="rounded-lg border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
            />
            <select
              value={docType}
              onChange={(e) => setDocType(e.target.value)}
              className="rounded-lg border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
            >
              <option value="policy">Policy</option>
              <option value="faq">FAQ</option>
              <option value="general">General</option>
            </select>
            <textarea
              value={docText}
              onChange={(e) => setDocText(e.target.value)}
              placeholder="Paste approved text content here..."
              required
              rows={6}
              className="rounded-lg border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
            />
            <button
              type="submit"
              disabled={ingesting}
              className="self-start rounded-full bg-foreground px-4 py-1.5 text-xs font-medium text-background disabled:opacity-50"
            >
              {ingesting ? "Uploading…" : "Upload & embed"}
            </button>
            {ingestError && <p className="text-xs text-red-600 dark:text-red-400">{ingestError}</p>}
          </form>

          <h3 className="mt-6 text-xs font-medium text-zinc-500">Documents</h3>
          <ul className="mt-2 space-y-2">
            {documents.map((doc) => (
              <li key={doc.id} className="flex items-center justify-between text-sm">
                <span className="text-black dark:text-zinc-50">{doc.title}</span>
                <span className="text-xs text-zinc-500">{doc.embedding_status}</span>
              </li>
            ))}
            {documents.length === 0 && (
              <li className="text-sm text-zinc-500">No documents uploaded yet.</li>
            )}
          </ul>
        </div>

        <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
          <h2 className="text-sm font-medium text-black dark:text-zinc-50">
            Test the approved-answer system
          </h2>
          <p className="mt-1 text-xs text-zinc-500">
            Ask anything a patient might ask — this is exactly what checks hallucination
            boundaries before the AI Concierge (Phase 6) uses it live.
          </p>
          <form onSubmit={handleAsk} className="mt-3 flex gap-2">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. How much do veneers cost?"
              required
              className="flex-1 rounded-lg border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
            />
            <button
              type="submit"
              disabled={asking}
              className="rounded-full bg-foreground px-4 py-2 text-xs font-medium text-background disabled:opacity-50"
            >
              {asking ? "Asking…" : "Ask"}
            </button>
          </form>
          {askError && <p className="mt-2 text-xs text-red-600 dark:text-red-400">{askError}</p>}

          {answer && (
            <div className="mt-4 rounded-lg border border-zinc-200 p-3 dark:border-zinc-800">
              <div className="flex gap-2 text-xs">
                <span
                  className={`rounded-full px-2 py-0.5 ${
                    answer.grounded
                      ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300"
                      : "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300"
                  }`}
                >
                  {answer.grounded ? "Grounded" : "Escalated — no match"}
                </span>
                <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-zinc-600 dark:bg-zinc-900 dark:text-zinc-400">
                  {answer.generated ? "LLM-generated" : "Raw context (LLM unavailable)"}
                </span>
              </div>
              <p className="mt-2 text-sm text-black dark:text-zinc-50">{answer.answer}</p>
              {answer.sources.length > 0 && (
                <div className="mt-3 space-y-1">
                  <p className="text-xs font-medium text-zinc-500">Sources</p>
                  {answer.sources.map((s, i) => (
                    <p key={i} className="text-xs text-zinc-500">
                      [{s.source_type}] {s.title} — similarity {s.similarity.toFixed(2)}
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
