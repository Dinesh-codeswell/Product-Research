"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Globe,
  Search,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  ChevronRight,
  ChevronDown,
  Activity,
  Layers,
  FileCode,
  CheckCircle2,
  Clock,
  Zap,
  Sliders,
  AlertTriangle,
  Cpu,
  Monitor,
  Check,
  X,
  FileText,
  BarChart3,
  ExternalLink,
  Code2,
  Radio
} from "lucide-react";
import { startSeoAudit, listRecentSeoAudits } from "@/lib/api";

const AUDIT_MODES = [
  {
    id: "quick",
    label: "Quick Audit (~15s)",
    badge: "FAST",
    desc: "Fast-path SSR crawl, 4-pillar GEO readiness score, meta & schema generator"
  },
  {
    id: "full",
    label: "Full Deep Audit (Playwright CSR)",
    badge: "PLAYWRIGHT",
    desc: "Spawns headless Chromium to detect client-side JS rendering gaps & hydration risks"
  },
  {
    id: "geo",
    label: "GEO AI Citation Focus",
    badge: "LLM READY",
    desc: "Evaluates citation readiness across ChatGPT, Perplexity, Gemini & Claude"
  },
  {
    id: "drift",
    label: "Drift & Baseline Check",
    badge: "REGRESSION",
    desc: "Compares current metrics against saved baseline to catch tag or schema regressions"
  }
];

// Pre-audited benchmark domains
const BENCHMARK_SHOWCASE = [
  {
    domain: "resend.com",
    url: "https://resend.com",
    geoScore: 88,
    techScore: 95,
    hydrationGap: "0ms",
    schemas: 3,
    highlight: "Exceptional evidence density & clean semantic HTML structure."
  },
  {
    domain: "supabase.com",
    url: "https://supabase.com",
    geoScore: 84,
    techScore: 92,
    hydrationGap: "Clean",
    schemas: 4,
    highlight: "Rich quantitative developer documentation & high authority attribution."
  },
  {
    domain: "songdew.com",
    url: "https://songdew.com",
    geoScore: 74,
    techScore: 80,
    hydrationGap: "14%",
    schemas: 2,
    highlight: "Dynamic artist catalog requires SSR hydration optimization for AI crawlers."
  },
  {
    domain: "github.com",
    url: "https://github.com",
    geoScore: 92,
    techScore: 96,
    hydrationGap: "0ms",
    schemas: 5,
    highlight: "Gold-standard inverted pyramid hierarchy and universal bot accessibility."
  }
];

// SEO vs GEO Comparison Matrix
const SEO_VS_GEO_ROWS = [
  {
    dimension: "Primary Objective",
    traditional: "Rank on Page 1 blue links in Google SERP",
    geo: "Become the cited source in ChatGPT, Perplexity & Gemini"
  },
  {
    dimension: "Core Ranking Signal",
    traditional: "Keyword frequency & backlink domain rating",
    geo: "Evidence density, statistics, and structured Q&A clarity"
  },
  {
    dimension: "Content Architecture",
    traditional: "Keyword-stuffed long-form articles (2,000+ words)",
    geo: "Inverted pyramid: front-loaded definitions & quantitative tables"
  },
  {
    dimension: "Rendering Requirement",
    traditional: "Googlebot renders JavaScript over days/weeks",
    geo: "AI crawlers (GPTBot, Perplexity) demand instant raw SSR HTML"
  },
  {
    dimension: "Structured Data",
    traditional: "Basic OpenGraph and schema for rich cards",
    geo: "Deep JSON-LD knowledge graphs (Software, Organization, FAQ)"
  },
  {
    dimension: "Success Metric",
    traditional: "Click-through rate (CTR) to web landing page",
    geo: "Direct AI recommendation share & verbatim quote attribution"
  }
];

