import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center bg-zinc-50 px-6 text-center dark:bg-black">
      <h1 className="text-3xl font-semibold tracking-tight text-black dark:text-zinc-50">
        CosmoPilot
      </h1>
      <p className="mt-3 max-w-md text-zinc-600 dark:text-zinc-400">
        AI Patient Acquisition &amp; Appointment Automation. The premium
        clinic website, enquiry flow, and AI concierge land in later phases —
        this is the Phase 1 foundation.
      </p>
      <Link
        href="/health"
        className="mt-6 rounded-full bg-foreground px-5 py-2.5 text-sm font-medium text-background transition-colors hover:bg-[#383838] dark:hover:bg-[#ccc]"
      >
        View system health
      </Link>
    </div>
  );
}
