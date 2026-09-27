"use client";

import React, { useState, useEffect } from "react";
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
  Globe,
  BookOpen,
  TrendingUp,
  Tv,
  Briefcase,
  Activity,
  CheckCircle2,
  CheckSquare,
  Square,
  HelpCircle
} from "lucide-react";
import { startResearch } from "@/lib/api";
import { ChannelSettingsModal } from "@/components/ChannelSettingsModal";
import { BrowserApprovalModal } from "@/components/BrowserApprovalModal";
import { DiagnosticDoctorModal } from "@/components/DiagnosticDoctorModal";

export interface ChannelDef {
  id: string;
  label: string;
  icon: any;
  domain: string;
  category: "dev" | "social" | "video" | "web" | "biz_fin";
  badge: string;
  tier: number;
}

const ALL_AVAILABLE_CHANNELS: ChannelDef[] = [
  // Developer & Code
  { id: "hackernews", label: "Hacker News", icon: Terminal, domain: "news.ycombinator.com", category: "dev", badge: "Zero-Auth", tier: 0 },
  { id: "github", label: "GitHub Issues", icon: Github, domain: "github.com", category: "dev", badge: "Zero-Auth", tier: 0 },
  { id: "v2ex", label: "V2EX Community", icon: MessageSquare, domain: "v2ex.com", category: "dev", badge: "Zero-Auth", tier: 0 },
  // Social & Community
  { id: "reddit", label: "Reddit", icon: MessageSquare, domain: "reddit.com", category: "social", badge: "Zero-Auth", tier: 0 },
  { id: "twitter", label: "Twitter / X", icon: Twitter, domain: "x.com", category: "social", badge: "Session/Key", tier: 1 },
  { id: "facebook", label: "Facebook Groups", icon: Users, domain: "facebook.com", category: "social", badge: "Zero-Auth", tier: 0 },
  // Video & Multimedia
  { id: "youtube", label: "YouTube Transcripts", icon: Youtube, domain: "youtube.com", category: "video", badge: "Zero-Auth", tier: 0 },
  { id: "bilibili", label: "Bilibili Reviews", icon: Tv, domain: "bilibili.com", category: "video", badge: "Zero-Auth", tier: 0 },
  // Web & Semantic Search
  { id: "google", label: "Google / Web", icon: Globe, domain: "google.com", category: "web", badge: "Zero-Auth", tier: 0 },
  { id: "web", label: "Jina Web Reader", icon: BookOpen, domain: "r.jina.ai", category: "web", badge: "Markdown", tier: 0 },
  { id: "exa", label: "Exa Neural Search", icon: Sparkles, domain: "exa.ai", category: "web", badge: "Semantic", tier: 1 },
  // Business & Finance
  { id: "linkedin", label: "LinkedIn B2B", icon: Briefcase, domain: "linkedin.com", category: "biz_fin", badge: "B2B Pulse", tier: 0 },
  { id: "xueqiu", label: "Xueqiu Finance", icon: TrendingUp, domain: "xueqiu.com", category: "biz_fin", badge: "Market Sentiment", tier: 0 },
];

const RECOMMENDED_CHANNELS = ["google", "reddit", "youtube", "twitter", "hackernews", "v2ex", "github"];