// Interactive SEO & GEO FAQs
const SEO_FAQS = [
  {
    q: "What is Generative Engine Optimization (GEO) and why does traditional SEO fall short?",
    a: "Traditional SEO focuses on keyword stuffing and acquiring backlinks to rank in Google's 10 blue links. Generative Engine Optimization (GEO) optimizes content to be ingested and cited as a verified authority by AI search engines like ChatGPT Search, Perplexity, Google Gemini, and Claude. AI search engines ignore keyword density; they prioritize empirical data tables, direct answers in paragraph 1, author attribution, and schema markup."
  },
  {
    q: "How does the Playwright Hydration Gap test work?",
    a: "PulseRadar executes a dual-phase crawl: first, it fetches the initial server response using lightweight HTTP requests; second, it spawns a full headless Playwright Chromium instance that executes client-side JavaScript. By diffing the two DOM trees, PulseRadar detects content, headings, or metadata that only exist after client-side hydration—which AI search crawlers often fail to index."
  },
  {
    q: "How are the 4 GEO pillars scored?",
    a: "Based on empirical research from EPK Pilot and academic GEO benchmarks, PulseRadar weights 4 core pillars: Evidence Density (35% - statistics, numbers, quotes), Structure & Inverted Pyramid (25% - H1-H3 hierarchy, concise early answers), E-E-A-T Authority (25% - author credentials, source attribution), and AI Bot Crawlability (15% - robots.txt rules for GPTBot/ClaudeBot/PerplexityBot and zero JS rendering blocks)."
  },
  {
    q: "Are the generated JSON-LD schemas valid for production?",
    a: "Yes. All generated schemas adhere strictly to Schema.org standards and Google Rich Results guidelines. You can copy the generated JSON-LD directly for Organization, WebSite, SoftwareApplication, FAQPage, Article, and BreadcrumbList, and paste it into your Next.js, Astro, or static HTML head tags."
  },
  {
    q: "How does Drift & Baseline Monitoring work?",
    a: "When you audit a domain, PulseRadar can save a baseline snapshot containing its canonical tags, title, meta description, heading structure, and schema fingerprints. Future audits compare the live URL against this baseline, flagging any accidental tag omissions, broken links, or score degradation."
  }
];

