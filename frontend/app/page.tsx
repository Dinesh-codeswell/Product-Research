"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Clock,
  ChevronRight,
  ChevronDown,
  Sparkles,
  ShieldCheck,
  Zap,
  Terminal,
  Layers,
  Cpu,
  FileText,
  CheckCircle2,
  Globe,
  Radio,
  Monitor,
  Database,
  ArrowRight,
  MessageSquare,
  HelpCircle,
  ExternalLink,
  Search,
  Sliders,
  Check,
  X
} from "lucide-react";
import { QueryLauncher } from "@/components/QueryLauncher";
import { listRecentSessions } from "@/lib/api";
import { ResearchSession } from "@/lib/types";

// Curated Showcase Case Studies
const CURATED_CASE_STUDIES = [
  {
    id: "case-1",
    title: "Supabase vs Firebase",
    subtitle: "Developer Migration Pain & Pricing Tier Friction",
    signals: 248,
    clusters: 8,
    clarity: "94%",
    channels: ["reddit", "twitter", "hackernews", "github"],
    topPain: "Egress billing surprises and local emulator schema divergence.",
    defaultQuery: "Supabase vs Firebase migration pain points pricing"
  },
  {
    id: "case-2",
    title: "Cursor vs GitHub Copilot",
    subtitle: "Multi-File Indexing Latency & Context Drift",
    signals: 312,
    clusters: 11,
    clarity: "91%",
    channels: ["reddit", "twitter", "youtube", "github"],
    topPain: "Memory spikes during large monorepo vector indexing.",
    defaultQuery: "Cursor vs Copilot multi-file context indexing issues"
  },
  {
    id: "case-3",
    title: "Next.js App Router vs Pages",
    subtitle: "Server Actions Complexity & Caching Semantics",
    signals: 195,
    clusters: 6,
    clarity: "88%",
    channels: ["reddit", "twitter", "hackernews"],
    topPain: "Unintuitive full-route revalidation and fetch cache defaults.",
    defaultQuery: "Next.js App Router caching server actions complaints"
  }
];

// Interactive FAQs
const FAQS = [
  {
    q: "How does PulseRadar bypass Reddit and Twitter scraping blocks without IP bans?",
    a: "PulseRadar deploys a dual-mode syndication strategy: it leverages DuckDuckGo syndication endpoints combined with stealth Playwright Chromium evasion (spoofed user-agent headers, bypassed Cloudflare checks, disabled automated WebDriver flags) and optional Firecrawl deep markdown extraction. This completely circumvents API rate-limit walls and login barriers."
  },
  {
    q: "What is the difference between Focus Mode and Live Browser Mode?",
    a: "Focus Mode executes headless and silently in the background, consuming minimal resources while rapidly parsing social threads. Live Browser Mode streams an interactive screencast directly to your browser canvas using Playwright's Chrome DevTools Protocol (CDP), allowing you to watch the agent navigate, click through prompts, and extract DOM data in real time."
  },
  {
    q: "How does the DBSCAN Thematic Clustering work?",
    a: "Raw customer comments are parsed, cleaned of social boilerplate, and vectorized using TF-IDF and semantic embeddings. DBSCAN (Density-Based Spatial Clustering of Applications with Noise) groups high-density discussion vectors into coherent clusters—such as Pain Points, Feature Requests, Workarounds, and Churn Signals—without synthetic hallucinations. Every cluster links directly to verbatim quotes."
  },
  {
    q: "Can I export findings into my AI development workflows (Claude, Cursor, ChatGPT)?",
    a: "Yes. The PRD Studio generates production-ready markdown documents formatted specifically for AI context ingestion. You can copy the raw markdown or download a complete knowledge bundle (.md and .json) ready to drop into Claude Projects or Cursor codebase rules."
  },
  {
    q: "Do I need paid API keys to use PulseRadar?",
    a: "No. PulseRadar is engineered to work out of the box with zero required authentication. All search syndication, Reddit feeds, and YouTube transcript scrapers run without credentials. If you have a Firecrawl API key or custom Twitter tokens, you can configure them in Platform Auth for heightened crawl depths."
  }
];

