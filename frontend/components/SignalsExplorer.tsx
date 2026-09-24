"use client";

import React, { useState, useMemo } from "react";
import {
  MessageSquare,
  Youtube,
  Terminal,
  Github,
  Twitter,
  Users,
  ExternalLink,
  Search,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Globe,
  Radio,
  SlidersHorizontal
} from "lucide-react";
import { RawFeedback } from "@/lib/types";

interface SignalsExplorerProps {
  feedbacks?: RawFeedback[];
  totalExpected?: number;
}

export function SignalsExplorer({ feedbacks = [], totalExpected = 0 }: SignalsExplorerProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedChannel, setSelectedChannel] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"engagement" | "newest">("engagement");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  const getPlatformMeta = (channel: string) => {
    switch (channel.toLowerCase()) {
      case "reddit":
        return { label: "Reddit", icon: MessageSquare, dotColor: "bg-[#ff9592]" };
      case "youtube":
        return { label: "YouTube", icon: Youtube, dotColor: "bg-[#ff6465]" };
      case "hackernews":
        return { label: "Hacker News", icon: Terminal, dotColor: "bg-[#ffca16]" };
      case "github":
        return { label: "GitHub", icon: Github, dotColor: "bg-[#baa7ff]" };
      case "twitter":
        return { label: "Twitter / X", icon: Twitter, dotColor: "bg-[#70b8ff]" };
      case "facebook":
        return { label: "Facebook", icon: Users, dotColor: "bg-[#3b9eff]" };
      default:
        return { label: channel, icon: Globe, dotColor: "bg-[#3ad389]" };
    }
  };

  // Channel item counts
  const channelCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const item of feedbacks) {
      const ch = item.channel.toLowerCase();
      counts[ch] = (counts[ch] || 0) + 1;
    }
    return counts;
  }, [feedbacks]);

  // Filter and sort
  const filteredFeedbacks = useMemo(() => {
    let result = [...feedbacks];

    if (selectedChannel !== "all") {
      result = result.filter(
        (item) => item.channel.toLowerCase() === selectedChannel.toLowerCase()
      );
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (item) =>
          item.content.toLowerCase().includes(q) ||
          (item.title && item.title.toLowerCase().includes(q)) ||
          (item.author && item.author.toLowerCase().includes(q))
      );
    }

    if (sortBy === "engagement") {
      result.sort((a, b) => (b.engagement_score || 0) - (a.engagement_score || 0));
    } else {
      result.sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
    }

    return result;
  }, [feedbacks, selectedChannel, searchQuery, sortBy]);

  const totalPages = Math.ceil(filteredFeedbacks.length / pageSize) || 1;
  const paginatedFeedbacks = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredFeedbacks.slice(start, start + pageSize);
  }, [filteredFeedbacks, currentPage, pageSize]);

  const handleCopy = (item: RawFeedback) => {
    navigator.clipboard.writeText(
      `"${item.content}"\n— ${item.author || "User"} (${item.url})`
    );
    setCopiedId(item.id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const channelsList = Object.keys(channelCounts);

  return (
    <div className="space-y-6">
      {/* Overview Stat Ribbon (Resend 16px Hairline Cards) */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-5 rounded-[16px] bg-[#000000] border border-[#292d30] flex flex-col justify-between">
          <div className="flex items-center gap-2 text-xs font-mono text-[#a1a4a5]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#3ad389]" />
            <span>Harvested Signals</span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-mono font-medium text-[#ffffff]">
              {feedbacks.length}
            </span>
            <span className="text-xs font-mono text-[#6e727a]">raw items</span>
          </div>
        </div>

        <div className="p-5 rounded-[16px] bg-[#000000] border border-[#292d30] flex flex-col justify-between">
          <div className="flex items-center gap-2 text-xs font-mono text-[#a1a4a5]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#70b8ff]" />
            <span>Filter Matches</span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-mono font-medium text-[#70b8ff]">
              {filteredFeedbacks.length}
            </span>
            <span className="text-xs font-mono text-[#6e727a]">in view</span>
          </div>
        </div>

        <div className="p-5 rounded-[16px] bg-[#000000] border border-[#292d30] flex flex-col justify-between">
          <div className="flex items-center gap-2 text-xs font-mono text-[#a1a4a5]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#9281f7]" />
            <span>Active Sources</span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-mono font-medium text-[#ffffff]">
              {channelsList.length}
            </span>
            <span className="text-xs font-mono text-[#6e727a]">channels</span>
          </div>
        </div>

        <div className="p-5 rounded-[16px] bg-[#000000] border border-[#292d30] flex flex-col justify-between">
          <div className="flex items-center gap-2 text-xs font-mono text-[#a1a4a5]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#ffca16]" />
            <span>Peak Engagement</span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-mono font-medium text-[#ffffff]">
              {feedbacks.length > 0
                ? Math.max(...feedbacks.map((f) => f.engagement_score || 0))
                : 0}
            </span>
            <span className="text-xs font-mono text-[#6e727a]">score</span>
          </div>
        </div>
      </div>

      {/* Control Console (Search, Sort, Channel Filter Pills) */}
      <div className="p-5 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-4">
        <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[#6e727a]" />
            <input
              type="text"
              placeholder="Search verbatim quotes, topics, authors, or keywords..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full pl-10 pr-4 py-2.5 bg-[#000000] border border-[#292d30] rounded-[6px] text-xs font-sans text-[#ffffff] placeholder-[#464a4d] focus:outline-none focus:border-[#ffffff] transition-colors"
            />
          </div>

          {/* Sort Selector */}
          <div className="flex items-center gap-2 shrink-0 text-xs font-mono">
            <span className="text-[#a1a4a5]">Sort:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as "engagement" | "newest")}
              className="bg-[#000000] border border-[#292d30] text-[#f0f0f0] text-xs font-mono rounded-[6px] px-3 py-2 focus:outline-none focus:border-[#ffffff]"
            >
              <option value="engagement">Engagement Score (High to Low)</option>
              <option value="newest">Most Recent</option>
            </select>
          </div>
        </div>

        {/* Channel Filter Pills (6px Radius, Hairline Borders) */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
          <button
            onClick={() => {
              setSelectedChannel("all");
              setCurrentPage(1);
            }}
            className={`px-3 py-1.5 rounded-[6px] text-xs font-mono transition-all shrink-0 flex items-center gap-2 border ${
              selectedChannel === "all"
                ? "bg-[#000000] text-[#ffffff] border-[#ffffff]"
                : "bg-[#000000] text-[#a1a4a5] border-[#292d30] hover:text-[#ffffff] hover:border-[#464a4d]"
            }`}
          >
            <span>All Channels</span>
            <span className="text-[10px] text-[#9281f7]">({feedbacks.length})</span>
          </button>

          {channelsList.map((ch) => {
            const meta = getPlatformMeta(ch);
            const Icon = meta.icon;
            const count = channelCounts[ch] || 0;
            const isSelected = selectedChannel.toLowerCase() === ch.toLowerCase();

            return (
              <button
                key={ch}
                onClick={() => {
                  setSelectedChannel(ch);
                  setCurrentPage(1);
                }}
                className={`px-3 py-1.5 rounded-[6px] text-xs font-mono transition-all shrink-0 flex items-center gap-2 border ${
                  isSelected
                    ? "bg-[#000000] text-[#ffffff] border-[#ffffff]"
                    : "bg-[#000000] text-[#a1a4a5] border-[#292d30] hover:text-[#ffffff] hover:border-[#464a4d]"
                }`}
              >
                <span className={`h-1.5 w-1.5 rounded-full ${meta.dotColor}`} />
                <span>{meta.label}</span>
                <span className="text-[10px] text-[#6e727a]">({count})</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Signals List (16px Black Cards with Graphite Hairline) */}
      {paginatedFeedbacks.length === 0 ? (
        <div className="p-12 text-center rounded-[16px] bg-[#000000] border border-[#292d30] space-y-3">
          <MessageSquare className="h-6 w-6 text-[#464a4d] mx-auto" />
          <h3 className="text-sm font-sans font-medium text-[#f0f0f0]">
            No verbatim signals match your filter
          </h3>
          <p className="text-xs font-sans text-[#a1a4a5] max-w-sm mx-auto">
            Try clearing your search query or switching channel pills to view other harvested community discussions.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {paginatedFeedbacks.map((item) => {
            const meta = getPlatformMeta(item.channel);
            const isExpanded = expandedId === item.id;
            const isLong = item.content.length > 240;

            return (
              <div
                key={item.id}
                className="p-5 sm:p-6 rounded-[16px] bg-[#000000] border border-[#292d30] hover:border-[#464a4d] transition-all space-y-3 group"
              >
                {/* Meta Header */}
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-mono">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[6px] border border-[#292d30] bg-[#000000]">
                      <span className={`h-1.5 w-1.5 rounded-full ${meta.dotColor}`} />
                      <span className="text-[#ffffff]">{meta.label}</span>
                    </div>

                    {item.author && (
                      <span className="text-[#9281f7]">
                        @{item.author.replace(/^[@u\/]/, "")}
                      </span>
                    )}

                    <span className="text-[#464a4d]">•</span>

                    <span className="text-[#a1a4a5]">
                      Engagement: {item.engagement_score || 0}
                    </span>
                  </div>

                  {/* Resend Ghost Action Buttons */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleCopy(item)}
                      title="Copy citation"
                      className="p-1.5 rounded-[6px] bg-[#000000] border border-[#292d30] hover:border-[#ffffff] text-[#a1a4a5] hover:text-[#ffffff] transition-all"
                    >
                      {copiedId === item.id ? (
                        <Check className="h-3.5 w-3.5 text-[#3ad389]" />
                      ) : (
                        <Copy className="h-3.5 w-3.5" />
                      )}
                    </button>

                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-[6px] bg-[#000000] border border-[#292d30] hover:border-[#ffffff] text-xs font-mono text-[#f0f0f0] hover:text-[#ffffff] transition-all"
                    >
                      <span>Source</span>
                      <ExternalLink className="h-3 w-3 text-[#a1a4a5]" />
                    </a>
                  </div>
                </div>

                {/* Title if present */}
                {item.title && (
                  <h4 className="text-sm font-sans font-medium text-[#ffffff] leading-snug">
                    {item.title}
                  </h4>
                )}

                {/* Verbatim Content */}
                <div className="text-sm font-sans text-[#f0f0f0] leading-relaxed whitespace-pre-line">
                  {isLong && !isExpanded ? (
                    <>
                      {item.content.slice(0, 240)}...
                      <button
                        onClick={() => setExpandedId(item.id)}
                        className="ml-2 text-[#9281f7] hover:underline inline-flex items-center gap-0.5 text-xs font-mono"
                      >
                        <span>show_more</span>
                        <ChevronDown className="h-3 w-3" />
                      </button>
                    </>
                  ) : (
                    <>
                      {item.content}
                      {isLong && (
                        <button
                          onClick={() => setExpandedId(null)}
                          className="ml-2 text-[#9281f7] hover:underline inline-flex items-center gap-0.5 text-xs font-mono"
                        >
                          <span>show_less</span>
                          <ChevronUp className="h-3 w-3" />
                        </button>
                      )}
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Pagination Footer */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-[#292d30] pt-4 px-2 text-xs font-mono">
          <span className="text-[#a1a4a5]">
            Showing {(currentPage - 1) * pageSize + 1} to{" "}
            {Math.min(currentPage * pageSize, filteredFeedbacks.length)} of{" "}
            {filteredFeedbacks.length}
          </span>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1.5 rounded-[6px] bg-[#000000] border border-[#292d30] text-[#f0f0f0] disabled:opacity-30 disabled:cursor-not-allowed hover:border-[#ffffff] transition-all"
            >
              Previous
            </button>
            <span className="text-[#a1a4a5] px-2">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1.5 rounded-[6px] bg-[#000000] border border-[#292d30] text-[#f0f0f0] disabled:opacity-30 disabled:cursor-not-allowed hover:border-[#ffffff] transition-all"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
