import Link from "next/link";

import { StatusBadge } from "@/components/status-badge";
import { apiFetch } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import type { Appointment, Doctor, Lead, Treatment } from "@/lib/types";

export default async function AppointmentsPage() {
  const { accessToken } = await requireSession();

  const [appointments, leadsPage, doctors, treatments] = await Promise.all([
    apiFetch<Appointment[]>("/appointments", accessToken),
    apiFetch<{ items: Lead[] }>("/leads?limit=200", accessToken),
    apiFetch<Doctor[]>("/doctors", accessToken),
    apiFetch<Treatment[]>("/treatments", accessToken),
  ]);

  const leadsById = new Map(leadsPage.items.map((l) => [l.id, l]));
  const doctorsById = new Map(doctors.map((d) => [d.id, d]));
  const treatmentsById = new Map(treatments.map((t) => [t.id, t]));

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold text-black dark:text-zinc-50">Appointments</h1>

      <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-200 text-left text-zinc-500 dark:border-zinc-800">
              <th className="px-5 py-3 font-medium">Patient</th>
              <th className="px-5 py-3 font-medium">Doctor</th>
              <th className="px-5 py-3 font-medium">Treatment</th>
              <th className="px-5 py-3 font-medium">When</th>
              <th className="px-5 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
            {appointments.map((appt) => (
              <tr key={appt.id} className="hover:bg-zinc-50 dark:hover:bg-zinc-900">
                <td className="px-5 py-3">
                  <Link
                    href={`/admin/leads/${appt.lead_id}`}
                    className="font-medium hover:underline"
                  >
                    {leadsById.get(appt.lead_id)?.name ?? "Unknown"}
                  </Link>
                </td>
                <td className="px-5 py-3 text-zinc-500">
                  {appt.doctor_id ? (doctorsById.get(appt.doctor_id)?.name ?? "—") : "—"}
                </td>
                <td className="px-5 py-3 text-zinc-500">
                  {appt.treatment_id
                    ? (treatmentsById.get(appt.treatment_id)?.name ?? "—")
                    : "—"}
                </td>
                <td className="px-5 py-3 text-zinc-500">
                  {appt.start ? new Date(appt.start).toLocaleString() : "Not set"}
                </td>
                <td className="px-5 py-3">
                  <StatusBadge status={appt.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {appointments.length === 0 && (
          <p className="px-5 py-6 text-sm text-zinc-500">No appointments yet.</p>
        )}
      </div>
    </div>
  );
}
