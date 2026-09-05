function getInitials(name: string): string {
  return name
    .replace(/^Dr\.?\s*/i, "")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

// Doctors don't have real photos yet (photo_url is null for the demo
// clinic) — an initials avatar is honest placeholder UI rather than a
// stock photo standing in for a fictional person.
export function AvatarInitials({ name, size = 64 }: { name: string; size?: number }) {
  return (
    <div
      className="flex shrink-0 items-center justify-center rounded-full bg-emerald text-ivory"
      style={{ width: size, height: size, fontSize: size * 0.36 }}
    >
      <span className="font-serif">{getInitials(name)}</span>
    </div>
  );
}
