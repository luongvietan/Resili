import { PricingTier } from "@/components/ui/PricingTier";

const tiers = [
  {
    name: "Free",
    price: "$0",
    pricePeriod: "/mo",
    description: "For exploring and prototyping.",
    ctaLabel: "Start for free",
    ctaHref: "/signup",
    features: [
      { text: "500 credits/month", included: true },
      { text: "Markdown + JSON output", included: true },
      { text: "10 req/min rate limit", included: true },
      { text: "Community support", included: true },
      { text: "JavaScript rendering", included: false },
      { text: "Priority queue", included: false },
      { text: "SLA guarantee", included: false },
    ],
  },
  {
    name: "Pro",
    price: "$29",
    pricePeriod: "/mo",
    description: "For production AI pipelines.",
    ctaLabel: "Start Pro trial",
    ctaHref: "/signup?plan=pro",
    featured: true,
    badge: "Most popular",
    features: [
      { text: "50,000 credits/month", included: true },
      { text: "Markdown + JSON output", included: true },
      { text: "120 req/min rate limit", included: true },
      { text: "Email support", included: true },
      { text: "JavaScript rendering", included: true },
      { text: "Priority queue", included: true },
      { text: "SLA guarantee", included: false },
    ],
  },
  {
    name: "Enterprise",
    price: "Custom",
    pricePeriod: "",
    description: "For high-volume, mission-critical workloads.",
    ctaLabel: "Contact sales",
    ctaHref: "/contact",
    features: [
      { text: "Unlimited credits", included: true },
      { text: "Markdown + JSON output", included: true },
      { text: "Custom rate limits", included: true },
      { text: "Dedicated support", included: true },
      { text: "JavaScript rendering", included: true },
      { text: "Priority queue", included: true },
      { text: "SLA guarantee", included: true },
    ],
  },
];

export function Pricing() {
  return (
    <section
      id="pricing"
      className="relative py-16 tablet:py-24 px-6 overflow-hidden"
      style={{
        background:
          "radial-gradient(ellipse 70% 500px at 50% 0px, rgba(255,89,0,0.22), transparent)",
      }}
    >
      <div className="mx-auto max-w-body">
        <div className="text-center mb-12">
          <p className="text-caption text-accent-orange uppercase tracking-[0.12em] font-medium mb-3">
            Pricing
          </p>
          <h2
            className="font-display text-ink leading-none tracking-[-0.48px] mb-4"
            style={{ fontSize: "clamp(32px, 4vw, 48px)" }}
          >
            Simple, transparent pricing
          </h2>
          <p className="text-body-lg text-charcoal max-w-xl mx-auto">
            Pay for what you use. Scale as your agents grow. No hidden fees.
          </p>
        </div>

        <div className="grid grid-cols-1 tablet:grid-cols-3 gap-6 items-start">
          {tiers.map((tier) => (
            <PricingTier key={tier.name} {...tier} />
          ))}
        </div>

        <p className="text-center text-body-sm text-mute mt-8">
          All plans include SSL encryption, GDPR compliance, and 99.9% uptime.
        </p>
      </div>
    </section>
  );
}
