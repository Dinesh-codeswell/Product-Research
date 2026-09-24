"use client";

import React, { useState, useMemo } from "react";
import {
  Monitor,
  Lock,
  Pause,
  Play,
  RotateCw,
  ExternalLink,
  Terminal,
  ShieldCheck,
  CheckCircle2,
  Sparkles,
  Layers,
  ArrowRight,
  Search,
  Filter,
  Radio,
  Share2,
  ThumbsUp,
  MessageSquare,
  Download
} from "lucide-react";
import { BrowserActionEvent, RawFeedback, InsightCluster } from "@/lib/types";
import { getExportUrl } from "@/lib/api";

interface LiveBrowserViewportProps {
  events: BrowserActionEvent[];
  isSessionRunning: boolean;
  feedbacks?: RawFeedback[];
  clusters?: InsightCluster[];
  sessionId?: string;
  onSwitchToFocusMode?: () => void;
}

export function LiveBrowserViewport({
  events,
  isSessionRunning,
  feedbacks = [],
  clusters = [],
  sessionId,
  onSwitchToFocusMode,
}: LiveBrowserViewportProps) {
  const [isPaused, setIsPaused] = useState(false);
  const [selectedChannel, setSelectedChannel] = useState<string>("all");
  const [searchFilter, setSearchFilter] = useState<string>("");

  const latestEvent = events.length > 0 ? events[events.length - 1] : null;
  const currentUrl = latestEvent?.url || (feedbacks.length > 0 ? feedbacks[0].url : "about:blank");
  const currentAction = latestEvent?.action || (isSessionRunning ? "INSPECTING" : "STANDBY");
  const currentChannel = latestEvent?.channel || (feedbacks.length > 0 ? feedbacks[0].channel : "system");
  const latestScreenshot = latestEvent?.screenshot;

  // Filter signals
  const filteredFeedbacks = useMemo(() => {
    return feedbacks.filter((fb) => {
      const matchesChannel = selectedChannel === "all" || fb.channel.toLowerCase() === selectedChannel.toLowerCase();
      const matchesQuery =
        !searchFilter ||
        (fb.title && fb.title.toLowerCase().includes(searchFilter.toLowerCase())) ||
        fb.content.toLowerCase().includes(searchFilter.toLowerCase()) ||
        (fb.author && fb.author.toLowerCase().includes(searchFilter.toLowerCase()));
      return matchesChannel && matchesQuery;
    });
  }, [feedbacks, selectedChannel, searchFilter]);

  // Unique channel counts
  const channelCounts = useMemo(() => {
    const counts: Record<string, number> = { all: feedbacks.length };
    for (const fb of feedbacks) {
      const ch = fb.channel.toLowerCase();
      counts[ch] = (counts[ch] || 0) + 1;
    }
    return counts;
  }, [feedbacks]);

  const channelsList = Object.keys(channelCounts).filter((k) => k !== "all");

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Viewport Terminal Container (Resend 16px Terminal Window) */}
      <div className="rounded-[16px] bg-[#000000] border border-[#292d30] overflow-hidden shadow-2xl">
        {/* Terminal Header & Browser Chrome Bar */}
        <div className="p-4 border-b border-[#292d30] bg-[#000000] flex flex-col md:flex-row md:items-center justify-between gap-3">
          {/* Traffic Light Dots & Status */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-[#292d30]" />
              <span className="h-2.5 w-2.5 rounded-full bg-[#292d30]" />
              <span className="h-2.5 w-2.5 rounded-full bg-[#292d30]" />
            </div>

            <div className="flex items-center gap-2 pl-2 border-l border-[#292d30]">
              <span
                className={`h-2 w-2 rounded-full ${
                  isSessionRunning
                    ? isPaused
                      ? "bg-[#ffca16]"
                      : "bg-[#3ad389] animate-pulse"
                    : "bg-[#3ad389]"
                }`}
              />
              <span className="text-xs font-mono text-[#ffffff] uppercase tracking-wider">
                {isSessionRunning
                  ? isPaused
                    ? "AGENT PAUSED"
                    : "AGENT IN CONTROL (LIVE)"
                  : "INSPECTION COMPLETE • DATA SYNTHESIZED"}
              </span>
            </div>
          </div>

          {/* URL Omnibox (Commit Mono with Lock) */}
          <div className="flex-1 max-w-xl mx-auto w-full">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-[6px] bg-[#000000] border border-[#292d30] text-xs font-mono text-[#a1a4a5]">
              <Lock className="h-3 w-3 text-[#3ad389] shrink-0" />
              <span className="truncate text-[#ffffff]">{currentUrl}</span>
            </div>
          </div>

          {/* Channel Tag & Actions */}
          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-[#9281f7] bg-[#000000] px-2.5 py-1 rounded-[6px] border border-[#292d30] capitalize font-medium">
              {currentChannel}
            </span>

            {isSessionRunning && (
              <button
                onClick={() => setIsPaused(!isPaused)}
                className="px-2.5 py-1 rounded-[6px] bg-[#000000] border border-[#292d30] hover:border-[#ffffff] text-[#a1a4a5] hover:text-[#ffffff] transition-colors flex items-center gap-1.5"
              >
                {isPaused ? <Play className="h-3 w-3" /> : <Pause className="h-3 w-3" />}
                <span>{isPaused ? "Resume" : "Pause"}</span>
              </button>
            )}
          </div>
        </div>

        {/* Live Viewport Screencast Screen */}
        <div className="relative aspect-[16/10] sm:aspect-[16/9] w-full bg-[#000000] flex items-center justify-center overflow-hidden border-b border-[#292d30]">
          {latestScreenshot ? (
            <div className="relative w-full h-full">
              {/* Actual Base64 Screencast Image */}
              <img
                src={latestScreenshot}
                alt="Live agent browser viewport"
                className="w-full h-full object-contain bg-[#000000]"
              />

              {/* Action HUD Overlay Pill */}
              <div className="absolute top-4 left-4 z-10 flex items-center gap-2 px-3 py-1.5 rounded-[6px] bg-[#000000]/90 backdrop-blur-md border border-[#292d30] text-xs font-mono">
                <span className="h-2 w-2 rounded-full bg-[#9281f7] animate-ping" />
                <span className="text-[#9281f7] font-semibold">[{currentAction}]</span>
                <span className="text-[#f0f0f0] truncate max-w-xs sm:max-w-md">
                  {latestEvent?.description}
                </span>
              </div>

              {/* Live Tag Watermark */}
              <div className="absolute bottom-4 right-4 z-10 px-2.5 py-1 rounded-[6px] bg-[#000000]/80 backdrop-blur-sm border border-[#292d30] text-[10px] font-mono text-[#a1a4a5]">
                1280x800 Chromium • Anti-Gatekeeping Active
              </div>
            </div>
          ) : (
            <div className="text-center p-8 space-y-4 font-mono text-xs">
              <div className="w-12 h-12 mx-auto rounded-[6px] bg-[#000000] border border-[#292d30] flex items-center justify-center text-[#9281f7]">
                <Monitor className="h-6 w-6 animate-pulse" />
              </div>
              <div className="space-y-1">
                <p className="text-[#ffffff] font-medium text-sm">
                  {isSessionRunning
                    ? "Connecting to Live Browser Session..."
                    : "Autonomous Browser Sweep Complete"}
                </p>
                <p className="text-[#6e727a] text-[11px] max-w-md mx-auto">
                  {isSessionRunning
                    ? "Visible window spawned on host desktop. Live screencast will mirror un-gatekept frames here in real-time."
                    : `The agent successfully inspected all targeted channels, bypassed login walls via privacy syndication, and persisted ${feedbacks.length} verified signals below.`}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Live Action Stream Ticker (Commit Mono Terminal Feed) */}
        <div className="p-4 sm:p-5 bg-[#000000] space-y-3">
          <div className="flex items-center justify-between text-xs font-mono">
            <div className="flex items-center gap-2 text-[#a1a4a5]">
              <Terminal className="h-3.5 w-3.5 text-[#9281f7]" />
              <span>AGENT_ACTION_STREAM.log</span>
            </div>

            <span className="text-[11px] text-[#6e727a]">
              {events.length} actions logged
            </span>
          </div>

          <div className="p-4 rounded-[6px] bg-[#000000] border border-[#292d30] font-mono text-xs text-[#a1a4a5] space-y-2 max-h-40 overflow-y-auto">
            {events.length === 0 ? (
              <div className="text-[#6e727a] text-center py-3">
                {isSessionRunning
                  ? "Awaiting first agent browser dispatch event..."
                  : `Browser session finalized with ${feedbacks.length} captured signals.`}
              </div>
            ) : (
              events.map((evt, idx) => (
                <div key={idx} className="flex items-start gap-2.5 leading-relaxed">
                  <span className="text-[#6e727a] shrink-0">{evt.timestamp}</span>
                  <span className="text-[#9281f7] shrink-0 font-medium">
                    [{evt.action}]
                  </span>
                  <span className="text-[#f0f0f0] truncate">{evt.description}</span>
                  {evt.url && (
                    <span className="text-[#464a4d] truncate hidden md:inline">
                      ({evt.url})
                    </span>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Anti-Gatekeeping & Professional Architecture Status Card */}
      <div className="p-4 sm:p-5 rounded-[16px] bg-[#000000] border border-[#292d30] flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs font-mono">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-[6px] bg-[#000000] border border-[#292d30] text-[#3ad389]">
            <ShieldCheck className="h-4 w-4" />
          </div>
          <div>
            <div className="text-[#ffffff] font-medium flex items-center gap-2">
              <span>Anti-Gatekeeping & Surplus Extraction Engine</span>
              <span className="px-1.5 py-0.5 rounded-[4px] bg-[#3ad389]/10 text-[#3ad389] text-[10px] border border-[#3ad389]/30">
                ACTIVE
              </span>
            </div>
            <p className="text-[#a1a4a5] text-[11px] mt-0.5">
              Routes around login gates via un-gatekept syndication, Playwright stealth evasions, and authenticated cookie hydration.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-[#a1a4a5] text-[11px] shrink-0">
          <div>
            <span className="text-[#ffffff] font-bold">{feedbacks.length}</span> Signals Captured
          </div>
          <span className="text-[#292d30]">•</span>
          <div>
            <span className="text-[#ffffff] font-bold">{clusters.length}</span> Clusters Synthesized
          </div>
        </div>
      </div>

      {/* Harvested Signals Live Inspection Grid (Resolves Gatekeeping Visibility Issue) */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#292d30] pb-3">
          <div className="flex items-center gap-2">
            <Radio className="h-4 w-4 text-[#9281f7]" />
            <h2 className="text-sm font-mono text-[#ffffff] font-medium">
              HARVESTED_SIGNALS_FEED ({filteredFeedbacks.length} of {feedbacks.length})
            </h2>
          </div>

          {/* Controls: Search & AI Bundle Export */}
          <div className="flex items-center gap-2 w-full sm:w-auto">
            {sessionId && feedbacks.length > 0 && (
              <a
                href={getExportUrl(sessionId, "ai-bundle")}
                download
                className="shrink-0 px-3 py-1.5 rounded-[6px] bg-[#000000] border border-[#9281f7]/50 hover:border-[#9281f7] text-[#9281f7] hover:text-[#ffffff] text-xs font-mono inline-flex items-center gap-1.5 transition-colors shadow-subtle"
                title="Download full Markdown dossier with Firecrawl articles formatted for Cursor and AI agents"
              >
                <Download className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Export</span>
                <span>AI Bundle (.md)</span>
              </a>
            )}

            {/* Quick Search */}
            <div className="relative w-full sm:w-64">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#6e727a]" />
              <input
                type="text"
                placeholder="Search captured text..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 rounded-[6px] bg-[#000000] border border-[#292d30] focus:border-[#ffffff] text-xs font-mono text-[#ffffff] placeholder-[#6e727a] outline-none"
              />
            </div>
          </div>
        </div>

        {/* Channel Filter Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
          <button
            onClick={() => setSelectedChannel("all")}
            className={`px-3 py-1 rounded-[6px] text-xs font-mono transition-colors border ${
              selectedChannel === "all"
                ? "bg-[#ffffff] text-[#000000] border-[#ffffff] font-semibold"
                : "bg-[#000000] text-[#a1a4a5] border-[#292d30] hover:text-[#ffffff] hover:border-[#6e727a]"
            }`}
          >
            All Channels ({channelCounts.all || 0})
          </button>

          {channelsList.map((ch) => (
            <button
              key={ch}
              onClick={() => setSelectedChannel(ch)}
              className={`px-3 py-1 rounded-[6px] text-xs font-mono capitalize transition-colors border ${
                selectedChannel === ch
                  ? "bg-[#9281f7] text-[#ffffff] border-[#9281f7] font-semibold"
                  : "bg-[#000000] text-[#a1a4a5] border-[#292d30] hover:text-[#ffffff] hover:border-[#6e727a]"
              }`}
            >
              {ch} ({channelCounts[ch]})
            </button>
          ))}
        </div>

        {/* Signals Cards Grid */}
        {filteredFeedbacks.length === 0 ? (
          <div className="p-12 text-center rounded-[16px] bg-[#000000] border border-[#292d30] space-y-2">
            <p className="text-sm font-mono text-[#ffffff]">
              {feedbacks.length === 0
                ? "Awaiting first harvest batch from active browser workers..."
                : "No signals match the current search or channel filter."}
            </p>
            <p className="text-xs font-mono text-[#6e727a]">
              The autonomous agent will populate real community quotes and permalinks as each channel is swept.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredFeedbacks.map((fb) => (
              <div
                key={fb.id}
                className="p-5 rounded-[16px] bg-[#000000] border border-[#292d30] hover:border-[#9281f7]/50 transition-all duration-150 flex flex-col justify-between gap-4 group"
              >
                <div className="space-y-2.5">
                  {/* Top metadata badge row */}
                  <div className="flex items-center justify-between gap-2 text-xs font-mono">
                    <span className="px-2 py-0.5 rounded-[4px] bg-[#000000] border border-[#292d30] text-[#9281f7] uppercase font-semibold text-[10px]">
                      {fb.channel}
                    </span>

                    <div className="flex items-center gap-2 text-[11px] text-[#6e727a]">
                      <span className="text-[#a1a4a5]">{fb.author || "anonymous"}</span>
                      <span>•</span>
                      <span className="text-[#3ad389] flex items-center gap-1">
                        <ThumbsUp className="h-3 w-3" />
                        {fb.engagement_score}
                      </span>
                    </div>
                  </div>

                  {/* Title with link */}
                  {fb.title && (
                    <a
                      href={fb.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-sm text-[#ffffff] hover:text-[#9281f7] transition-colors inline-flex items-center gap-1.5 group-hover:underline"
                    >
                      <span className="line-clamp-2">{fb.title}</span>
                      <ExternalLink className="h-3 w-3 shrink-0 text-[#6e727a]" />
                    </a>
                  )}

                  {/* Verbatim quote snippet */}
                  <p className="text-xs text-[#a1a4a5] leading-relaxed line-clamp-4 font-sans whitespace-pre-line">
                    {fb.content}
                  </p>
                </div>

                {/* Footer link to source */}
                <div className="pt-3 border-t border-[#292d30] flex items-center justify-between text-xs font-mono text-[#6e727a]">
                  <span className="truncate max-w-[220px] text-[10px]">
                    {fb.url}
                  </span>

                  <a
                    href={fb.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[#9281f7] hover:underline inline-flex items-center gap-1 text-[11px]"
                  >
                    <span>View Source</span>
                    <ArrowRight className="h-3 w-3" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Switch to Focus Mode Banner */}
      {onSwitchToFocusMode && (
        <div className="flex items-center justify-between p-4 rounded-[16px] bg-[#000000] border border-[#292d30] text-xs font-mono">
          <div className="flex items-center gap-2 text-[#a1a4a5]">
            <Layers className="h-4 w-4 text-[#9281f7]" />
            <span>Ready to explore clustered themes or synthesize specs?</span>
          </div>

          <button
            onClick={onSwitchToFocusMode}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] bg-[#000000] border border-[#292d30] hover:border-[#ffffff] text-[#f0f0f0] hover:text-[#ffffff] transition-all"
          >
            <span>Jump to Theme Matrix</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}
