"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  Key,
  Sliders,
  Sparkles,
  ArrowRight,
  MessageSquare,
  Youtube,
  Twitter,
  Terminal,
  Github,
  Users,
  Loader2,
  ChevronRight,
  Monitor,
  Layers,
  Globe
} from "lucide-react";
import { startResearch } from "@/lib/api";
import { ChannelSettingsModal } from "@/components/ChannelSettingsModal";
import { BrowserApprovalModal } from "@/components/BrowserApprovalModal";

const AVAILABLE_CHANNELS = [
  { id: "google", label: "Google / Web", icon: Globe, domain: "google.com" },
  { id: "reddit", label: "Reddit", icon: MessageSquare, domain: "reddit.com" },
  { id: "youtube", label: "YouTube", icon: Youtube, domain: "youtube.com" },
  { id: "twitter", label: "Twitter / X", icon: Twitter, domain: "x.com" },
  { id: "hackernews", label: "Hacker News", icon: Terminal, domain: "news.ycombinator.com" },
  { id: "github", label: "GitHub", icon: Github, domain: "github.com" },
  { id: "facebook", label: "Facebook", icon: Users, domain: "facebook.com" },
];

export function QueryLauncher() {
  const router = useRouter();

  const [query, setQuery] = useState("");
  const [channels, setChannels] = useState<string[]>([
    "google",
    "reddit",
    "youtube",
    "twitter",
    "hackernews",
    "github",
  ]);
  const [sampleSize, setSampleSize] = useState<number>(80);
  const [subreddits, setSubreddits] = useState<string>("");
  const [executionMode, setExecutionMode] = useState<"focus" | "browser">("focus");
  const [isApprovalOpen, setIsApprovalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const toggleChannel = (channel: string) => {
    if (channels.includes(channel)) {
      if (channels.length > 1) {
        setChannels(channels.filter((c) => c !== channel));
      }
    } else {
      setChannels([...channels, channel]);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    if (executionMode === "browser") {
      // Prompt for explicit user approval before spawning browser
      setIsApprovalOpen(true);
    } else {
      doLaunch("focus", false);
    }
  };

  const doLaunch = async (mode: "focus" | "browser", approved: boolean) => {
    setIsApprovalOpen(false);
    setIsLoading(true);
    setError(null);

    try {
      const subList = subreddits
        .split(",")
        .map((s) => s.trim().replace(/^r\//, ""))
        .filter(Boolean);

      const res = await startResearch({
        query: query.trim(),
        channels,
        subreddits: subList.length > 0 ? subList : undefined,
        max_items: sampleSize,
        execution_mode: mode,
        browser_approved: approved,
      });

      router.push(`/research/${res.session_id}`);
    } catch (err: any) {
      setError(err.message || "Failed to start research session");
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full space-y-12">
      {/* Editorial Hero Section (Domaine Serif + 3D Wireframe Cube) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center pt-4 sm:pt-8">
        <div className="lg:col-span-8 space-y-6">
          {/* Resend Hero Announcement Pill */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-transparent border border-[#292d30] text-xs font-sans text-[#f0f0f0] hover:border-[#ffffff]/50 transition-colors">
            <span className="h-1.5 w-1.5 rounded-full bg-[#9281f7]" />
            <span className="font-mono text-[11px] text-[#9281f7]">v1.2</span>
            <span className="text-[#a1a4a5]">•</span>
            <span>Multi-channel intelligence & live browser control</span>
            <ChevronRight className="h-3 w-3 text-[#a1a4a5]" />
          </div>

          {/* Domaine Editorial Display Headline */}
          <h1 className="font-serif text-4xl sm:text-6xl lg:text-7xl font-normal text-[#ffffff] tracking-[-0.01em] leading-[1.05]">
            Customer truth, <br />
            <span className="italic text-[#f0f0f0]">extracted from the void.</span>
          </h1>

          <p className="text-base sm:text-lg font-sans text-[#a1a4a5] max-w-2xl leading-relaxed">
            Sweep verbatim discussions across Reddit, YouTube transcripts, Twitter/X, Hacker News, and GitHub issues. Choose between silent Focus Mode or Live Interactive Browser Agent control.
          </p>
        </div>

        {/* Sculptural Black 3D Cube Anchor */}
        <div className="lg:col-span-4 flex items-center justify-center lg:justify-end">
          <div className="relative w-48 h-48 sm:w-56 sm:h-56 flex items-center justify-center">
            {/* Minimalist Isometric Cube in pure black with hairline edges */}
            <div className="relative w-36 h-36 border border-[#292d30] rounded-[16px] bg-[#000000] rotate-12 transition-transform duration-700 hover:rotate-6 shadow-subtle flex flex-col justify-between p-4 group">
              <div className="flex items-center justify-between text-[11px] font-mono text-[#a1a4a5]">
                <div className="flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#3ad389]" />
                  <span>{executionMode === "browser" ? "BROWSER" : "FOCUS"}</span>
                </div>
                <span className="text-[#9281f7]">7 CHANNELS</span>
              </div>

              <div className="space-y-1 font-mono text-xs">
                <div className="text-[#6e727a] text-[10px]">CURRENT HARVEST</div>
                <div className="text-[#ffffff] font-medium tracking-tight">160 signals / sweep</div>
                <div className="text-[#9281f7] text-[11px] truncate">@verbatim_quotes</div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-[#292d30] text-[10px] font-mono text-[#6e727a]">
                <span>ZERO-AUTH</span>
                <span className="h-1 w-1 rounded-full bg-[#9281f7]" />
                <span>AGENT-READY</span>
              </div>
            </div>

            {/* Ghost background plane */}
            <div className="absolute inset-0 -z-10 border border-[#292d30]/40 rounded-[24px] rotate-[-6deg] pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Main Search & Ingestion Console (16px Card, 1px #292d30 Border) */}
      <div className="p-6 sm:p-8 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-6">
        {/* Execution Mode Selector Bar */}
        <div className="flex items-center justify-between border-b border-[#292d30] pb-4">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-[#a1a4a5] uppercase tracking-wider mr-1">
              Mode:
            </span>

            {/* Focus Mode Pill */}
            <button
              type="button"
              onClick={() => setExecutionMode("focus")}
              className={`px-3 py-1.5 rounded-[6px] text-xs font-mono flex items-center gap-2 transition-all ${
                executionMode === "focus"
                  ? "bg-[#000000] text-[#ffffff] border border-[#ffffff]"
                  : "bg-[#000000] text-[#a1a4a5] border border-[#292d30] hover:text-[#ffffff]"
              }`}
            >
              <Layers className="h-3.5 w-3.5" />
              <span>Focus Mode (Silent Background)</span>
            </button>

            {/* Live Browser Mode Pill */}
            <button
              type="button"
              onClick={() => setExecutionMode("browser")}
              className={`px-3 py-1.5 rounded-[6px] text-xs font-mono flex items-center gap-2 transition-all ${
                executionMode === "browser"
                  ? "bg-[#000000] text-[#ffffff] border border-[#3b9eff] shadow-subtle"
                  : "bg-[#000000] text-[#a1a4a5] border border-[#292d30] hover:text-[#ffffff]"
              }`}
            >
              <Monitor className="h-3.5 w-3.5 text-[#9281f7]" />
              <span>Live Browser Mode (Agent In Control)</span>
              <span className="h-1.5 w-1.5 rounded-full bg-[#3ad389] animate-pulse" />
            </button>
          </div>

          <span className="hidden sm:inline-block text-[11px] font-mono text-[#6e727a]">
            {executionMode === "browser"
              ? "Spawns visible Chromium session + live screencast"
              : "Parallel headless APIs, stays quietly on site"}
          </span>
        </div>

        {/* Search Query Input */}
        <form onSubmit={handleFormSubmit} className="space-y-4">
          <div className="relative flex flex-col sm:flex-row items-stretch gap-2.5">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-[#6e727a]" />
              <input
                type="text"
                placeholder="Topic, product, or competitor debate (e.g. 'Supabase vs Firebase', 'Doom Day', 'Messi vs Ronaldo')..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={isLoading}
                className="w-full pl-11 pr-4 py-3.5 bg-[#000000] border border-[#292d30] rounded-[6px] text-sm text-[#ffffff] placeholder-[#464a4d] focus:outline-none focus:border-[#ffffff] transition-colors font-sans"
              />
            </div>

            {/* Primary Action Button */}
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="px-6 py-3.5 rounded-[6px] bg-[#3b9eff] hover:bg-[#3b9eff]/90 text-[#ffffff] font-sans font-medium text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin text-[#ffffff]" />
                  <span>Synthesizing...</span>
                </>
              ) : (
                <>
                  <span>
                    {executionMode === "browser" ? "Launch Browser Agent" : "Begin Sweep"}
                  </span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </div>

          {error && (
            <div className="p-3 rounded-[6px] border border-[#ff9592]/30 bg-[#000000] text-xs font-mono text-[#ff9592] flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-[#ff9592]" />
              <span>{error}</span>
            </div>
          )}
        </form>

        {/* Configuration Bar (Channels & Sample Size) */}
        <div className="space-y-4 pt-4 border-t border-[#292d30]">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="text-xs font-mono uppercase tracking-wider text-[#a1a4a5]">
                Harvest Channels ({channels.length}/6)
              </span>
              <button
                type="button"
                onClick={() => setIsSettingsOpen(true)}
                className="inline-flex items-center gap-1.5 text-xs font-sans text-[#a1a4a5] hover:text-[#ffffff] transition-colors"
              >
                <Key className="h-3 w-3 text-[#9281f7]" />
                <span className="underline underline-offset-2">Auth & Cookies</span>
              </button>
            </div>

            {/* Sample Size Dropdown */}
            <div className="flex items-center gap-2 text-xs font-mono">
              <Sliders className="h-3.5 w-3.5 text-[#6e727a]" />
              <span className="text-[#a1a4a5]">Sample Size:</span>
              <select
                value={sampleSize}
                onChange={(e) => setSampleSize(Number(e.target.value))}
                className="bg-[#000000] border border-[#292d30] rounded-[6px] px-2.5 py-1 text-xs text-[#ffffff] font-mono focus:outline-none focus:border-[#ffffff]"
              >
                <option value={40}>40 Signals (Fast)</option>
                <option value={80}>80 Signals (Recommended)</option>
                <option value={120}>120 Signals (Deep Sweep)</option>
                <option value={160}>160 Signals (Exhaustive)</option>
              </select>
            </div>
          </div>

          {/* 7 Channel Toggles */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
            {AVAILABLE_CHANNELS.map((ch) => {
              const Icon = ch.icon;
              const isSelected = channels.includes(ch.id);

              return (
                <button
                  key={ch.id}
                  type="button"
                  onClick={() => toggleChannel(ch.id)}
                  className={`flex items-center justify-between py-2 px-3 rounded-[6px] border text-xs font-mono transition-all ${
                    isSelected
                      ? "bg-[#000000] border-[#ffffff] text-[#ffffff]"
                      : "bg-[#000000] border-[#292d30] text-[#6e727a] hover:border-[#464a4d] hover:text-[#a1a4a5]"
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <Icon className="h-3.5 w-3.5 shrink-0" />
                    <span className="truncate">{ch.label}</span>
                  </div>
                  <span
                    className={`h-1.5 w-1.5 rounded-full shrink-0 ${
                      isSelected ? "bg-[#3ad389]" : "bg-[#292d30]"
                    }`}
                  />
                </button>
              );
            })}
          </div>

          {/* Optional targeted subreddits */}
          {channels.includes("reddit") && (
            <div className="pt-2 flex flex-col sm:flex-row sm:items-center gap-2 text-xs font-mono text-[#a1a4a5]">
              <span className="shrink-0 text-[#6e727a]">Target Subreddits (optional):</span>
              <input
                type="text"
                value={subreddits}
                onChange={(e) => setSubreddits(e.target.value)}
                placeholder="webdev, technology, programming (comma-separated)"
                className="w-full sm:max-w-md px-3 py-1 bg-[#000000] border border-[#292d30] rounded-[6px] text-xs text-[#ffffff] placeholder-[#464a4d] focus:outline-none focus:border-[#ffffff]"
              />
            </div>
          )}
        </div>
      </div>

      {/* Human-In-The-Loop Approval Modal */}
      <BrowserApprovalModal
        isOpen={isApprovalOpen}
        query={query}
        onClose={() => setIsApprovalOpen(false)}
        onApprove={() => doLaunch("browser", true)}
        onFallbackFocus={() => doLaunch("focus", false)}
      />

      <ChannelSettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
    </div>
  );
}
