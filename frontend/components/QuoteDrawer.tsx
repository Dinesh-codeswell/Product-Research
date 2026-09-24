"use client";

import React, { useState } from "react";
import {
  X,
  ExternalLink,
  Copy,
  Check,
  MessageSquare,
  Youtube,
  Quote,
  Terminal,
  Github,
  Twitter,
  Users,
  Globe
} from "lucide-react";
import { InsightCluster, EvidenceQuote } from "@/lib/types";

interface QuoteDrawerProps {
  cluster: InsightCluster | null;
  onClose: () => void;
}

export function QuoteDrawer({ cluster, onClose }: QuoteDrawerProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  if (!cluster) return null;

  const handleCopy = (quote: EvidenceQuote) => {
    navigator.clipboard.writeText(
      `"${quote.quote_text}" — ${quote.source_author || "Verified User"} (${quote.permalink})`
    );
    setCopiedId(quote.id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getPlatformMeta = (channel: string) => {
    switch (channel.toLowerCase()) {
      case "reddit":
        return { label: "Reddit", dotColor: "bg-[#ff9592]" };
      case "youtube":
        return { label: "YouTube", dotColor: "bg-[#ff6465]" };
      case "hackernews":
        return { label: "Hacker News", dotColor: "bg-[#ffca16]" };
      case "github":
        return { label: "GitHub", dotColor: "bg-[#baa7ff]" };
      case "twitter":
        return { label: "Twitter / X", dotColor: "bg-[#70b8ff]" };
      case "facebook":
        return { label: "Facebook", dotColor: "bg-[#3b9eff]" };
      default:
        return { label: channel, dotColor: "bg-[#3ad389]" };
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[500px] bg-[#000000]/95 backdrop-blur-[25px] border-l border-[#292d30] flex flex-col animate-in slide-in-from-right duration-200">
      {/* Drawer Header */}
      <div className="p-6 border-b border-[#292d30] flex items-start justify-between gap-4">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono text-[#9281f7] bg-[#000000] px-2 py-0.5 rounded-[6px] border border-[#292d30]">
              VERIFIED EVIDENCE
            </span>
            <span className="text-xs font-mono text-[#a1a4a5]">
              {cluster.quotes.length} Quotes
            </span>
          </div>

          <h2 className="text-lg font-sans font-medium text-[#ffffff] leading-snug">
            {cluster.title}
          </h2>
        </div>

        <button
          onClick={onClose}
          className="p-1.5 rounded-[6px] text-[#a1a4a5] hover:text-[#ffffff] border border-transparent hover:border-[#292d30] transition-colors"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Verbatim Quotes List (Resend Testimonial Card pattern) */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {cluster.quotes.length === 0 ? (
          <div className="text-center py-12 text-xs font-mono text-[#6e727a]">
            No verbatim quotes captured for this cluster.
          </div>
        ) : (
          cluster.quotes.map((quote) => {
            const meta = getPlatformMeta(quote.source_channel);

            return (
              <div
                key={quote.id}
                className="p-5 rounded-[16px] bg-[#000000] border border-[#292d30] hover:border-[#464a4d] transition-colors space-y-3"
              >
                {/* Platform Badge & Author */}
                <div className="flex items-center justify-between text-xs font-mono">
                  <div className="flex items-center gap-2">
                    <span className={`h-1.5 w-1.5 rounded-full ${meta.dotColor}`} />
                    <span className="text-[#a1a4a5]">{meta.label}</span>
                    <span className="text-[#464a4d]">•</span>
                    <span className="text-[#9281f7]">
                      @{quote.source_author?.replace(/^[@u\/]/, "") || "user"}
                    </span>
                  </div>

                  <span className="text-[#6e727a]">
                    ⚡ {quote.engagement_score || 0}
                  </span>
                </div>

                {/* Quote Text */}
                <blockquote className="text-sm font-sans text-[#f0f0f0] leading-relaxed italic border-l border-[#292d30] pl-3 py-0.5">
                  "{quote.quote_text}"
                </blockquote>

                {/* Action Buttons */}
                <div className="pt-2 border-t border-[#292d30] flex items-center justify-end gap-2 text-xs font-mono">
                  <button
                    onClick={() => handleCopy(quote)}
                    className="p-1.5 rounded-[6px] bg-[#000000] border border-[#292d30] hover:border-[#ffffff] text-[#a1a4a5] hover:text-[#ffffff] transition-all"
                    title="Copy quote"
                  >
                    {copiedId === quote.id ? (
                      <Check className="h-3.5 w-3.5 text-[#3ad389]" />
                    ) : (
                      <Copy className="h-3.5 w-3.5" />
                    )}
                  </button>

                  <a
                    href={quote.permalink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-[6px] bg-[#000000] border border-[#292d30] hover:border-[#ffffff] text-xs font-mono text-[#f0f0f0] hover:text-[#ffffff] transition-all"
                  >
                    <span>Source</span>
                    <ExternalLink className="h-3 w-3 text-[#a1a4a5]" />
                  </a>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
