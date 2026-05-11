import { CodeWindow } from "@/components/ui/CodeWindow";

const fetcherResponseExample = `{
  "url": "https://example.com",
  "format": "markdown",
  "content": "# Example Domain\\n\\nThis domain is for use in illustrative examples...",
  "metadata": {
    "title": "Example Domain",
    "statusCode": 200,
    "contentType": "text/html",
    "fetchedAt": "2026-05-11T07:26:00Z"
  },
  "credits_used": 1
}`;

const features = [
  {
    icon: "⚡",
    title: "Lightning fast",
    description:
      "Sub-second response times with global edge caching. Your agents never wait for data.",
  },
  {
    icon: "🤖",
    title: "LLM-native formats",
    description:
      "Get clean Markdown, structured JSON, or raw HTML. No parsing boilerplate needed.",
  },
  {
    icon: "🛡️",
    title: "Anti-bot bypass",
    description:
      "Handles JavaScript rendering, CAPTCHAs, and bot detection automatically.",
  },
  {
    icon: "📊",
    title: "Usage transparency",
    description:
      "Credit-based billing with real-time dashboard. Know exactly what your agents consume.",
  },
];

const agentFeatures = [
  {
    title: "MCP-compatible",
    description:
      "Drop-in Model Context Protocol server. Works with Claude, GPT-4, and any MCP-supporting framework.",
  },
  {
    title: "OpenAPI + type-safe clients",
    description:
      "Auto-generated TypeScript SDK. Full type safety from API to your agent logic.",
  },
  {
    title: "Retry & circuit breaker",
    description:
      "Built-in resilience patterns. Your agents keep running even when targets go down.",
  },
];

export function Features() {
  return (
    <>
      {/* Feature Section 1: How it works */}
      <section
        id="features"
        className="relative py-16 tablet:py-24 px-6 overflow-hidden"
        style={{
          background:
            "radial-gradient(ellipse 70% 500px at 50% 0px, rgba(255,89,0,0.22), transparent)",
        }}
      >
        <div className="mx-auto max-w-body">
          <div className="text-center mb-12">
            <p className="text-caption text-accent-orange uppercase tracking-[0.12em] font-medium mb-3">
              How it works
            </p>
            <h2
              className="font-display text-ink leading-none tracking-[-0.48px] mb-4"
              style={{ fontSize: "clamp(32px, 4vw, 48px)" }}
            >
              One API call.
              <br />
              Clean data, every time.
            </h2>
            <p className="text-body-lg text-charcoal max-w-xl mx-auto">
              Send a URL, get back structured content. Resili handles rendering,
              extraction, and formatting — so your AI pipeline stays focused.
            </p>
          </div>

          <div className="flex flex-col tablet-lg:flex-row items-start gap-12">
            {/* Code response example */}
            <div className="flex-1 w-full">
              <CodeWindow
                tabs={[{ label: "Response", code: fetcherResponseExample }]}
              />
            </div>

            {/* Feature grid */}
            <div className="flex-1 grid grid-cols-1 tablet:grid-cols-2 gap-6">
              {features.map((feature) => (
                <div
                  key={feature.title}
                  className="bg-surface-card border border-hairline rounded-lg p-6"
                >
                  <div className="text-2xl mb-3">{feature.icon}</div>
                  <h3 className="text-body-md font-medium text-ink mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-body-sm text-charcoal">
                    {feature.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Feature Section 2: Built for AI Agents */}
      <section
        className="relative py-16 tablet:py-24 px-6 overflow-hidden"
        style={{
          background:
            "radial-gradient(ellipse 70% 500px at 50% 0px, rgba(34,255,153,0.18), transparent)",
        }}
      >
        <div className="mx-auto max-w-body">
          <div className="text-center mb-12">
            <p className="text-caption text-accent-green uppercase tracking-[0.12em] font-medium mb-3">
              Built for AI agents
            </p>
            <h2
              className="font-display text-ink leading-none tracking-[-0.48px] mb-4"
              style={{ fontSize: "clamp(32px, 4vw, 48px)" }}
            >
              Designed for the
              <br />
              agentic era
            </h2>
            <p className="text-body-lg text-charcoal max-w-xl mx-auto">
              Every Resili feature is built around autonomous AI workflows —
              not human browsing patterns.
            </p>
          </div>

          <div className="grid grid-cols-1 tablet:grid-cols-3 gap-6">
            {agentFeatures.map((feature) => (
              <div
                key={feature.title}
                className="bg-surface-card border border-hairline rounded-lg p-8 text-center"
              >
                <h3 className="text-body-lg font-medium text-ink mb-3">
                  {feature.title}
                </h3>
                <p className="text-body-sm text-charcoal">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
