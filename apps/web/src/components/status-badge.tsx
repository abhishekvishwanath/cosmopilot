const COLORS: Record<string, string> = {
  NEW: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300",
  CONTACTING: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  CONTACTED: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  QUALIFIED: "bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300",
  APPOINTMENT_INTENT: "bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300",
  BOOKED: "bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300",
  booked: "bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300",
  CONFIRMED: "bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300",
  confirmed: "bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300",
  ATTENDED: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  completed: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  NO_ANSWER: "bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-300",
  WHATSAPP_FOLLOWUP: "bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-300",
  HUMAN_REQUIRED: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
  CANCELLED: "bg-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  cancelled: "bg-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  NO_SHOW: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
  no_show: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
  LOST: "bg-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  REACTIVATION: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300",
  pending: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
};

export function StatusBadge({ status }: { status: string }) {
  const color = COLORS[status] ?? "bg-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300";
  return (
    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${color}`}>
      {status}
    </span>
  );
}
