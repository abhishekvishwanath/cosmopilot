export function SectionHeading({
  eyebrow,
  title,
  description,
  align = "left",
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  align?: "left" | "center";
}) {
  return (
    <div className={align === "center" ? "text-center" : "text-left"}>
      {eyebrow && (
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-gold-dark">
          {eyebrow}
        </p>
      )}
      <h2
        className={`mt-2 font-serif text-3xl text-charcoal sm:text-4xl ${
          align === "center" ? "mx-auto max-w-2xl" : ""
        }`}
      >
        {title}
      </h2>
      {description && (
        <p
          className={`mt-3 text-charcoal-soft ${
            align === "center" ? "mx-auto max-w-2xl" : "max-w-2xl"
          }`}
        >
          {description}
        </p>
      )}
    </div>
  );
}
