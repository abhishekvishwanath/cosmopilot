const ANONYMOUS_ID_KEY = "cosmopilot_anonymous_id";

// A stable per-browser id so multiple visits/enquiries from the same
// visitor can be correlated later (visitor_sessions.anonymous_id) — not
// used for anything beyond attribution, and never sent anywhere but our
// own API.
export function getOrCreateAnonymousId(): string | null {
  if (typeof window === "undefined") return null;
  try {
    const existing = window.localStorage.getItem(ANONYMOUS_ID_KEY);
    if (existing) return existing;
    const generated = crypto.randomUUID();
    window.localStorage.setItem(ANONYMOUS_ID_KEY, generated);
    return generated;
  } catch {
    // Private browsing / storage blocked — attribution is best-effort.
    return null;
  }
}

const LEAD_ID_KEY = "cosmopilot_lead_id";

// Set once a visitor's enquiry form succeeds (see appointment-form.tsx) —
// the AI Concierge widget (concierge-launcher.tsx) reads this to decide
// whether it has a lead to attach the conversation to. Conversations are
// always tied to a lead (CLAUDE.md's data model — Conversation.lead_id is
// required), so the concierge follows up on an enquiry rather than
// cold-opening with a fully anonymous visitor.
export function setStoredLeadId(leadId: string): void {
  try {
    window.localStorage.setItem(LEAD_ID_KEY, leadId);
  } catch {
    // Private browsing / storage blocked — the concierge just won't
    // unlock this session; the form and WhatsApp still work.
  }
}

export function getStoredLeadId(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(LEAD_ID_KEY);
  } catch {
    return null;
  }
}


export interface Attribution {
  source: string | null;
  campaign: string | null;
}

function referrerHostname(): string | null {
  if (!document.referrer) return null;
  try {
    return new URL(document.referrer).hostname;
  } catch {
    return null;
  }
}

export function getAttribution(): Attribution {
  if (typeof window === "undefined") return { source: null, campaign: null };
  const params = new URLSearchParams(window.location.search);
  const source = params.get("utm_source") ?? referrerHostname();
  const campaign = params.get("utm_campaign");
  return { source, campaign };
}
