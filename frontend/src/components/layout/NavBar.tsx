"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

const navLinks = [
  { label: "Docs", href: "/docs" },
  { label: "Pricing", href: "#pricing" },
  { label: "Blog", href: "/blog" },
];

export function NavBar() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-hairline bg-canvas/80 backdrop-blur-sm">
      <div className="mx-auto max-w-body px-6 flex items-center justify-between h-14">
        {/* Logo */}
        <a href="/" className="flex items-center gap-2 text-ink font-display font-semibold text-body-md">
          <span className="w-6 h-6 rounded-md bg-accent-orange flex items-center justify-center text-canvas text-body-xs font-bold">
            R
          </span>
          Resili
        </a>

        {/* Desktop nav */}
        <nav className="hidden tablet-lg:flex items-center gap-6">
          {navLinks.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="text-charcoal hover:text-ink text-body-sm transition-colors"
            >
              {link.label}
            </a>
          ))}
        </nav>

        {/* Desktop CTA */}
        <div className="hidden tablet-lg:flex items-center gap-3">
          <a href="/login" className="text-charcoal hover:text-ink text-body-sm transition-colors">
            Sign in
          </a>
          <Button variant="primary" href="/signup" className="h-8 px-3 text-body-xs">
            Get started
          </Button>
        </div>

        {/* Hamburger */}
        <button
          type="button"
          className="tablet-lg:hidden flex flex-col gap-1.5 p-2"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Toggle menu"
          aria-expanded={menuOpen}
          aria-controls="mobile-nav-panel"
        >
          <span
            className={cn(
              "block w-5 h-0.5 bg-ink transition-transform origin-center",
              menuOpen && "rotate-45 translate-y-2"
            )}
          />
          <span
            className={cn(
              "block w-5 h-0.5 bg-ink transition-opacity",
              menuOpen && "opacity-0"
            )}
          />
          <span
            className={cn(
              "block w-5 h-0.5 bg-ink transition-transform origin-center",
              menuOpen && "-rotate-45 -translate-y-2"
            )}
          />
        </button>
      </div>

      {/* Mobile menu */}
      <div
        id="mobile-nav-panel"
        className={cn(
          "tablet-lg:hidden border-t border-hairline bg-canvas overflow-hidden transition-all duration-200",
          menuOpen ? "max-h-64" : "max-h-0"
        )}
      >
        <nav className="flex flex-col px-6 py-4 gap-4">
          {navLinks.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="text-charcoal hover:text-ink text-body-md transition-colors"
              onClick={() => setMenuOpen(false)}
            >
              {link.label}
            </a>
          ))}
          <div className="flex flex-col gap-3 pt-2 border-t border-hairline">
            <a href="/login" className="text-charcoal hover:text-ink text-body-md transition-colors">
              Sign in
            </a>
            <Button variant="primary" href="/signup" className="w-full justify-center">
              Get started
            </Button>
          </div>
        </nav>
      </div>
    </header>
  );
}
