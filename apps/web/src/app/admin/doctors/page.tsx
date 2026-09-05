import { apiFetch } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import type { Doctor } from "@/lib/types";

export default async function DoctorsPage() {
  const { accessToken } = await requireSession();
  const doctors = await apiFetch<Doctor[]>("/doctors", accessToken);

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold text-black dark:text-zinc-50">Doctors</h1>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {doctors.map((doctor) => (
          <div
            key={doctor.id}
            className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950"
          >
            <h2 className="font-medium text-black dark:text-zinc-50">{doctor.name}</h2>
            <p className="text-sm text-zinc-500">{doctor.title}</p>
            {doctor.specialties && (
              <p className="mt-2 text-xs text-zinc-500">{doctor.specialties.join(", ")}</p>
            )}
            {doctor.bio && <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-400">{doctor.bio}</p>}
          </div>
        ))}
      </div>
      {doctors.length === 0 && <p className="text-sm text-zinc-500">No doctors yet.</p>}
    </div>
  );
}