export function QueryLauncher() {
  const router = useRouter();

  const [query, setQuery] = useState("");
  const [channels, setChannels] = useState<string[]>(RECOMMENDED_CHANNELS);
  const [sampleSize, setSampleSize] = useState<number>(80);
  const [subreddits, setSubreddits] = useState<string>("");
  const [executionMode, setExecutionMode] = useState<"focus" | "browser">("focus");
  const [channelFilter, setChannelFilter] = useState<string>("all");
  
  // Detect if running on Vercel (where browser agent is not supported)
  const [isVercel, setIsVercel] = useState(false);
  useEffect(() => {
    if (typeof window !== "undefined") {
      setIsVercel(
        process.env.NEXT_PUBLIC_VERCEL === "1" || 
        window.location.hostname.includes("vercel.app")
      );
    }
  }, []);
  
  const [isApprovalOpen, setIsApprovalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isDoctorOpen, setIsDoctorOpen] = useState(false);

  const toggleChannel = (channelId: string) => {
    if (channels.includes(channelId)) {
      setChannels(channels.filter((c) => c !== channelId));
    } else {
      setChannels([...channels, channelId]);
    }
  };

  const selectAllChannels = () => {
    setChannels(ALL_AVAILABLE_CHANNELS.map(c => c.id));
  };

  const selectRecommendedChannels = () => {
    setChannels(RECOMMENDED_CHANNELS);
  };

  const clearAllChannels = () => {
    setChannels([]);
  };

  const selectOnlyChannel = (channelId: string) => {
    setChannels([channelId]);
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    if (channels.length === 0) {
      setError("Please select at least one harvest source channel (e.g. YouTube, Reddit, Google) before launching research.");
      return;
    }

    if (executionMode === "browser") {
      setIsApprovalOpen(true);
    } else {
      doLaunch("focus", false);
    }
  };

  const doLaunch = async (mode: "focus" | "browser", approved: boolean) => {
    if (channels.length === 0) {
      setError("Please select at least one harvest source channel before launching research.");
      return;
    }

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

  const displayedChannels = channelFilter === "all"
    ? ALL_AVAILABLE_CHANNELS
    : ALL_AVAILABLE_CHANNELS.filter(c => c.category === channelFilter);

  return (
    <div className="w-full space-y-12">
      {/* Editorial Hero Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center pt-4 sm:pt-8">
        <div className="lg:col-span-8 space-y-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-transparent border border-[#292d30] text-xs font-sans text-[#f0f0f0] hover:border-[#ffffff]/50 transition-colors">
            <span className="h-1.5 w-1.5 rounded-full bg-[#9281f7]" />
            <span className="font-mono text-[11px] text-[#9281f7]">v2.0</span>
            <span className="text-[#a1a4a5]">•</span>
            <span>13 Intelligence Channels • Agent Reach Core • Live CDP</span>
            <ChevronRight className="h-3 w-3 text-[#a1a4a5]" />
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-serif font-normal text-[#ffffff] tracking-tight leading-[1.08]">
            Discover real customer pain before writing a single line of code.
          </h1>

          <p className="text-base sm:text-lg font-sans text-[#a1a4a5] max-w-2xl leading-relaxed">
            Autonomous multi-channel research harvesting verbatim friction signals across Reddit, Twitter, Hacker News, YouTube transcripts, GitHub, V2EX, and B2B networks. Grouped by mathematical density clustering into actionable PRDs and pitch decks.
          </p>
        </div>

        {/* 3D Wireframe Visual Hero Cue */}
        <div className="lg:col-span-4 hidden lg:flex justify-center items-center">
          <div className="w-64 h-64 rounded-[24px] border border-[#292d30] bg-[#000000] p-6 relative flex flex-col justify-between shadow-subtle group hover:border-[#9281f7]/50 transition-colors">
            <div className="flex items-center justify-between text-xs font-mono text-[#a1a4a5]">
              <span>CLUSTER MATRIX</span>
              <span className="text-[#3ad389] flex items-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-[#3ad389] animate-pulse" />
                Live Doctor
              </span>
            </div>

            <div className="space-y-2 font-mono text-xs text-[#6e727a]">
              <div className="flex justify-between">
                <span>// Channels Active</span>
                <span className="text-[#ffffff]">{channels.length} Selected</span>
              </div>
              <div className="flex justify-between">
                <span>// Algolia + V2EX</span>
                <span className="text-[#3ad389]">Zero-Auth</span>
              </div>
              <div className="flex justify-between">
                <span>// Jina Reader</span>
                <span className="text-[#3b9eff]">r.jina.ai</span>
              </div>
              <div className="flex justify-between">
                <span>// Office Decks</span>
                <span className="text-[#ff9592]">16:9 .pptx</span>
              </div>
            </div>

            <div className="pt-3 border-t border-[#292d30] flex items-center justify-between text-[11px] font-mono text-[#9281f7]">
              <span>DBSCAN Epsilon 0.42</span>
              <span>100% Verifiable</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Research Console Card */}
      <div className="w-full rounded-[16px] bg-[#000000] border border-[#292d30] p-6 sm:p-8 space-y-6 shadow-subtle">
        {/* Mode Selector & Diagnostics Pill Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#292d30] pb-4">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono uppercase tracking-wider text-[#a1a4a5] mr-2">
              Execution Mode:
            </span>
            <div className="inline-flex rounded-[6px] border border-[#292d30] p-0.5 bg-[#000000]">
              <button
                type="button"
                onClick={() => setExecutionMode("focus")}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-[4px] text-xs font-sans font-medium transition-all ${
                  executionMode === "focus"
                    ? "bg-[#ffffff] text-[#000000] shadow-sm"
                    : "text-[#a1a4a5] hover:text-[#ffffff]"
                }`}
              >
                <Layers className="h-3.5 w-3.5" />
                <span>Focus (Fast APIs)</span>
              </button>
              <button
                type="button"
                onClick={() => {
                  if (isVercel) return;
                  setExecutionMode("browser");
                }}
                disabled={isVercel}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-[4px] text-xs font-sans font-medium transition-all opacity-50 ${ 
                  isVercel
                    ? "cursor-not-allowed text-[#464a4d]"
                    : executionMode === "browser"
                    ? "bg-[#ffffff] text-[#000000] shadow-sm"
                    : "text-[#a1a4a5] hover:text-[#ffffff]"
                }`}
                title={isVercel ? "Live Browser Agent requires a local browser (not available on Vercel)" : ""}
              >
                <Monitor className="h-3.5 w-3.5" />
                <span>Live Browser Stream</span>
                {isVercel && <HelpCircle className="h-3 w-3 opacity-50" />}
              </button>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* System Doctor Diagnostic Button */}
            <button
              type="button"
              onClick={() => setIsDoctorOpen(true)}
              className="inline-flex items-center gap-1.5 text-xs font-mono text-[#3ad389] hover:text-[#ffffff] bg-[#3ad389]/10 border border-[#3ad389]/30 hover:border-[#3ad389] px-2.5 py-1 rounded-[6px] transition-colors"
              title="Inspect upstream channel reachability and failover chains"
            >
              <Activity className="h-3.5 w-3.5" />
              <span>Diagnostic Doctor</span>
            </button>

            {/* Auth & Cookies Modal Trigger */}
            <button
              type="button"
              onClick={() => setIsSettingsOpen(true)}
              className="inline-flex items-center gap-1.5 text-xs font-mono text-[#a1a4a5] hover:text-[#ffffff] bg-[#000000] border border-[#292d30] hover:border-[#ffffff]/40 px-2.5 py-1 rounded-[6px] transition-colors"
            >
              <Key className="h-3 w-3 text-[#9281f7]" />
              <span>Platform Auth</span>
            </button>
          </div>
        </div>

        {/* Search Query Input */}
        <form onSubmit={handleFormSubmit} className="space-y-4">
          <div className="relative flex flex-col sm:flex-row items-stretch gap-2.5">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-[#6e727a]" />
              <input
                type="text"
                placeholder="Topic, product, or competitor debate (e.g. 'Supabase vs Firebase', 'Next.js App Router', 'Linear vs Jira')..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={isLoading}
                className="w-full pl-11 pr-4 py-3.5 bg-[#000000] border border-[#292d30] rounded-[6px] text-sm text-[#ffffff] placeholder-[#464a4d] focus:outline-none focus:border-[#ffffff] transition-colors font-sans"
              />
            </div>

            {/* Primary Action Button */}
            <button
              type="submit"
              disabled={isLoading || !query.trim() || channels.length === 0}
              className={`px-6 py-3.5 rounded-[6px] font-sans font-medium text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-40 disabled:cursor-not-allowed shrink-0 ${
                channels.length === 0
                  ? "bg-[#292d30] text-[#a1a4a5]"
                  : channels.length === 1 && channels[0] === "youtube"
                  ? "bg-[#ff6465] hover:bg-[#ff6465]/90 text-[#ffffff] shadow-md shadow-[#ff6465]/20"
                  : "bg-[#3b9eff] hover:bg-[#3b9eff]/90 text-[#ffffff]"
              }`}
              title={channels.length === 0 ? "Please select at least 1 harvest source" : `Harvest from: ${channels.join(", ")}`}
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin text-[#ffffff]" />
                  <span>Synthesizing...</span>
                </>
              ) : (
                <>
                  <span>
                    {channels.length === 0
                      ? "Select Channel to Sweep"
                      : executionMode === "browser"
                      ? `Launch Browser Agent (${channels.length} ${channels.length === 1 ? "Channel" : "Channels"})`
                      : channels.length === 1
                      ? `Sweep 1 Channel: ${ALL_AVAILABLE_CHANNELS.find((c) => c.id === channels[0])?.label || channels[0]}`
                      : `Begin Sweep (${channels.length} Channels)`}
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

        {/* Channels Configuration & Category Filter */}
        <div className="space-y-4 pt-4 border-t border-[#292d30]">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-mono uppercase tracking-wider text-[#a1a4a5]">
                Harvest Sources ({channels.length}/{ALL_AVAILABLE_CHANNELS.length})
              </span>
              <span className="text-[#6e727a]">•</span>
              <button
                type="button"
                onClick={selectAllChannels}
                className="text-[11px] font-mono text-[#9281f7] hover:underline"
              >
                All 13
              </button>
              <span className="text-[#6e727a]">•</span>
              <button
                type="button"
                onClick={selectRecommendedChannels}
                className="text-[11px] font-mono text-[#a1a4a5] hover:text-[#ffffff]"
              >
                Recommended (7)
              </button>
              <span className="text-[#6e727a]">•</span>
              <button
                type="button"
                onClick={() => setChannels(["youtube"])}
                className={`text-[11px] font-mono px-2 py-0.5 rounded border transition-colors ${
                  channels.length === 1 && channels[0] === "youtube"
                    ? "bg-[#ff6465]/20 border-[#ff6465]/40 text-[#ff6465] font-bold"
                    : "border-[#292d30] text-[#a1a4a5] hover:text-[#ff6465] hover:border-[#ff6465]/40"
                }`}
                title="Target ONLY YouTube Transcripts"
              >
                YouTube Only
              </button>
              <span className="text-[#6e727a]">•</span>
              <button
                type="button"
                onClick={clearAllChannels}
                className="text-[11px] font-mono text-[#ff9592] hover:underline"
              >
                Clear All
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

          {/* Active Channels Chips & Visibility Bar */}
          <div className="flex flex-wrap items-center gap-1.5 p-2 rounded-[8px] bg-[#121418] border border-[#20232a]">
            <span className="text-[11px] font-mono text-[#6e727a] mr-1 flex items-center gap-1">
              <span>Active Scope:</span>
              <span className={`h-1.5 w-1.5 rounded-full ${channels.length > 0 ? "bg-[#3ad389]" : "bg-[#ff9592]"}`} />
            </span>
            {channels.length === 0 ? (
              <span className="text-[11px] font-mono text-[#ff9592]">
                No sources selected. Click a channel card below or use [ONLY] to target a single source.
              </span>
            ) : (
              channels.map((cid) => {
                const def = ALL_AVAILABLE_CHANNELS.find((c) => c.id === cid);
                return (
                  <span
                    key={cid}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded-[4px] bg-[#1a1c23] border border-[#292d30] text-[11px] font-mono text-[#ffffff]"
                  >
                    <span>{def?.label || cid}</span>
                    <button
                      type="button"
                      onClick={() => setChannels(channels.filter((c) => c !== cid))}
                      className="text-[#6e727a] hover:text-[#ff9592] font-bold ml-0.5"
                      title={`Remove ${def?.label || cid}`}
                    >
                      ×
                    </button>
                  </span>
                );
              })
            )}
          </div>

          {/* Category Filter Pills & Scope Helper */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#20232a] pb-2">
            <div className="flex items-center gap-1.5 overflow-x-auto">
              {[
                { id: "all", label: "All Sources" },
                { id: "dev", label: "Developer & Code" },
                { id: "social", label: "Social & Forums" },
                { id: "video", label: "Video Reviews" },
                { id: "web", label: "Web & Search" },
                { id: "biz_fin", label: "B2B & Finance" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setChannelFilter(tab.id)}
                  className={`px-2.5 py-1 rounded-full text-[11px] font-mono transition-colors whitespace-nowrap ${
                    channelFilter === tab.id
                      ? "bg-[#292d30] text-[#ffffff] font-medium"
                      : "text-[#6e727a] hover:text-[#a1a4a5]"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {channelFilter !== "all" && (
              <button
                type="button"
                onClick={() => {
                  const catChannelIds = ALL_AVAILABLE_CHANNELS.filter(c => c.category === channelFilter).map(c => c.id);
                  setChannels(catChannelIds);
                }}
                className="self-start sm:self-auto px-2.5 py-1 rounded-[6px] bg-[#9281f7]/15 border border-[#9281f7]/35 hover:bg-[#9281f7]/25 text-[11px] font-mono text-[#9281f7] transition-all flex items-center gap-1 shrink-0"
                title={`Scope active sweep to only the ${displayedChannels.length} channels in this category`}
              >
                <span>Select Only {channelFilter === "video" ? "Video Reviews (YouTube & Bilibili)" : `${displayedChannels.length} Category Channels`}</span>
              </button>
            )}
          </div>

          {/* 13 Channel Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
            {displayedChannels.map((ch) => {
              const Icon = ch.icon;
              const isSelected = channels.includes(ch.id);

              return (
                <div
                  key={ch.id}
                  onClick={() => toggleChannel(ch.id)}
                  className={`flex flex-col justify-between p-2.5 rounded-[8px] border text-left transition-all cursor-pointer ${
                    isSelected
                      ? "bg-[#0e0e12] border-[#ffffff] text-[#ffffff] shadow-sm"
                      : "bg-[#000000] border-[#292d30] text-[#6e727a] hover:border-[#464a4d] hover:text-[#a1a4a5]"
                  }`}
                >
                  <div className="flex items-center justify-between w-full mb-1.5">
                    <div className="flex items-center gap-1.5">
                      <Icon className="h-3.5 w-3.5 shrink-0" />
                      <span className="text-xs font-mono truncate font-medium">
                        {ch.label}
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          selectOnlyChannel(ch.id);
                        }}
                        className={`px-1.5 py-0.5 rounded text-[9px] font-mono transition-all font-semibold ${
                          isSelected && channels.length === 1
                            ? "bg-[#3ad389] text-[#000000] ring-1 ring-[#3ad389]"
                            : "bg-[#181a20] border border-[#292d30] text-[#a1a4a5] hover:bg-[#ffffff] hover:text-[#000000]"
                        }`}
                        title={`Scope research to ONLY ${ch.label} (deselects all other channels)`}
                      >
                        {isSelected && channels.length === 1 ? "✓ ONLY" : "ONLY"}
                      </button>
                      <span
                        className={`h-2 w-2 rounded-full shrink-0 ${
                          isSelected ? "bg-[#3ad389]" : "bg-[#292d30]"
                        }`}
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-between w-full text-[10px] font-mono text-[#6e727a]">
                    <span className="truncate">{ch.domain}</span>
                    <span className={`px-1 py-0.2 rounded text-[9px] ${
                      ch.tier === 0 ? "text-[#3ad389]" : "text-[#3b9eff]"
                    }`}>
                      {ch.badge}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Optional targeted subreddits if Reddit selected */}
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

      {/* Channel Auth & Cookies Modal */}
      <ChannelSettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />

      {/* Diagnostic Doctor Telemetry Modal */}
      <DiagnosticDoctorModal
        isOpen={isDoctorOpen}
        onClose={() => setIsDoctorOpen(false)}
      />
    </div>
  );
}
