import Link from "next/link";

import { StatCard } from "@/components/stat-card";
import { StatusBadge } from "@/components/status-badge";
import { requireSession } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import type { DashboardStats, LeadPage } from "@/lib/types";

export default async function DashboardPage() {
  const { accessToken } = await requireSession();

  const [stats, recentLeads] = await Promise.all([
    apiFetch<DashboardStats>("/analytics/dashboard", accessToken),
    apiFetch<LeadPage>("/leads?limit=5", accessToken),
  ]);

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold text-black dark:text-zinc-50">Dashboard</h1>
        <p className="mt-1 text-sm text-zinc-500">Cosmo Dental Dubai (demo clinic)</p>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Total leads" value={stats.total_leads} />
        <StatCard label="Qualified" value={stats.leads_by_status["QUALIFIED"] ?? 0} />
        <StatCard label="Booked" value={stats.leads_by_status["BOOKED"] ?? 0} />
        <StatCard label="Upcoming appointments" value={stats.upcoming_appointments} />
      </div>

      <div className="rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
        <div className="flex items-center justify-between border-b border-zinc-200 px-5 py-3 dark:border-zinc-800">
          <h2 className="text-sm font-medium text-black dark:text-zinc-50">Recent leads</h2>
          <Link href="/admin/leads" className="text-sm text-zinc-500 hover:underline">
            View all
          </Link>
        </div>
        <ul className="divide-y divide-zinc-200 dark:divide-zinc-800">
          {recentLeads.items.map((lead) => (
            <li key={lead.id}>
              <Link
                href={`/admin/leads/${lead.id}`}
                className="flex items-center justify-between px-5 py-3 hover:bg-zinc-50 dark:hover:bg-zinc-900"
              >
                <div>
                  <p className="text-sm font-medium text-black dark:text-zinc-50">{lead.name}</p>
                  <p className="text-xs text-zinc-500">{lead.source ?? "unknown source"}</p>
                </div>
                <StatusBadge status={lead.status} />
              </Link>
            </li>
          ))}
          {recentLeads.items.length === 0 && (
            <li className="px-5 py-6 text-sm text-zinc-500">No leads yet.</li>
          )}
        </ul>
      </div>
    </div>
  );
}
