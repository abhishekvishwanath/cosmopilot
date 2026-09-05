import { apiFetch } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import type { Treatment } from "@/lib/types";

export default async function TreatmentsPage() {
  const { accessToken } = await requireSession();
  const treatments = await apiFetch<Treatment[]>("/treatments", accessToken);

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold text-black dark:text-zinc-50">Treatments</h1>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {treatments.map((treatment) => (
          <div
            key={treatment.id}
            className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950"
          >
            <div className="flex items-center justify-between">
              <h2 className="font-medium text-black dark:text-zinc-50">{treatment.name}</h2>
              {!treatment.booking_enabled && (
                <span className="text-xs text-zinc-400">Booking disabled</span>
              )}
            </div>
            <p className="text-sm text-zinc-500">{treatment.category}</p>
            {treatment.description && (
              <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
                {treatment.description}
              </p>
            )}
            <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-zinc-500">
              {treatment.price_guidance && <span>{treatment.price_guidance}</span>}
              {treatment.duration && <span>{treatment.duration}</span>}
            </div>
          </div>
        ))}
      </div>
      {treatments.length === 0 && <p className="text-sm text-zinc-500">No treatments yet.</p>}
    </div>
  );
}
