const BADGES = [
  { label: "Premium Dubai clinic", detail: "Sheikh Zayed Road" },
  { label: "Specialist-led team", detail: "Cosmetic, ortho & implant specialists" },
  { label: "Rapid follow-up", detail: "New enquiries contacted in minutes" },
  { label: "Transparent pricing", detail: "Guidance shared before you commit" },
];

export function TrustBadges() {
  return (
    <dl className="grid grid-cols-2 gap-6 sm:grid-cols-4">
      {BADGES.map((badge) => (
        <div key={badge.label} className="border-t-2 border-gold pt-3">
          <dt className="text-sm font-medium text-charcoal">{badge.label}</dt>
          <dd className="mt-1 text-xs text-charcoal-soft">{badge.detail}</dd>
        </div>
      ))}
    </dl>
  );
}
