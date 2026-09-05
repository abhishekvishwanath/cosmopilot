import Link from "next/link";
import { notFound } from "next/navigation";

import { LeadStatusControl } from "@/components/lead-status-control";
import { StatusBadge } from "@/components/status-badge";
import { apiFetch, ApiError } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import type { Appointment, Lead, TimelineEvent } from "@/lib/types";

export default async function LeadDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { accessToken } = await requireSession();
  const { id } = await params;

  let lead: Lead;
  try {
    lead = await apiFetch<Lead>(`/leads/${id}`, accessToken);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  const [timeline, appointments] = await Promise.all([
    apiFetch<TimelineEvent[]>(`/leads/${id}/timeline`, accessToken),
    apiFetch<Appointment[]>(`/appointments?lead_id=${id}`, accessToken),
  ]);

  return (
    <div className="flex flex-col gap-8">
      <div>
        <Link href="/admin/leads" className="text-sm text-zinc-500 hover:underline">
          ← Leads
        </Link>
        <div className="mt-2 flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-black dark:text-zinc-50">{lead.name}</h1>
          <LeadStatusControl leadId={lead.id} currentStatus={lead.status} />
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
          <h2 className="text-sm font-medium text-black dark:text-zinc-50">Contact</h2>
          <dl className="mt-3 space-y-2 text-sm">
            <Row label="Email" value={lead.email} />
            <Row label="Phone" value={lead.phone} />
            <Row label="WhatsApp" value={lead.whatsapp} />
            <Row label="Source" value={lead.source} />
            <Row label="Landing page" value={lead.landing_page} />
            <Row label="Consent" value={lead.consent ? "Granted" : "Not granted"} />
          </dl>
        </div>

        <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
          <h2 className="text-sm font-medium text-black dark:text-zinc-50">Appointments</h2>
          <ul className="mt-3 space-y-3">
            {appointments.map((a) => (
              <li key={a.id} className="text-sm">
                <div className="flex items-center justify-between">
                  <span>{a.start ? new Date(a.start).toLocaleString() : "No time set"}</span>
                  <StatusBadge status={a.status} />
                </div>
                {a.location && <p className="text-xs text-zinc-500">{a.location}</p>}
              </li>
            ))}
            {appointments.length === 0 && (
              <li className="text-sm text-zinc-500">No appointments yet.</li>
            )}
          </ul>
        </div>

        <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950 lg:col-span-1">
          <h2 className="text-sm font-medium text-black dark:text-zinc-50">Timeline</h2>
          <ol className="mt-3 space-y-3">
            {timeline.map((event) => (
              <li key={event.id} className="text-sm">
                <p className="text-xs text-zinc-500">
                  {new Date(event.timestamp).toLocaleString()}
                </p>
                <p className="font-medium text-black dark:text-zinc-50">
                  {event.event_type.replaceAll("_", " ")}
                </p>
                {event.event_metadata && (
                  <p className="text-xs text-zinc-500">
                    {Object.entries(event.event_metadata)
                      .map(([k, v]) => `${k}: ${v}`)
                      .join(", ")}
                  </p>
                )}
              </li>
            ))}
            {timeline.length === 0 && (
              <li className="text-sm text-zinc-500">No activity yet.</li>
            )}
          </ol>
        </div>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-zinc-500">{label}</dt>
      <dd className="text-right text-black dark:text-zinc-50">{value ?? "—"}</dd>
    </div>
  );
}
