const footerLinks = {
  Product: [
    { label: "Features", href: "#features" },
    { label: "Pricing", href: "#pricing" },
    { label: "Changelog", href: "/changelog" },
    { label: "Status", href: "https://status.resili.io" },
  ],
  Developers: [
    { label: "Documentation", href: "/docs" },
    { label: "API Reference", href: "/docs/api" },
    { label: "SDKs", href: "/docs/sdks" },
    { label: "MCP Server", href: "/docs/mcp" },
  ],
  Company: [
    { label: "About", href: "/about" },
    { label: "Blog", href: "/blog" },
    { label: "Contact", href: "/contact" },
    { label: "Privacy", href: "/privacy" },
  ],
};

export function Footer() {
  return (
    <footer className="border-t border-hairline bg-surface-card px-6 py-12 tablet:py-16">
      <div className="mx-auto max-w-body">
        <div className="flex flex-col tablet:flex-row gap-12 tablet:gap-8">
          {/* Brand */}
          <div className="flex-shrink-0 max-w-xs">
            <a
              href="/"
              className="flex items-center gap-2 text-ink font-display font-semibold text-body-md mb-4"
            >
              <span className="w-6 h-6 rounded-md bg-accent-orange flex items-center justify-center text-canvas text-body-xs font-bold">
                R
              </span>
              Resili
            </a>
            <p className="text-body-sm text-charcoal">
              Web data infrastructure for the next generation of AI agents.
            </p>
          </div>

          {/* Links */}
          <div className="flex-1 grid grid-cols-2 tablet:grid-cols-3 gap-8">
            {Object.entries(footerLinks).map(([category, links]) => (
              <div key={category}>
                <h4 className="text-caption font-medium text-charcoal uppercase tracking-[0.08em] mb-4">
                  {category}
                </h4>
                <ul className="flex flex-col gap-2">
                  {links.map((link) => (
                    <li key={link.label}>
                      <a
                        href={link.href}
                        className="text-body-sm text-mute hover:text-body transition-colors"
                      >
                        {link.label}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-12 pt-6 border-t border-hairline flex flex-col mobile:flex-row items-center justify-between gap-4">
          <p className="text-body-xs text-mute">
            © 2026 Resili, Inc. All rights reserved.
          </p>
          <div className="flex items-center gap-4">
            <a href="/terms" className="text-body-xs text-mute hover:text-charcoal transition-colors">
              Terms
            </a>
            <a href="/privacy" className="text-body-xs text-mute hover:text-charcoal transition-colors">
              Privacy
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
