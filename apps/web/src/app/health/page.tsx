"use client";

import { useEffect, useState } from "react";

type HealthState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ok"; liveness: unknown; readiness: unknown };

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function HealthPage() {
  const [state, setState] = useState<HealthState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;

    async function check() {
      try {
        const [liveness, readiness] = await Promise.all([
          fetch(`${API_URL}/api/v1/health`).then((r) => r.json()),
          fetch(`${API_URL}/api/v1/health/ready`).then((r) => r.json()),
        ]);
        if (!cancelled) {
          setState({ status: "ok", liveness, readiness });
        }
      } catch (err) {
        if (!cancelled) {
          setState({
            status: "error",
            message:
              err instanceof Error
                ? err.message
                : "Could not reach the API.",
          });
        }
      }
    }

    check();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex flex-1 flex-col items-center gap-6 bg-zinc-50 px-6 py-16 dark:bg-black">
      <h1 className="text-2xl font-semibold text-black dark:text-zinc-50">
        System health
      </h1>
      <p className="text-sm text-zinc-500">
        Frontend (apps/web) → API ({API_URL})
      </p>

      {state.status === "loading" && (
        <p className="text-zinc-600 dark:text-zinc-400">Checking…</p>
      )}

      {state.status === "error" && (
        <div className="max-w-lg rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
          <p className="font-medium">Could not reach the API.</p>
          <p className="mt-1">{state.message}</p>
          <p className="mt-2 text-red-700 dark:text-red-300">
            Is the FastAPI server running at {API_URL}? See apps/api/README.md.
          </p>
        </div>
      )}

      {state.status === "ok" && (
        <div className="grid w-full max-w-lg gap-4 sm:grid-cols-2">
          <HealthCard title="Liveness (/health)" data={state.liveness} />
          <HealthCard title="Readiness (/health/ready)" data={state.readiness} />
        </div>
      )}
    </div>
  );
}

function HealthCard({ title, data }: { title: string; data: unknown }) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
      <h2 className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
        {title}
      </h2>
      <pre className="mt-2 overflow-x-auto text-xs text-zinc-600 dark:text-zinc-400">
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
}
