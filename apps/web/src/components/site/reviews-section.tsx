import type { DemoReview } from "@/lib/site-content";

function Stars({ rating }: { rating: number }) {
  return (
    <div className="text-gold" aria-label={`${rating} out of 5 stars`}>
      {"★".repeat(rating)}
      {"☆".repeat(5 - rating)}
    </div>
  );
}

export function ReviewsSection({ reviews }: { reviews: DemoReview[] }) {
  return (
    <div>
      <div className="grid gap-4 sm:grid-cols-3">
        {reviews.map((review) => (
          <figure
            key={review.id}
            className="flex flex-col justify-between rounded-2xl border border-ivory-soft bg-white p-6"
          >
            <div>
              <Stars rating={review.rating} />
              <blockquote className="mt-3 text-sm text-charcoal-soft">
                &ldquo;{review.quote}&rdquo;
              </blockquote>
            </div>
            <figcaption className="mt-4 text-xs font-medium text-charcoal">
              {review.name} <span className="text-charcoal-soft">— {review.treatment}</span>
            </figcaption>
          </figure>
        ))}
      </div>
      <p className="mt-4 text-xs text-charcoal-soft/70">
        Demo reviews — illustrative content for this prototype, not real patient feedback.
      </p>
    </div>
  );
}
