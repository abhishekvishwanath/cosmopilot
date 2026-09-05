"use client";

import { useState } from "react";

// UI shell only — the AI Patient Concierge itself (RAG + tool calling +
// booking) lands in Phase 6 (CLAUDE.md §10). This intentionally does not
// pretend to converse; it tells the visitor what's coming and routes them
// to the form/WhatsApp, which already work.
export function ConciergeLauncher({ clinicName }: { clinicName: string }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label="Open AI concierge"
        className="fixed bottom-6 right-24 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-gold text-ivory shadow-lg transition-transform hover:scale-105"
      >
        <svg viewBox="0 0 24 24" fill="none" className="h-6 w-6" stroke="currentColor" strokeWidth={1.8}>
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
                <p className="text-xs text-ivory/70">Coming soon</p>
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
            <div className="flex flex-1 flex-col gap-3 overflow-y-auto px-5 py-5">
              <div className="max-w-[85%] rounded-2xl rounded-tl-sm bg-white px-4 py-3 text-sm text-charcoal-soft">
                Hi! I&apos;ll soon be able to answer questions about treatments, pricing, and
                availability, and help you book a consultation right here.
              </div>
              <div className="max-w-[85%] rounded-2xl rounded-tl-sm bg-white px-4 py-3 text-sm text-charcoal-soft">
                For now, please use the enquiry form on this page or message us on WhatsApp —
                a member of the team will get back to you.
              </div>
            </div>
            <div className="border-t border-ivory-soft p-4">
              <div className="flex items-center gap-2 rounded-full border border-ivory-soft bg-white px-4 py-2.5 text-sm text-charcoal-soft/60">
                <span>Chat isn&apos;t connected yet</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
