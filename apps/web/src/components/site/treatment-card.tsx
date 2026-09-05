import Link from "next/link";

import type { PublicTreatment } from "@/lib/types";

export function TreatmentCard({ treatment }: { treatment: PublicTreatment }) {
  return (
    <Link
      href={`/treatments/${treatment.slug}`}
      className="group flex flex-col justify-between rounded-2xl border border-ivory-soft bg-white p-6 transition-colors hover:border-gold"
    >
      <div>
        {treatment.category && (
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-gold-dark">
            {treatment.category}
          </p>
        )}
        <h3 className="mt-2 font-serif text-xl text-charcoal">{treatment.name}</h3>
        {treatment.description && (
          <p className="mt-2 line-clamp-3 text-sm text-charcoal-soft">
            {treatment.description}
          </p>
        )}
      </div>
      <div className="mt-6 flex items-center justify-between text-sm">
        <span className="text-charcoal-soft">{treatment.duration}</span>
        <span className="font-medium text-gold-dark group-hover:underline">
          Learn more &rarr;
        </span>
      </div>
    </Link>
  );
}
