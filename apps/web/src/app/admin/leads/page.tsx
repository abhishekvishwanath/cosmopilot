import Link from "next/link";

import { StatusBadge } from "@/components/status-badge";
import { apiFetch } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import { LEAD_STATUSES, type LeadPage } from "@/lib/types";

export default async function LeadsPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string }>;
}) {
  const { accessToken } = await requireSession();
  const { status } = await searchParams;

  const query = status ? `?status=${encodeURIComponent(status)}&limit=100` : "?limit=100";
  const page = await apiFetch<LeadPage>(`/leads${query}`, accessToken);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-black dark:text-zinc-50">Leads</h1>
      </div>

      <div className="flex flex-wrap gap-2">
        <Link
          href="/admin/leads"
          className={`rounded-full px-3 py-1 text-xs font-medium ${
            !status
              ? "bg-foreground text-background"
              : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-900 dark:text-zinc-400"
          }`}
        >
          All
        </Link>
        {LEAD_STATUSES.map((s) => (
          <Link
            key={s}
            href={`/admin/leads?status=${s}`}
            className={`rounded-full px-3 py-1 text-xs font-medium ${
              status === s
                ? "bg-foreground text-background"
                : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-900 dark:text-zinc-400"
            }`}
          >
            {s}
          </Link>
        ))}
      </div>

      <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-200 text-left text-zinc-500 dark:border-zinc-800">
              <th className="px-5 py-3 font-medium">Name</th>
              <th className="px-5 py-3 font-medium">Contact</th>
              <th className="px-5 py-3 font-medium">Source</th>
              <th className="px-5 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
            {page.items.map((lead) => (
              <tr key={lead.id} className="hover:bg-zinc-50 dark:hover:bg-zinc-900">
                <td className="px-5 py-3">
                  <Link href={`/admin/leads/${lead.id}`} className="font-medium hover:underline">
                    {lead.name}
                  </Link>
                </td>
                <td className="px-5 py-3 text-zinc-500">{lead.email ?? lead.phone ?? "—"}</td>
                <td className="px-5 py-3 text-zinc-500">{lead.source ?? "—"}</td>
                <td className="px-5 py-3">
                  <StatusBadge status={lead.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {page.items.length === 0 && (
          <p className="px-5 py-6 text-sm text-zinc-500">No leads match this filter.</p>
        )}
      </div>
    </div>
  );
}
