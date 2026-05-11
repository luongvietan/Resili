import { Button } from "@/components/ui/Button";
import { CodeWindow } from "@/components/ui/CodeWindow";

const curlExample = `curl -X POST https://api.resili.io/api/v1/scrape/fetch \\
  -H "Authorization: Bearer rsl_your_key_here" \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://example.com", "format": "markdown"}'`;

const pythonExample = `import requests

response = requests.post(
    "https://api.resili.io/api/v1/scrape/fetch",
    headers={"Authorization": "Bearer rsl_your_key_here"},
    json={"url": "https://example.com", "format": "markdown"}
)
data = response.json()
print(data["content"])`;

const codeTabs = [
  { label: "curl", code: curlExample },
  { label: "Python", code: pythonExample },
];

export function Hero() {
  return (
    <section
      id="hero-stripe"
      className="relative pt-32 pb-16 tablet:pb-24 desktop:pb-32 px-6 overflow-hidden"
      style={{
        background:
          "radial-gradient(ellipse 80% 600px at 50% -100px, rgba(0,117,255,0.34), transparent)",
      }}
    >
      <div className="mx-auto max-w-body">
        <div className="flex flex-col tablet-lg:flex-row items-center gap-12 desktop:gap-20">
          {/* Text side */}
          <div className="flex-1 text-center tablet-lg:text-left">
            <div className="inline-flex items-center gap-2 bg-surface-card border border-hairline-strong rounded-full px-3 py-1 mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-green" />
              <span className="text-caption text-charcoal">Now in public beta</span>
            </div>

            <h1
              className="font-display text-ink leading-none tracking-[-0.96px] mb-6"
              style={{ fontSize: "clamp(44px, 6vw, 96px)" }}
            >
              Web data for
              <br />
              <span className="text-accent-blue">AI agents</span>
            </h1>

            <p className="text-body-xl text-charcoal max-w-lg mx-auto tablet-lg:mx-0 mb-8">
              High-performance scraping API built for LLM workflows. Fetch,
              transform, and integrate web content at scale — no infrastructure
              to manage.
            </p>

            <div className="flex flex-col mobile:flex-row gap-3 justify-center tablet-lg:justify-start">
              <Button
                variant="primary"
                href="/signup"
                className="h-11 px-6 text-body-md"
              >
                Get started
              </Button>
              <Button variant="ghost" href="/docs" className="h-11 px-6 text-body-md">
                View docs
              </Button>
            </div>

            <p className="text-body-xs text-mute mt-4">
              Free tier available · No credit card required
            </p>
          </div>

          {/* Code window side */}
          <div className="flex-1 w-full max-w-xl tablet-lg:max-w-none">
            <CodeWindow tabs={codeTabs} />
          </div>
        </div>
      </div>
    </section>
  );
}
