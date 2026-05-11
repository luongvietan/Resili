import { cn } from "@/lib/utils";

interface PricingFeature {
  text: string;
  included: boolean;
}

interface PricingTierProps {
  name: string;
  price: string;
  pricePeriod?: string;
  description: string;
  features: PricingFeature[];
  ctaLabel: string;
  ctaHref?: string;
  featured?: boolean;
  badge?: string;
}

export function PricingTier({
  name,
  price,
  pricePeriod = "/mo",
  description,
  features,
  ctaLabel,
  ctaHref = "#",
  featured = false,
  badge,
}: PricingTierProps) {
  return (
    <div
      className={cn(
        "relative border border-hairline-strong rounded-lg p-8 flex flex-col gap-6",
        featured ? "bg-surface-elevated" : "bg-surface-card"
      )}
    >
      {badge && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <span className="bg-accent-orange text-canvas text-caption font-medium px-3 py-0.5 rounded-full">
            {badge}
          </span>
        </div>
      )}

      {/* Header */}
      <div>
        <p className="text-charcoal text-body-sm font-medium uppercase tracking-[0.08em] mb-2">
          {name}
        </p>
        <div className="flex items-end gap-1 mb-2">
          <span className="text-display-lg font-display text-ink leading-none">
            {price}
          </span>
          {pricePeriod && (
            <span className="text-charcoal text-body-sm mb-1">{pricePeriod}</span>
          )}
        </div>
        <p className="text-charcoal text-body-sm">{description}</p>
      </div>

      {/* Features */}
      <ul className="flex flex-col gap-3 flex-1">
        {features.map((feature, i) => (
          <li key={i} className="flex items-start gap-2">
            {feature.included ? (
              <span className="text-accent-green text-body-sm mt-0.5 shrink-0">✓</span>
            ) : (
              <span className="text-mute text-body-sm mt-0.5 shrink-0">—</span>
            )}
            <span
              className={cn(
                "text-body-sm",
                feature.included ? "text-body" : "text-mute"
              )}
            >
              {feature.text}
            </span>
          </li>
        ))}
      </ul>

      {/* CTA */}
      <a
        href={ctaHref}
        className={cn(
          "block text-center rounded-md h-10 leading-10 text-body-sm font-medium transition-colors",
          featured
            ? "bg-ink text-canvas hover:bg-[#f1f7fe]"
            : "border border-hairline-strong text-ink hover:bg-surface-elevated"
        )}
      >
        {ctaLabel}
      </a>
    </div>
  );
}