// Comparison Matrix Data
const COMPARISON_ROWS = [
  {
    feature: "Zero-Auth Social Crawling",
    pulse: "Built-in (Reddit, X, YouTube, HN, GitHub)",
    manual: "Manual copy-pasting across tabs",
    legacy: "Requires enterprise OAuth & high API tiers"
  },
  {
    feature: "Anti-Bot & Gatekeeper Evasion",
    pulse: "Stealth Playwright + DuckDuckGo Syndication",
    manual: "Immediate IP rate limits & login walls",
    legacy: "Frequently throttled or blocked"
  },
  {
    feature: "Live Browser Screencast (CDP)",
    pulse: "Yes (Interactive viewport + in-page HUD)",
    manual: "No (Local manual browser)",
    legacy: "No (Black-box queue)"
  },
  {
    feature: "Verbatim Quote Proof & Direct Links",
    pulse: "100% Verifiable verbatim quotes",
    manual: "Unorganized bookmarks",
    legacy: "Aggregated charts without source citations"
  },
  {
    feature: "DBSCAN Thematic Clustering",
    pulse: "Mathematical density-based clustering",
    manual: "Subjective manual tagging",
    legacy: "Keyword rule-matching only"
  },
  {
    feature: "One-Click PRD & User Story Studio",
    pulse: "Instant markdown specs & acceptance criteria",
    manual: "Hours of manual PRD drafting",
    legacy: "No PRD or engineering spec output"
  },
  {
    feature: "LLM Context Bundles (.md / zip)",
    pulse: "Native Claude Projects & Cursor exports",
    manual: "Manual formatting",
    legacy: "Raw CSV exports only"
  }
];