export default function SeoLaunchpadPage() {
  const router = useRouter();

  const [url, setUrl] = useState("");
  const [auditType, setAuditType] = useState<"quick" | "full" | "geo" | "drift">("quick");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recentAudits, setRecentAudits] = useState<any[]>([]);
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  useEffect(() => {
    listRecentSeoAudits().then(setRecentAudits);
  }, []);

  const handleLaunch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const res = await startSeoAudit({
        url: url.trim(),
        audit_type: auditType
      });
      router.push(`/seo/${res.audit_id}`);
    } catch (err: any) {
      setError(err.message || "Failed to start SEO audit");
      setIsLoading(false);
    }
  };

  const handleQuickUrl = (sampleUrl: string) => {
    setUrl(sampleUrl);
  };

  return (
    <div className="space-y-24 animate-in fade-in duration-200">
      {/* 1. Editorial Hero Section (Domaine Serif + Resend Dark Velvet Wireframe) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center pt-2 sm:pt-6">
        <div className="lg:col-span-8 space-y-6">
          {/* Announcement Pill */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-transparent border border-[#292d30] text-xs font-sans text-[#f0f0f0] hover:border-[#ffffff]/50 transition-colors">
            <span className="h-1.5 w-1.5 rounded-full bg-[#9281f7]" />
            <span className="font-mono text-[11px] text-[#9281f7]">SEO &amp; GEO Studio v2.0</span>
            <span className="text-[#a1a4a5]">•</span>
            <span>4-Pillar AI Citation &amp; Technical Pipeline</span>
            <ChevronRight className="h-3 w-3 text-[#a1a4a5]" />
          </div>

          {/* Domaine Editorial Display Headline */}
          <h1 className="font-serif text-4xl sm:text-6xl lg:text-7xl font-normal text-[#ffffff] tracking-[-0.01em] leading-[1.05]">
            Search authority &amp; AI citation, <br />
            <span className="italic text-[#f0f0f0]">verified from the void.</span>
          </h1>

          <p className="text-base sm:text-lg font-sans text-[#a1a4a5] max-w-2xl leading-relaxed">
            Execute technical crawls, evaluate 4-pillar Generative Engine Optimization (GEO) for ChatGPT &amp; Perplexity, detect Playwright client-side hydration gaps, and generate copy-ready JSON-LD schemas.
          </p>
        </div>

        {/* Sculptural Black 3D Cube Anchor */}
        <div className="lg:col-span-4 flex items-center justify-center lg:justify-end">
          <div className="relative w-48 h-48 sm:w-56 sm:h-56 flex items-center justify-center">
            <div className="relative w-40 h-40 border border-[#292d30] rounded-[16px] bg-[#000000] rotate-12 transition-transform duration-700 hover:rotate-6 shadow-subtle flex flex-col justify-between p-4 group">
              <div className="flex items-center justify-between text-[11px] font-mono text-[#a1a4a5]">
                <div className="flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#3ad389]" />
                  <span>GEO 4-PILLARS</span>
                </div>
                <span className="text-[#9281f7]">0-100</span>
              </div>

              <div className="space-y-1 font-mono text-xs">
                <div className="text-[#6e727a] text-[10px]">AI ENGINE CITATION</div>
                <div className="text-[#ffffff] font-medium tracking-tight">ChatGPT &amp; Perplexity</div>
                <div className="text-[#9281f7] text-[11px] truncate">@evidence_density</div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-[#292d30] text-[10px] font-mono text-[#6e727a]">
                <span>PLAYWRIGHT</span>
                <span className="h-1 w-1 rounded-full bg-[#9281f7]" />
                <span>JSON-LD</span>
              </div>
            </div>
            <div className="absolute inset-0 -z-10 border border-[#292d30]/40 rounded-[24px] rotate-[-6deg] pointer-events-none" />
          </div>
        </div>
      </div>

      {/* 2. Main Audit Console (16px Card, 1px #292d30 Border) */}
      <div className="p-6 sm:p-8 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-6 shadow-subtle">
        {/* Mode Selector Tabs */}
        <div className="flex items-center justify-between border-b border-[#292d30] pb-4 overflow-x-auto scrollbar-none">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-[#a1a4a5] uppercase tracking-wider mr-1">
              Audit Mode:
            </span>

            {AUDIT_MODES.map((mode) => (
              <button
                key={mode.id}
                type="button"
                onClick={() => setAuditType(mode.id as any)}
                className={`px-3 py-1.5 rounded-[6px] text-xs font-mono flex items-center gap-2 transition-all ${
                  auditType === mode.id
                    ? "bg-[#000000] text-[#ffffff] border border-[#ffffff] shadow-subtle"
                    : "bg-[#000000] text-[#a1a4a5] border border-[#292d30] hover:text-[#ffffff] hover:border-[#6e727a]"
                }`}
              >
                <span>{mode.label}</span>
                <span className="text-[10px] px-1 py-0.2 rounded bg-[#292d30]/60 text-[#9281f7]">
                  {mode.badge}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Input Form */}
        <form onSubmit={handleLaunch} className="space-y-4">
          <div className="relative flex flex-col sm:flex-row items-stretch gap-2.5">
            <div className="relative flex-1">
              <Globe className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-[#6e727a]" />
              <input
                type="text"
                placeholder="Enter URL or domain (e.g., 'https://songdew.com', 'https://supabase.com', 'https://resend.com')..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={isLoading}
                className="w-full pl-11 pr-4 py-3.5 bg-[#000000] border border-[#292d30] rounded-[6px] text-sm text-[#ffffff] placeholder-[#464a4d] focus:outline-none focus:border-[#ffffff] transition-colors font-sans"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading || !url.trim()}
              className="px-6 py-3.5 bg-[#ffffff] hover:bg-[#ffffff]/90 text-[#000000] font-sans font-medium text-sm rounded-[6px] flex items-center justify-center gap-2 transition-all disabled:opacity-40 shrink-0"
            >
              {isLoading ? (
                <>
                  <span className="h-4 w-4 border-2 border-[#000000] border-t-transparent rounded-full animate-spin" />
                  <span>Auditing...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 text-[#000000]" />
                  <span>Run SEO &amp; GEO Audit</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </div>

          {error && (
            <div className="p-3 rounded-[6px] bg-[#ff9592]/10 border border-[#ff9592]/30 text-[#ff9592] text-xs font-mono flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Quick Preset Samples */}
          <div className="flex flex-wrap items-center gap-2 pt-1 text-xs font-mono text-[#a1a4a5]">
            <span className="text-[#6e727a]">Quick Presets:</span>
            {["https://songdew.com", "https://supabase.com", "https://resend.com", "https://github.com"].map((sample) => (
              <button
                key={sample}
                type="button"
                onClick={() => handleQuickUrl(sample)}
                className="px-2 py-0.5 rounded-[4px] bg-[#000000] border border-[#292d30] hover:border-[#ffffff] hover:text-[#ffffff] text-[11px] transition-colors"
              >
                {sample.replace("https://", "")}
              </button>
            ))}
          </div>
        </form>
      </div>

      {/* 3. Live Telemetry Strip */}
      <section className="border-y border-[#292d30] py-8">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-[#9281f7]">
              <Sparkles className="h-4 w-4" />
              <span className="text-[11px] font-mono uppercase tracking-wider">GEO Citation</span>
            </div>
            <div className="text-2xl sm:text-3xl font-sans font-semibold text-[#ffffff] tracking-tight">
              4 Pillars
            </div>
            <p className="text-xs text-[#a1a4a5] font-sans">
              Weighted AI ranking for ChatGPT, Perplexity &amp; Claude
            </p>
          </div>

          <div className="space-y-1">
            <div className="flex items-center gap-2 text-[#3ad389]">
              <Activity className="h-4 w-4" />
              <span className="text-[11px] font-mono uppercase tracking-wider">Hydration Gap</span>
            </div>
            <div className="text-2xl sm:text-3xl font-sans font-semibold text-[#ffffff] tracking-tight">
              Playwright CSR
            </div>
            <p className="text-xs text-[#a1a4a5] font-sans">
              Diffs static server HTML against executed client DOM
            </p>
          </div>

          <div className="space-y-1">
            <div className="flex items-center gap-2 text-[#3b9eff]">
              <FileCode className="h-4 w-4" />
              <span className="text-[11px] font-mono uppercase tracking-wider">JSON-LD Studio</span>
            </div>
            <div className="text-2xl sm:text-3xl font-sans font-semibold text-[#ffffff] tracking-tight">
              5 Schemas
            </div>
            <p className="text-xs text-[#a1a4a5] font-sans">
              Organization, Software, Article, FAQ &amp; Breadcrumbs
            </p>
          </div>

          <div className="space-y-1">
            <div className="flex items-center gap-2 text-[#ffca16]">
              <Clock className="h-4 w-4" />
              <span className="text-[11px] font-mono uppercase tracking-wider">Drift Engine</span>
            </div>
            <div className="text-2xl sm:text-3xl font-sans font-semibold text-[#ffffff] tracking-tight">
              Zero Regress
            </div>
            <p className="text-xs text-[#a1a4a5] font-sans">
              Monitors title, canonical, and tag drift across releases
            </p>
          </div>
        </div>
      </section>

      {/* 4. The 4-Pillar Generative Engine Optimization (GEO) Deep Dive */}
      <section className="space-y-10">
        <div className="space-y-2">
          <span className="text-xs font-mono uppercase tracking-wider text-[#9281f7]">
            GEO Evaluation Matrix
          </span>
          <h2 className="text-3xl sm:text-4xl font-serif font-normal text-[#ffffff] tracking-tight">
            How LLMs decide what content to cite.
          </h2>
          <p className="text-sm sm:text-base font-sans text-[#a1a4a5] max-w-2xl">
            Derived from academic GEO research and real-world evaluation in EPK Pilot, PulseRadar scores your domain across 4 weighted citation pillars.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Pillar 1 */}
          <div className="p-6 rounded-[16px] bg-[#000000] border border-[#292d30] hover:border-[#6e727a] transition-all space-y-4 shadow-subtle flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-[#9281f7] bg-[#9281f7]/10 px-2 py-0.5 rounded-[4px] border border-[#9281f7]/30">
                  PILLAR 01 (35%)
                </span>
                <BarChart3 className="h-4 w-4 text-[#9281f7]" />
              </div>
              <h3 className="text-base font-sans font-medium text-[#ffffff]">
                Evidence Density &amp; Citations
              </h3>
              <p className="text-xs font-sans text-[#a1a4a5] leading-relaxed">
                Evaluates quantitative statistics, percentage gains, data benchmarks, and verbatim quotes. LLMs are trained to cite concrete numerical assertions rather than generic marketing fluff.
              </p>
            </div>
            <div className="p-3 rounded-[6px] bg-[#000000] border border-[#292d30] font-mono text-[11px] text-[#9281f7]">
              Weight: 35% of Total Score
            </div>
          </div>

          {/* Pillar 2 */}
          <div className="p-6 rounded-[16px] bg-[#000000] border border-[#292d30] hover:border-[#6e727a] transition-all space-y-4 shadow-subtle flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-[#3ad389] bg-[#3ad389]/10 px-2 py-0.5 rounded-[4px] border border-[#3ad389]/30">
                  PILLAR 02 (25%)
                </span>
                <Layers className="h-4 w-4 text-[#3ad389]" />
              </div>
              <h3 className="text-base font-sans font-medium text-[#ffffff]">
                Structural Hierarchy &amp; Q&amp;A
              </h3>
              <p className="text-xs font-sans text-[#a1a4a5] leading-relaxed">
                Rewards an inverted pyramid architecture. Front-loads direct answers and definitions in paragraph 1, followed by clean H2/H3 subsections and bulleted lists that AI summarizers ingest cleanly.
              </p>
            </div>
            <div className="p-3 rounded-[6px] bg-[#000000] border border-[#292d30] font-mono text-[11px] text-[#3ad389]">
              Weight: 25% of Total Score
            </div>
          </div>

          {/* Pillar 3 */}
          <div className="p-6 rounded-[16px] bg-[#000000] border border-[#292d30] hover:border-[#6e727a] transition-all space-y-4 shadow-subtle flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-[#3b9eff] bg-[#3b9eff]/10 px-2 py-0.5 rounded-[4px] border border-[#3b9eff]/30">
                  PILLAR 03 (25%)
                </span>
                <ShieldCheck className="h-4 w-4 text-[#3b9eff]" />
              </div>
              <h3 className="text-base font-sans font-medium text-[#ffffff]">
                E-E-A-T &amp; Authority Attribution
              </h3>
              <p className="text-xs font-sans text-[#a1a4a5] leading-relaxed">
                Verifies author profiles, professional credentials, explicit publication dates, and external academic references. AI models prefer citing recognized domain experts.
              </p>
            </div>
            <div className="p-3 rounded-[6px] bg-[#000000] border border-[#292d30] font-mono text-[11px] text-[#3b9eff]">
              Weight: 25% of Total Score
            </div>
          </div>

          {/* Pillar 4 */}
          <div className="p-6 rounded-[16px] bg-[#000000] border border-[#292d30] hover:border-[#6e727a] transition-all space-y-4 shadow-subtle flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-[#ffca16] bg-[#ffca16]/10 px-2 py-0.5 rounded-[4px] border border-[#ffca16]/30">
                  PILLAR 04 (15%)
                </span>
                <Cpu className="h-4 w-4 text-[#ffca16]" />
              </div>
              <h3 className="text-base font-sans font-medium text-[#ffffff]">
                AI Crawlability &amp; Bot Access
              </h3>
              <p className="text-xs font-sans text-[#a1a4a5] leading-relaxed">
                Audits robots.txt rules for GPTBot, PerplexityBot, ClaudeBot, and Google-Extended. Ensures zero cloudflare challenge walls or JavaScript rendering barriers block LLM scrapers.
              </p>
            </div>
            <div className="p-3 rounded-[6px] bg-[#000000] border border-[#292d30] font-mono text-[11px] text-[#ffca16]">
              Weight: 15% of Total Score
            </div>
          </div>
        </div>
      </section>

      {/* 5. Playwright Hydration Gap Visualizer (SSR vs CSR) */}
      <section className="p-8 sm:p-10 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-8 shadow-subtle">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-[#3ad389]">
            <Activity className="h-4 w-4" />
            <span className="text-xs font-mono uppercase tracking-wider">Playwright Engine</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-serif font-normal text-[#ffffff] tracking-tight">
            The Client-Side Hydration Blindspot
          </h2>
          <p className="text-sm font-sans text-[#a1a4a5] max-w-2xl">
            Many modern Next.js, Remix, and React SPAs rely on client-side fetching. While users see the page normally, AI search bots don&apos;t run JavaScript and receive an empty HTML shell.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-5 rounded-[12px] bg-[#000000] border border-[#ff9592]/30 space-y-3">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-[#ff9592] flex items-center gap-1.5">
                <X className="h-3.5 w-3.5" />
                Initial Server Response (SSR)
              </span>
              <span className="text-[#6e727a]">Fast-path crawler</span>
            </div>
            <div className="p-4 rounded-[6px] bg-[#000000] border border-[#292d30] font-mono text-[11px] text-[#a1a4a5] space-y-1">
              <div className="text-[#6e727a]">&lt;div id=&quot;__next&quot;&gt;</div>
              <div className="text-[#ff9592] pl-4">&lt;div class=&quot;skeleton-loader&quot;&gt;&lt;/div&gt;</div>
              <div className="text-[#6e727a] pl-4">&lt;!-- Dynamic data fetched on client --&gt;</div>
              <div className="text-[#6e727a]">&lt;/div&gt;</div>
            </div>
            <p className="text-xs font-sans text-[#a1a4a5]">
              AI bots like PerplexityBot and GPTBot parse only this raw HTML. If key data is loaded via React `useEffect`, your content is invisible to AI citations.
            </p>
          </div>

          <div className="p-5 rounded-[12px] bg-[#000000] border border-[#3ad389]/30 space-y-3">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-[#3ad389] flex items-center gap-1.5">
                <Check className="h-3.5 w-3.5" />
                Playwright Full DOM (CSR)
              </span>
              <span className="text-[#3ad389]">Headless Chromium</span>
            </div>
            <div className="p-4 rounded-[6px] bg-[#000000] border border-[#292d30] font-mono text-[11px] text-[#3ad389] space-y-1">
              <div className="text-[#6e727a]">&lt;div id=&quot;__next&quot;&gt;</div>
              <div className="text-[#3ad389] pl-4">&lt;h1&gt;Production Benchmark Results&lt;/h1&gt;</div>
              <div className="text-[#3ad389] pl-4">&lt;table class=&quot;pricing-matrix&quot;&gt;...&lt;/table&gt;</div>
              <div className="text-[#6e727a]">&lt;/div&gt;</div>
            </div>
            <p className="text-xs font-sans text-[#a1a4a5]">
              PulseRadar spots the exact difference between server and client DOM, telling you which headings, descriptions, and tables are missing from initial HTML.
            </p>
          </div>
        </div>
      </section>

      {/* 6. Traditional SEO vs Generative Engine Optimization Matrix */}
      <section className="space-y-6">
        <div className="space-y-2">
          <span className="text-xs font-mono uppercase tracking-wider text-[#9281f7]">
            Paradigm Shift
          </span>
          <h2 className="text-2xl sm:text-3xl font-serif font-normal text-[#ffffff] tracking-tight">
            Traditional SEO vs. Generative Engine Optimization (GEO)
          </h2>
          <p className="text-sm font-sans text-[#a1a4a5] max-w-xl">
            Why optimizing for AI search requires a completely new playbook.
          </p>
        </div>

        <div className="overflow-x-auto rounded-[16px] border border-[#292d30] bg-[#000000] shadow-subtle">
          <table className="w-full text-left text-xs font-sans border-collapse">
            <thead>
              <tr className="border-b border-[#292d30] bg-[#000000]/60">
                <th className="py-4 px-6 font-mono text-[#a1a4a5] uppercase tracking-wider w-1/4">
                  Dimension
                </th>
                <th className="py-4 px-6 font-mono text-[#9281f7] uppercase tracking-wider w-1/3 bg-[#9281f7]/5 border-x border-[#292d30]">
                  Generative Engine Optimization (GEO)
                </th>
                <th className="py-4 px-6 font-mono text-[#6e727a] uppercase tracking-wider w-1/3">
                  Traditional SEO (Google 2015-2023)
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#292d30]">
              {SEO_VS_GEO_ROWS.map((row, idx) => (
                <tr key={idx} className="hover:bg-[#292d30]/20 transition-colors">
                  <td className="py-4 px-6 font-medium text-[#ffffff]">
                    {row.dimension}
                  </td>
                  <td className="py-4 px-6 text-[#f0f0f0] font-sans bg-[#9281f7]/5 border-x border-[#292d30]">
                    <div className="flex items-start gap-2">
                      <Sparkles className="h-4 w-4 text-[#9281f7] shrink-0 mt-0.5" />
                      <span>{row.geo}</span>
                    </div>
                  </td>
                  <td className="py-4 px-6 text-[#a1a4a5]">
                    {row.traditional}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* 7. Curated Benchmark Showcase */}
      <section className="space-y-6">
        <div className="flex items-end justify-between border-b border-[#292d30] pb-4">
          <div>
            <span className="text-xs font-mono uppercase tracking-wider text-[#9281f7]">
              Pre-Audited Benchmarks
            </span>
            <h2 className="text-2xl sm:text-3xl font-serif font-normal text-[#ffffff] tracking-tight mt-1">
              Audited Domain Showcase
            </h2>
          </div>
          <span className="text-xs text-[#a1a4a5] font-mono">
            Sample Industry Benchmarks
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {BENCHMARK_SHOWCASE.map((item) => (
            <div
              key={item.domain}
              className="p-5 rounded-[16px] bg-[#000000] border border-[#292d30] hover:border-[#ffffff] transition-all flex flex-col justify-between space-y-4 shadow-subtle group"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-[#9281f7] bg-[#9281f7]/10 px-2 py-0.5 rounded-[4px] border border-[#9281f7]/20">
                    GEO {item.geoScore}/100
                  </span>
                  <span className="text-[#a1a4a5]">
                    Tech {item.techScore}
                  </span>
                </div>

                <div>
                  <h4 className="text-base font-sans font-medium text-[#ffffff] group-hover:text-[#ffffff] transition-colors">
                    {item.domain}
                  </h4>
                  <p className="text-xs font-sans text-[#a1a4a5] mt-1 line-clamp-2 leading-relaxed">
                    {item.highlight}
                  </p>
                </div>
              </div>

              <div className="pt-3 border-t border-[#292d30] flex items-center justify-between text-xs font-mono">
                <span className="text-[#6e727a]">
                  Gap: {item.hydrationGap}
                </span>

                <button
                  type="button"
                  onClick={() => {
                    setUrl(item.url);
                    window.scrollTo({ top: 0, behavior: "smooth" });
                  }}
                  className="flex items-center gap-1 text-[#ffffff] hover:text-[#9281f7] transition-colors"
                >
                  <span>Audit Now</span>
                  <ArrowRight className="h-3 w-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 8. Recent Audits Archive (Live Database History) */}
      {recentAudits.length > 0 && (
        <section className="space-y-6">
          <div className="flex items-end justify-between border-b border-[#292d30] pb-4">
            <div>
              <span className="text-xs font-mono uppercase tracking-wider text-[#9281f7]">
                Audit Archive
              </span>
              <h2 className="text-2xl sm:text-3xl font-serif font-normal text-[#ffffff] tracking-tight mt-1">
                Recent SEO &amp; GEO Sweeps
              </h2>
            </div>
            <span className="text-xs text-[#a1a4a5] font-mono">
              {recentAudits.length} recorded audits
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recentAudits.map((item) => (
              <Link
                key={item.id}
                href={`/seo/${item.id}`}
                className="p-6 rounded-[16px] bg-[#000000] border border-[#292d30] hover:border-[#ffffff] transition-all duration-150 flex flex-col justify-between group space-y-4 shadow-subtle"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span
                        className={`h-2 w-2 rounded-full ${
                          item.status === "COMPLETED"
                            ? "bg-[#3ad389]"
                            : item.status === "FAILED"
                            ? "bg-[#ff9592]"
                            : "bg-[#ffca16]"
                        }`}
                      />
                      <span className="text-xs font-mono text-[#a1a4a5] uppercase">
                        {item.audit_type}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-mono text-[#9281f7] bg-[#000000] px-2 py-0.5 rounded-[6px] border border-[#292d30]">
                        GEO {item.geo_readiness_score || 0}
                      </span>
                      <span className="text-xs font-mono text-[#ffffff] bg-[#000000] px-2 py-0.5 rounded-[6px] border border-[#292d30] font-semibold">
                        {item.overall_score || 0}/100
                      </span>
                    </div>
                  </div>

                  <h3 className="text-sm font-sans font-medium text-[#f0f0f0] group-hover:text-[#ffffff] transition-colors line-clamp-2 leading-snug">
                    {item.url}
                  </h3>
                </div>

                <div className="pt-4 border-t border-[#292d30] flex items-center justify-between text-xs font-mono">
                  <span className="text-[#6e727a] truncate max-w-[180px]">
                    {item.domain}
                  </span>
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

      {/* 9. Interactive SEO & GEO FAQ Accordion */}
      <section className="space-y-6">
        <div className="space-y-2">
          <span className="text-xs font-mono uppercase tracking-wider text-[#9281f7]">
            Technical Knowledge Base
          </span>
          <h2 className="text-2xl sm:text-3xl font-serif font-normal text-[#ffffff] tracking-tight">
            SEO &amp; GEO Frequently Asked Questions
          </h2>
          <p className="text-sm font-sans text-[#a1a4a5]">
            Everything you need to know about AI citation mechanics and client-side hydration gaps.
          </p>
        </div>

        <div className="space-y-3">
          {SEO_FAQS.map((faq, idx) => (
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

      {/* 10. High-Impact Editorial Closing Banner */}
      <section className="p-8 sm:p-12 rounded-[20px] bg-[#000000] border border-[#292d30] relative overflow-hidden shadow-subtle space-y-6">
        <div className="relative z-10 max-w-2xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#9281f7]/10 border border-[#9281f7]/30 text-xs font-mono text-[#9281f7]">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Generative Search Era</span>
          </div>

          <h2 className="text-3xl sm:text-5xl font-serif font-normal text-[#ffffff] tracking-tight leading-tight">
            Don&apos;t get left out of <br />
            <span className="italic text-[#f0f0f0]">ChatGPT &amp; Perplexity answers.</span>
          </h2>

          <p className="text-sm sm:text-base font-sans text-[#a1a4a5] leading-relaxed">
            Audit your domain now to uncover hydration gaps, evaluate evidence density, and generate production-ready JSON-LD schemas.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <button
              type="button"
              onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
              className="px-6 py-3 bg-[#ffffff] hover:bg-[#ffffff]/90 text-[#000000] font-sans font-medium text-sm rounded-[6px] flex items-center gap-2 transition-all shadow-subtle"
            >
              <Zap className="h-4 w-4" />
              <span>Audit Your Domain</span>
            </button>

            <Link
              href="/"
              className="px-6 py-3 bg-[#000000] hover:bg-[#292d30]/40 text-[#ffffff] border border-[#292d30] hover:border-[#ffffff] font-sans font-medium text-sm rounded-[6px] flex items-center gap-2 transition-all"
            >
              <Radio className="h-4 w-4 text-[#9281f7]" />
              <span>Explore Consumer Discovery</span>
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
