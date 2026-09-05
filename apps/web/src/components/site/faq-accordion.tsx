"use client";

import { useState } from "react";

export function FaqAccordion({ items }: { items: { q: string; a: string }[] }) {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <div className="divide-y divide-ivory-soft rounded-2xl border border-ivory-soft bg-white">
      {items.map((item, index) => {
        const isOpen = openIndex === index;
        return (
          <div key={item.q}>
            <button
              type="button"
              onClick={() => setOpenIndex(isOpen ? null : index)}
              className="flex w-full items-center justify-between gap-4 px-6 py-4 text-left"
              aria-expanded={isOpen}
            >
              <span className="font-medium text-charcoal">{item.q}</span>
              <span className="shrink-0 text-xl text-gold-dark">{isOpen ? "−" : "+"}</span>
            </button>
            {isOpen && <p className="px-6 pb-4 text-sm text-charcoal-soft">{item.a}</p>}
          </div>
        );
      })}
    </div>
  );
}