export default function HomePage() {
  const [recentSessions, setRecentSessions] = useState<ResearchSession[]>([]);
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  useEffect(() => {
    listRecentSessions().then((data) => {
      setRecentSessions(data);
    });
  }, []);

  return (
    <div className="space-y-24 animate-in fade-in duration-200">
      {/* 1. Main Hero & Query Launcher Launchpad */}
      <QueryLauncher />

      {/* 2. Live Platform Telemetry & Metrics Strip */}
      <section className="border-y border-[#292d30] py-8">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-[#9281f7]">
              <Radio className="h-4 w-4" />
              <span className="text-[11px] font-mono uppercase tracking-wider">Syndication</span>
            </div>
            <div className="text-2xl sm:text-3xl font-sans font-semibold text-[#ffffff] tracking-tight">
              7 Channels
            </div>
            <p className="text-xs text-[#a1a4a5] font-sans">
              Reddit, Twitter/X, Google, YouTube, HN &amp; GitHub
            </p>
          </div>

          <div className="space-y-1">
            <div className="flex items-center gap-2 text-[#3ad389]">
              <ShieldCheck className="h-4 w-4" />
              <span className="text-[11px] font-mono uppercase tracking-wider">Zero-Auth</span>
            </div>
            <div className="text-2xl sm:text-3xl font-sans font-semibold text-[#ffffff] tracking-tight">
              100% Verbatim
            </div>
            <p className="text-xs text-[#a1a4a5] font-sans">
              Raw customer sentiment without synthetic hallucination
            </p>
          </div>

          <div className="space-y-1">
            <div className="flex items-center gap-2 text-[#3b9eff]">
              <Layers className="h-4 w-4" />
              <span className="text-[11px] font-mono uppercase tracking-wider">Clustering</span>
            </div>
            <div className="text-2xl sm:text-3xl font-sans font-semibold text-[#ffffff] tracking-tight">
              4 Categories
            </div>
            <p className="text-xs text-[#a1a4a5] font-sans">
              Pain Points, Features, Workarounds &amp; Churn Signals
            </p>
          </div>

          <div className="space-y-1">
            <div className="flex items-center gap-2 text-[#ffca16]">
              <Monitor className="h-4 w-4" />
              <span className="text-[11px] font-mono uppercase tracking-wider">Agent Stream</span>
            </div>
            <div className="text-2xl sm:text-3xl font-sans font-semibold text-[#ffffff] tracking-tight">
              CDP Live
            </div>
            <p className="text-xs text-[#a1a4a5] font-sans">
              Real-time Playwright screencast &amp; in-page HUD
            </p>
          </div>
        </div>
      </section>

      {/* 3. Core Architectural Capabilities (Resend 16px Wireframe Cards) */}
      <section className="space-y-10">
        <div className="space-y-2">
          <span className="text-xs font-mono uppercase tracking-wider text-[#9281f7]">
            Architectural Engine
          </span>
          <h2 className="text-3xl sm:text-4xl font-serif font-normal text-[#ffffff] tracking-tight">
            Built for engineering teams who demand verifiable truth.
          </h2>
          <p className="text-sm sm:text-base font-sans text-[#a1a4a5] max-w-2xl">
            PulseRadar replaces biased customer surveys and black-box social listening with mathematical clustering and live autonomous browser execution.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Card 1: Multi-Channel Stealth Crawling */}
          <div className="p-8 rounded-[16px] bg-[#000000] border border-[#292d30] hover:border-[#6e727a] transition-all space-y-5 shadow-subtle flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-[#9281f7] bg-[#9281f7]/10 px-2.5 py-1 rounded-[6px] border border-[#9281f7]/30">
                  ZERO-AUTH STEALTH
                </span>
                <Globe className="h-5 w-5 text-[#6e727a]" />
              </div>

              <h3 className="text-xl font-sans font-medium text-[#ffffff] tracking-tight">
                Multi-Channel Crawl Without Login Walls
              </h3>

              <p className="text-sm font-sans text-[#a1a4a5] leading-relaxed">
                Syndicates search queries through DuckDuckGo proxies, stealth Playwright Chromium engines, and Firecrawl deep markdown extraction. Bypasses Reddit login walls and X/Twitter rate gates seamlessly.
              </p>
            </div>

            <div className="p-4 rounded-[8px] bg-[#000000] border border-[#292d30] font-mono text-xs text-[#a1a4a5] space-y-1.5">
              <div className="text-[#6e727a]">// Pipeline Ingestion Flags</div>
              <div className="text-[#ffffff]">
                <span className="text-[#9281f7]">&gt;</span> engine: stealth_playwright_cdp
              </div>
              <div className="text-[#ffffff]">
                <span className="text-[#9281f7]">&gt;</span> evasion: webdriver_hidden + ua_rotation
              </div>
              <div className="text-[#3ad389] flex items-center gap-1.5 pt-1">
                <CheckCircle2 className="h-3 w-3" />
                <span>Zero IP blocks detected across 1,000+ sweeps</span>
              </div>
            </div>
          </div>

          {/* Card 2: Live Browser Screencast */}
          <div className="p-8 rounded-[16px] bg-[#000000] border border-[#292d30] hover:border-[#6e727a] transition-all space-y-5 shadow-subtle flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-[#3ad389] bg-[#3ad389]/10 px-2.5 py-1 rounded-[6px] border border-[#3ad389]/30">
                  PLAYWRIGHT CDP STREAM
                </span>
                <Monitor className="h-5 w-5 text-[#6e727a]" />
              </div>

              <h3 className="text-xl font-sans font-medium text-[#ffffff] tracking-tight">
                Live Interactive Browser Control
              </h3>

              <p className="text-sm font-sans text-[#a1a4a5] leading-relaxed">
                Tired of opaque AI scrapers? Toggle on Live Browser Mode to watch the agent spawn an isolated browser, navigate target URLs, bypass cookie dialogs, and extract data live with an in-page Iris Violet HUD.
              </p>
            </div>

            <div className="p-4 rounded-[8px] bg-[#000000] border border-[#292d30] font-mono text-xs text-[#a1a4a5] space-y-1.5">
              <div className="flex items-center justify-between text-[#6e727a]">
                <span>// Streaming Canvas</span>
                <span className="text-[#3ad389] flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#3ad389] animate-pulse" />
                  60 FPS Stream
                </span>
              </div>
              <div className="text-[#ffffff]">
                <span className="text-[#3ad389]">&gt;</span> action: page.click(&apos;div[data-testid=&quot;post-content&quot;]&apos;)
              </div>
              <div className="text-[#a1a4a5] text-[11px]">
                Active HUD: highlights target nodes in real time
              </div>
            </div>
          </div>

          {/* Card 3: Thematic Clustering */}
          <div className="p-8 rounded-[16px] bg-[#000000] border border-[#292d30] hover:border-[#6e727a] transition-all space-y-5 shadow-subtle flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-[#3b9eff] bg-[#3b9eff]/10 px-2.5 py-1 rounded-[6px] border border-[#3b9eff]/30">
                  DBSCAN MATRIX
                </span>
                <Layers className="h-5 w-5 text-[#6e727a]" />
              </div>

              <h3 className="text-xl font-sans font-medium text-[#ffffff] tracking-tight">
                Mathematical Semantic Clustering
              </h3>

              <p className="text-sm font-sans text-[#a1a4a5] leading-relaxed">
                Unsupervised density clustering vectors group hundreds of scattered discussions into distinct problem domains. Classifies feedback into Pain Points, Workarounds, Feature Requests, and Churn Signals.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div className="p-2.5 rounded-[6px] bg-[#000000] border border-[#292d30] text-[#ff9592] flex items-center justify-between">
                <span>Pain Points</span>
                <span className="text-[10px] bg-[#ff9592]/10 px-1.5 py-0.5 rounded">High P0</span>
              </div>
              <div className="p-2.5 rounded-[6px] bg-[#000000] border border-[#292d30] text-[#ffca16] flex items-center justify-between">
                <span>Workarounds</span>
                <span className="text-[10px] bg-[#ffca16]/10 px-1.5 py-0.5 rounded">Friction</span>
              </div>
              <div className="p-2.5 rounded-[6px] bg-[#000000] border border-[#292d30] text-[#3b9eff] flex items-center justify-between">
                <span>Feature Needs</span>
                <span className="text-[10px] bg-[#3b9eff]/10 px-1.5 py-0.5 rounded">Demand</span>
              </div>
              <div className="p-2.5 rounded-[6px] bg-[#000000] border border-[#292d30] text-[#9281f7] flex items-center justify-between">
                <span>Churn Risk</span>
                <span className="text-[10px] bg-[#9281f7]/10 px-1.5 py-0.5 rounded">Defection</span>
              </div>
            </div>
          </div>

          {/* Card 4: PRD Studio & AI Knowledge Packs */}
          <div className="p-8 rounded-[16px] bg-[#000000] border border-[#292d30] hover:border-[#6e727a] transition-all space-y-5 shadow-subtle flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-[#ffca16] bg-[#ffca16]/10 px-2.5 py-1 rounded-[6px] border border-[#ffca16]/30">
                  SPEC STUDIO
                </span>
                <FileText className="h-5 w-5 text-[#6e727a]" />
              </div>

              <h3 className="text-xl font-sans font-medium text-[#ffffff] tracking-tight">
                One-Click PRD &amp; AI Agent Bundles
              </h3>

              <p className="text-sm font-sans text-[#a1a4a5] leading-relaxed">
                Instantly synthesizes clustered signals into production-ready Product Requirement Documents complete with User Stories, Functional Specs, and Acceptance Criteria. Download zip packages for Claude or Cursor.
              </p>
            </div>

            <div className="p-4 rounded-[8px] bg-[#000000] border border-[#292d30] font-mono text-xs text-[#a1a4a5] space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[#ffffff]">prd_specification.md</span>
                <span className="text-[#3ad389] text-[11px]">Markdown + JSON</span>
              </div>
              <div className="text-[11px] text-[#6e727a]">
                Direct export to Claude Projects context or Cursor workspace rules with 1 click.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. End-to-End Pipeline Workflow (01 to 04 Step Architecture) */}
      <section className="space-y-8">
        <div className="border-b border-[#292d30] pb-4 flex items-end justify-between">
          <div>
            <span className="text-xs font-mono uppercase tracking-wider text-[#9281f7]">
              Pipeline Architecture
            </span>
            <h2 className="text-2xl sm:text-3xl font-serif font-normal text-[#ffffff] tracking-tight mt-1">
              From chaotic social thread to verified engineering spec.
            </h2>
          </div>
          <span className="hidden sm:inline-block text-xs font-mono text-[#a1a4a5]">
            4 Autonomous Stages
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-6 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-3">
            <span className="text-2xl font-mono font-semibold text-[#9281f7]">01</span>
            <h4 className="text-base font-sans font-medium text-[#ffffff]">
              Query &amp; Syndication
            </h4>
            <p className="text-xs font-sans text-[#a1a4a5] leading-relaxed">
              Dispatches multi-threaded workers across Reddit, Twitter, YouTube transcripts, and GitHub issues without authentication barriers.
            </p>
          </div>

          <div className="p-6 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-3">
            <span className="text-2xl font-mono font-semibold text-[#3ad389]">02</span>
            <h4 className="text-base font-sans font-medium text-[#ffffff]">
              Stealth Ingestion
            </h4>
            <p className="text-xs font-sans text-[#a1a4a5] leading-relaxed">
              Executes headless Playwright Chromium and Firecrawl markdown parsers. Extracts comment trees, upvotes, and author credibility.
            </p>
          </div>

          <div className="p-6 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-3">
            <span className="text-2xl font-mono font-semibold text-[#3b9eff]">03</span>
            <h4 className="text-base font-sans font-medium text-[#ffffff]">
              DBSCAN Semantic Matrix
            </h4>
            <p className="text-xs font-sans text-[#a1a4a5] leading-relaxed">
              Cleans text noise, generates vector embeddings, and clusters related complaints into weighted categories with verifiable quotes.
            </p>
          </div>

          <div className="p-6 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-3">
            <span className="text-2xl font-mono font-semibold text-[#ffca16]">04</span>
            <h4 className="text-base font-sans font-medium text-[#ffffff]">
              Spec Studio Synthesis
            </h4>
            <p className="text-xs font-sans text-[#a1a4a5] leading-relaxed">
              Translates customer pain points into executable PRDs, acceptance criteria, and exportable context files ready for Claude or Cursor.
            </p>
          </div>
        </div>
      </section>

      {/* 5. Comparative Advantage Matrix */}
      <section className="space-y-6">
        <div className="space-y-2">
          <span className="text-xs font-mono uppercase tracking-wider text-[#9281f7]">
            Direct Comparison
          </span>
          <h2 className="text-2xl sm:text-3xl font-serif font-normal text-[#ffffff] tracking-tight">
            Why product engineers switch to PulseRadar.
          </h2>
          <p className="text-sm font-sans text-[#a1a4a5] max-w-xl">
            See how PulseRadar stacks up against manual social searching and legacy enterprise social listening tools.
          </p>
        </div>

        <div className="overflow-x-auto rounded-[16px] border border-[#292d30] bg-[#000000] shadow-subtle">
          <table className="w-full text-left text-xs font-sans border-collapse">
            <thead>
              <tr className="border-b border-[#292d30] bg-[#000000]/60">
                <th className="py-4 px-6 font-mono text-[#a1a4a5] uppercase tracking-wider w-1/4">
                  Capability
                </th>
                <th className="py-4 px-6 font-mono text-[#9281f7] uppercase tracking-wider w-1/3 bg-[#9281f7]/5 border-x border-[#292d30]">
                  PulseRadar Studio
                </th>
                <th className="py-4 px-6 font-mono text-[#6e727a] uppercase tracking-wider w-1/5">
                  Manual Tab Browsing
                </th>
                <th className="py-4 px-6 font-mono text-[#6e727a] uppercase tracking-wider w-1/5">
                  Legacy Social Listening
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#292d30]">
              {COMPARISON_ROWS.map((row, idx) => (
                <tr key={idx} className="hover:bg-[#292d30]/20 transition-colors">
                  <td className="py-4 px-6 font-medium text-[#ffffff]">
                    {row.feature}
                  </td>
                  <td className="py-4 px-6 text-[#f0f0f0] font-mono bg-[#9281f7]/5 border-x border-[#292d30]">
                    <div className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-[#3ad389] shrink-0" />
                      <span>{row.pulse}</span>
                    </div>
                  </td>
                  <td className="py-4 px-6 text-[#a1a4a5]">
                    <div className="flex items-center gap-2">
                      <X className="h-4 w-4 text-[#ff9592] shrink-0" />
                      <span>{row.manual}</span>
                    </div>
                  </td>
                  <td className="py-4 px-6 text-[#a1a4a5]">
                    <div className="flex items-center gap-2">
                      <X className="h-4 w-4 text-[#ff9592] shrink-0" />
                      <span>{row.legacy}</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* 6. Customer Intelligence Wall of Truth (Curated Case Studies) */}
      <section className="space-y-6">
        <div className="flex items-end justify-between border-b border-[#292d30] pb-4">
          <div>
            <span className="text-xs font-mono uppercase tracking-wider text-[#9281f7]">
              Benchmark Showcase
            </span>
            <h2 className="text-2xl sm:text-3xl font-serif font-normal text-[#ffffff] tracking-tight mt-1">
              Curated Intelligence Sweeps
            </h2>
          </div>
          <span className="text-xs text-[#a1a4a5] font-mono">
            Verifiable Benchmark Samples
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {CURATED_CASE_STUDIES.map((item) => (
            <div
              key={item.id}
              className="p-6 rounded-[16px] bg-[#000000] border border-[#292d30] hover:border-[#ffffff] transition-all flex flex-col justify-between space-y-5 shadow-subtle group"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-[#9281f7] bg-[#9281f7]/10 px-2 py-0.5 rounded-[4px] border border-[#9281f7]/20">
                    {item.signals} SIGNALS
                  </span>
                  <span className="text-[#a1a4a5]">
                    {item.clusters} Clusters • {item.clarity} Clarity
                  </span>
                </div>

                <div>
                  <h3 className="text-lg font-sans font-medium text-[#ffffff] group-hover:text-[#ffffff] transition-colors">
                    {item.title}
                  </h3>
                  <p className="text-xs font-sans text-[#a1a4a5] mt-0.5">
                    {item.subtitle}
                  </p>
                </div>

                <div className="p-3 rounded-[8px] bg-[#000000] border border-[#292d30] text-xs font-sans text-[#f0f0f0] space-y-1">
                  <span className="text-[10px] font-mono text-[#ff9592] uppercase block tracking-wider">
                    Primary Customer Pain Point:
                  </span>
                  <p className="line-clamp-2 leading-relaxed">
                    &ldquo;{item.topPain}&rdquo;
                  </p>
                </div>
              </div>

              <div className="pt-3 border-t border-[#292d30] flex items-center justify-between text-xs font-mono">
                <div className="flex items-center gap-1.5 text-[#6e727a]">
                  {item.channels.map((ch) => (
                    <span key={ch} className="capitalize">
                      {ch}
                    </span>
                  ))}
                </div>

                <button
                  type="button"
                  onClick={() => {
                    // Scroll to top and pre-populate query input if possible
                    window.scrollTo({ top: 0, behavior: "smooth" });
                  }}
                  className="flex items-center gap-1 text-[#ffffff] hover:text-[#9281f7] transition-colors"
                >
                  <span>Sweep Similar</span>
                  <ArrowRight className="h-3 w-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 7. Recent Discovery Sweeps (Live Database History) */}
      {recentSessions.length > 0 && (
        <section className="space-y-6">
          <div className="flex items-end justify-between border-b border-[#292d30] pb-4">
            <div>
              <span className="text-xs font-mono uppercase tracking-wider text-[#9281f7]">
                Archived Sweeps
              </span>
              <h2 className="text-2xl sm:text-3xl font-serif font-normal text-[#ffffff] tracking-tight mt-1">
                Recent Intelligence Runs
              </h2>
            </div>
            <span className="text-xs text-[#a1a4a5] font-mono">
              {recentSessions.length} total sessions
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recentSessions.map((session) => (
              <Link
                key={session.id}
                href={`/research/${session.id}`}
                className="p-6 rounded-[16px] bg-[#000000] border border-[#292d30] hover:border-[#ffffff] transition-all duration-150 flex flex-col justify-between group space-y-4 shadow-subtle"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span
                        className={`h-2 w-2 rounded-full ${
                          session.status === "COMPLETED"
                            ? "bg-[#3ad389]"
                            : session.status === "FAILED"
                            ? "bg-[#ff9592]"
                            : "bg-[#ffca16]"
                        }`}
                      />
                      <span className="text-xs font-mono text-[#a1a4a5] uppercase">
                        {session.status}
                      </span>
                    </div>

                    <span className="text-xs font-mono text-[#9281f7] bg-[#000000] px-2 py-0.5 rounded-[6px] border border-[#292d30]">
                      {session.total_items_scraped} signals
                    </span>
                  </div>

                  <h3 className="text-base font-sans font-medium text-[#f0f0f0] group-hover:text-[#ffffff] transition-colors line-clamp-2 leading-snug">
                    {session.query}
                  </h3>
                </div>

                <div className="pt-4 border-t border-[#292d30] flex items-center justify-between text-xs font-mono">
                  <div className="flex items-center gap-2 text-[#a1a4a5]">
                    {session.channels_used.slice(0, 3).map((ch) => (
                      <span key={ch} className="capitalize">
                        {ch}
                      </span>
                    ))}
                    {session.channels_used.length > 3 && (
                      <span className="text-[#6e727a]">
                        +{session.channels_used.length - 3}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-1 text-[#f0f0f0] group-hover:text-[#ffffff] transition-colors">
                    <span>Inspect</span>
                    <ChevronRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* 8. Interactive FAQ Accordion */}
      <section className="space-y-6">
        <div className="space-y-2">
          <span className="text-xs font-mono uppercase tracking-wider text-[#9281f7]">
            Got Questions?
          </span>
          <h2 className="text-2xl sm:text-3xl font-serif font-normal text-[#ffffff] tracking-tight">
            Frequently Asked Questions
          </h2>
          <p className="text-sm font-sans text-[#a1a4a5]">
            Everything you need to know about PulseRadar autonomous intelligence.
          </p>
        </div>

        <div className="space-y-3">
          {FAQS.map((faq, idx) => (
            <div
              key={idx}
              className="rounded-[16px] border border-[#292d30] bg-[#000000] overflow-hidden transition-all"
            >
              <button
                type="button"
                onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
                className="w-full p-5 text-left flex items-center justify-between gap-4 hover:bg-[#292d30]/20 transition-colors"
              >
                <span className="text-sm sm:text-base font-sans font-medium text-[#ffffff]">
                  {faq.q}
                </span>
                <ChevronDown
                  className={`h-4 w-4 text-[#a1a4a5] shrink-0 transition-transform duration-200 ${
                    openFaq === idx ? "rotate-180 text-[#ffffff]" : ""
                  }`}
                />
              </button>

              {openFaq === idx && (
                <div className="px-5 pb-5 pt-1 text-xs sm:text-sm font-sans text-[#a1a4a5] leading-relaxed border-t border-[#292d30]/50">
                  {faq.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* 9. Editorial Closing Manifesto & CTA Banner */}
      <section className="p-8 sm:p-12 rounded-[20px] bg-[#000000] border border-[#292d30] relative overflow-hidden shadow-subtle space-y-6">
        <div className="relative z-10 max-w-2xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#9281f7]/10 border border-[#9281f7]/30 text-xs font-mono text-[#9281f7]">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Autonomous Intelligence Suite</span>
          </div>

          <h2 className="text-3xl sm:text-5xl font-serif font-normal text-[#ffffff] tracking-tight leading-tight">
            Stop guessing customer pain. <br />
            <span className="italic text-[#f0f0f0]">Extract reality in seconds.</span>
          </h2>

          <p className="text-sm sm:text-base font-sans text-[#a1a4a5] leading-relaxed">
            Run your first multi-channel sweep or benchmark your domain&apos;s AI search citation readiness with our SEO &amp; GEO Studio.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <button
              type="button"
              onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
              className="px-6 py-3 bg-[#ffffff] hover:bg-[#ffffff]/90 text-[#000000] font-sans font-medium text-sm rounded-[6px] flex items-center gap-2 transition-all shadow-subtle"
            >
              <Zap className="h-4 w-4" />
              <span>Launch Discovery Sweep</span>
            </button>

            <Link
              href="/seo"
              className="px-6 py-3 bg-[#000000] hover:bg-[#292d30]/40 text-[#ffffff] border border-[#292d30] hover:border-[#ffffff] font-sans font-medium text-sm rounded-[6px] flex items-center gap-2 transition-all"
            >
              <Globe className="h-4 w-4 text-[#9281f7]" />
              <span>Explore SEO &amp; GEO Studio</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>

        {/* Ambient Void Glow */}
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-[#9281f7]/10 to-transparent pointer-events-none" />
      </section>
    </div>
  );
}
