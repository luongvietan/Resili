"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

interface CodeTab {
  label: string;
  code: string;
}

interface CodeWindowProps {
  tabs?: CodeTab[];
  className?: string;
}

export function CodeWindow({ tabs = [], className }: CodeWindowProps) {
  const [activeTab, setActiveTab] = useState(0);

  if (tabs.length === 0) {
    return null;
  }

  const currentCode = tabs[activeTab]?.code ?? "";

  return (
    <div
      className={cn(
        "bg-surface-deep border border-hairline-strong rounded-lg p-6 font-mono",
        className
      )}
    >
      {/* Traffic-light dots */}
      <div className="flex gap-2 mb-4">
        <div className="w-3 h-3 rounded-full bg-accent-red" />
        <div className="w-3 h-3 rounded-full bg-accent-yellow" />
        <div className="w-3 h-3 rounded-full bg-accent-green" />
      </div>

      {/* Tab strip */}
      {tabs.length > 1 && (
        <div className="flex gap-1 mb-4 border-b border-hairline">
          {tabs.map((tab, i) => (
            <button
              key={tab.label}
              onClick={() => setActiveTab(i)}
              className={cn(
                "px-3 py-1 text-caption rounded-t-sm transition-colors",
                i === activeTab
                  ? "bg-surface-card text-ink border-b-2 border-accent-blue"
                  : "text-charcoal hover:text-body"
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}

      {/* Code content */}
      <pre className="text-code-md text-body overflow-x-auto whitespace-pre-wrap">
        <code>{currentCode}</code>
      </pre>
    </div>
  );
}
