"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  Share2,
  Download,
  Check,
  RefreshCw,
  Sparkles,
  Globe,
  Activity,
  FileCode,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Copy,
  ExternalLink,
  Layers,
  Image as ImageIcon,
  TrendingDown,
  TrendingUp,
  Cpu
} from "lucide-react";
import { getSeoAudit, getSeoExportUrl, getSeoEventSourceUrl } from "@/lib/api";
import { SeoAuditSession, SSEProgressEvent } from "@/lib/types";

export default function SeoAuditPage() {
  const routeParams = useParams();
  const rawId = routeParams?.auditId;
  const auditId = Array.isArray(rawId) ? rawId[0] : (rawId as string) || "";

  const [session, setSession] = useState<SeoAuditSession | null>(null);
  const [activeTab, setActiveTab] = useState<"geo" | "technical" | "rendering" | "schemas" | "meta" | "images" | "drift">("geo");
  const [progress, setProgress] = useState<SSEProgressEvent | null>(null);
  const [copiedLink, setCopiedLink] = useState(false);
  const [copiedSchema, setCopiedSchema] = useState(false);
  const [copiedMeta, setCopiedMeta] = useState(false);
  const [copiedTitle, setCopiedTitle] = useState(false);

  const fetchAudit = async () => {
    try {
      const data = await getSeoAudit(auditId);
      setSession(data);
    } catch (e) {
      console.error("Error fetching SEO audit:", e);
    }
  };

  useEffect(() => {
    fetchAudit();

    const eventSource = new EventSource(getSeoEventSourceUrl(auditId));
    eventSource.onmessage = (event) => {
      try {
        const payload: SSEProgressEvent = JSON.parse(event.data);
        setProgress(payload);
        if (payload.stage === "completed" || payload.stage === "failed") {
          fetchAudit();
          eventSource.close();
        }
      } catch (err) {
        console.error("Error parsing SSE event:", err);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      fetchAudit();
    };

    return () => {
      eventSource.close();
    };
  }, [auditId]);

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  const copyToClipboard = (text: string, setter: (val: boolean) => void) => {
    navigator.clipboard.writeText(text);
    setter(true);
    setTimeout(() => setter(false), 2000);
  };

  if (!session) {
    return (
      <div className="py-24 text-center space-y-4">
        <div className="flex items-center justify-center gap-2">
          <span className="h-4 w-4 border-2 border-[#9281f7] border-t-transparent rounded-full animate-spin" />
          <span className="font-mono text-sm text-[#a1a4a5]">Connecting to SEO Audit Engine...</span>
        </div>
      </div>
    );
  }

  const results = session.results;
  const geo = results?.geo;
  const tech = results?.technical;
  const rendering = results?.rendering;
  const schemas = results?.schemas;
  const meta = results?.meta;
  const images = results?.images;
  const drift = results?.drift;
  const aiInsights = results?.ai_insights;

  return (
    <div className="space-y-10 animate-in fade-in duration-200">
      {/* Top Breadcrumb & Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-6 border-b border-[#292d30] pb-6">
        <div className="space-y-2">
          <Link
            href="/seo"
            className="inline-flex items-center gap-1.5 text-xs font-mono text-[#a1a4a5] hover:text-[#ffffff] transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>back_to_seo_studio</span>
          </Link>

          <div className="flex flex-wrap items-center gap-3">
            <h1 className="font-serif text-3xl sm:text-4xl font-normal text-[#ffffff] tracking-[-0.01em]">
              {session.url}
            </h1>

            {/* Status & Mode Badge */}
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-[6px] bg-[#000000] border border-[#292d30] text-xs font-mono">
              <span
                className={`h-2 w-2 rounded-full ${
                  session.status === "COMPLETED"
                    ? "bg-[#3ad389]"
                    : session.status === "FAILED"
                    ? "bg-[#ff9592]"
                    : "bg-[#ffca16]"
                }`}
              />
              <span className="text-[#a1a4a5] uppercase">{session.status}</span>
              <span className="text-[#464a4d]">•</span>
              <span className="text-[#9281f7] uppercase">{session.audit_type}</span>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs font-mono text-[#6e727a]">
            <span>Domain: {session.domain}</span>
            <span>•</span>
            <span>Audited on {new Date(session.created_at).toLocaleString()}</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5 shrink-0">
          <button
            onClick={handleShare}
            className="px-3.5 py-2 rounded-[6px] bg-[#000000] border border-[#292d30] hover:border-[#ffffff] text-xs font-sans text-[#f0f0f0] flex items-center gap-2 transition-all duration-150"
          >
            {copiedLink ? (
              <Check className="h-3.5 w-3.5 text-[#3ad389]" />
            ) : (
              <Share2 className="h-3.5 w-3.5 text-[#a1a4a5]" />
            )}
            <span>{copiedLink ? "Link Copied" : "Share"}</span>
          </button>

          <a
            href={getSeoExportUrl(auditId, "markdown")}
            download
            className="px-3.5 py-2 rounded-[6px] bg-[#000000] border border-[#9281f7]/60 hover:border-[#9281f7] text-xs font-sans text-[#9281f7] hover:text-[#ffffff] flex items-center gap-2 transition-all duration-150 shadow-subtle group"
          >
            <Sparkles className="h-3.5 w-3.5 text-[#9281f7] group-hover:rotate-12 transition-transform" />
            <span>SEO Dossier (.md)</span>
          </a>

          <a
            href={getSeoExportUrl(auditId, "json")}
            download
            className="px-3 py-2 rounded-[6px] bg-[#000000] border border-[#292d30] hover:border-[#ffffff] text-xs font-sans text-[#a1a4a5] hover:text-[#ffffff] flex items-center gap-1.5 transition-all duration-150"
          >
            <Download className="h-3.5 w-3.5 text-[#a1a4a5]" />
            <span>JSON</span>
          </a>
        </div>
      </div>

      {/* Live Progress Banner if running */}
      {session.status !== "COMPLETED" && (
        <div className="p-6 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-3">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-[#9281f7]">{progress?.message || "Running multi-phase SEO & GEO pipeline..."}</span>
            <span className="text-[#ffffff] font-bold">{progress?.percent || 20}%</span>
          </div>
          <div className="w-full h-1.5 bg-[#292d30] rounded-full overflow-hidden">
            <div
              className="h-full bg-[#9281f7] transition-all duration-300"
              style={{ width: `${progress?.percent || 20}%` }}
            />
          </div>
        </div>
      )}

      {/* Top Executive Scorecard Grid (Resend 16px Dark Velvet Cards) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4">
        {/* Composite Overall Score */}
        <div className="p-5 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-2 shadow-subtle flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-mono text-[#a1a4a5]">
            <span>OVERALL HEALTH</span>
            <span className="h-2 w-2 rounded-full bg-[#3ad389]" />
          </div>
          <div className="text-3xl sm:text-4xl font-mono font-medium text-[#ffffff]">
            {session.overall_score}
            <span className="text-xs text-[#6e727a] font-normal"> / 100</span>
          </div>
          <div className="text-[11px] font-mono text-[#a1a4a5] truncate">
            Weighted composite
          </div>
        </div>

        {/* AI Citation Readiness (GEO) */}
        <div className="p-5 rounded-[16px] bg-[#000000] border border-[#9281f7]/50 space-y-2 shadow-subtle flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-mono text-[#9281f7]">
            <span className="font-semibold">GEO AI CITATION</span>
            <Sparkles className="h-3.5 w-3.5 text-[#9281f7]" />
          </div>
          <div className="text-3xl sm:text-4xl font-mono font-medium text-[#9281f7]">
            {session.geo_readiness_score}
            <span className="text-xs text-[#6e727a] font-normal"> / 100</span>
          </div>
          <div className="text-[11px] font-mono text-[#a1a4a5] truncate">
            {geo?.badge || "AI Citation Score"}
          </div>
        </div>

        {/* Technical SEO Score */}
        <div className="p-5 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-2 shadow-subtle flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-mono text-[#a1a4a5]">
            <span>TECHNICAL</span>
            <Activity className="h-3.5 w-3.5 text-[#3b9eff]" />
          </div>
          <div className="text-3xl sm:text-4xl font-mono font-medium text-[#ffffff]">
            {session.technical_score}
            <span className="text-xs text-[#6e727a] font-normal"> / 100</span>
          </div>
          <div className="text-[11px] font-mono text-[#a1a4a5] truncate">
            {tech?.response_time_ms ? `${tech.response_time_ms}ms response` : "Crawl speed"}
          </div>
        </div>

        {/* On-Page & Schema */}
        <div className="p-5 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-2 shadow-subtle flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-mono text-[#a1a4a5]">
            <span>ON-PAGE &amp; SCHEMA</span>
            <FileCode className="h-3.5 w-3.5 text-[#ffca16]" />
          </div>
          <div className="text-3xl sm:text-4xl font-mono font-medium text-[#ffffff]">
            {session.onpage_score}
            <span className="text-xs text-[#6e727a] font-normal"> / 100</span>
          </div>
          <div className="text-[11px] font-mono text-[#a1a4a5] truncate">
            {schemas?.detected_count || 0} schemas detected
          </div>
        </div>

        {/* Image SEO */}
        <div className="p-5 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-2 shadow-subtle flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-mono text-[#a1a4a5]">
            <span>IMAGE SEO</span>
            <ImageIcon className="h-3.5 w-3.5 text-[#3ad389]" />
          </div>
          <div className="text-3xl sm:text-4xl font-mono font-medium text-[#ffffff]">
            {session.image_score}
            <span className="text-xs text-[#6e727a] font-normal"> / 100</span>
          </div>
          <div className="text-[11px] font-mono text-[#a1a4a5] truncate">
            {images?.alt_coverage_percent || 0}% alt coverage
          </div>
        </div>
      </div>

      {/* Executive Summary Card */}
      {session.executive_summary && (
        <div className="p-6 sm:p-8 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-4 shadow-subtle">
          <div className="flex items-center justify-between pb-3 border-b border-[#292d30]">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-[#292d30]" />
              <span className="h-2.5 w-2.5 rounded-full bg-[#292d30]" />
              <span className="h-2.5 w-2.5 rounded-full bg-[#292d30]" />
              <span className="text-xs font-mono text-[#a1a4a5] ml-2">
                EXECUTIVE_SEO_DOSSIER.md
              </span>
            </div>
            <span className="text-[11px] font-mono text-[#9281f7]">
              VERIFIED CRAWL
            </span>
          </div>
          <div className="prose prose-invert max-w-none text-sm text-[#f0f0f0] leading-relaxed whitespace-pre-line font-sans">
            {session.executive_summary}
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex items-center justify-between border-b border-[#292d30]">
        <div className="flex items-center gap-6 overflow-x-auto pb-0.5 scrollbar-none">
          <button
            onClick={() => setActiveTab("geo")}
            className={`pb-3 text-sm font-sans font-medium flex items-center gap-2 border-b-2 transition-all duration-150 shrink-0 ${
              activeTab === "geo"
                ? "border-[#9281f7] text-[#ffffff]"
                : "border-transparent text-[#a1a4a5] hover:text-[#f0f0f0]"
            }`}
          >
            <Sparkles className="h-4 w-4 text-[#9281f7]" />
            <span>GEO AI Citation Matrix</span>
            <span className="text-xs font-mono text-[#9281f7] bg-[#000000] px-1.5 py-0.2 rounded border border-[#292d30]">
              {session.geo_readiness_score}
            </span>
          </button>

          <button
            onClick={() => setActiveTab("technical")}
            className={`pb-3 text-sm font-sans font-medium flex items-center gap-2 border-b-2 transition-all duration-150 shrink-0 ${
              activeTab === "technical"
                ? "border-[#ffffff] text-[#ffffff]"
                : "border-transparent text-[#a1a4a5] hover:text-[#f0f0f0]"
            }`}
          >
            <Activity className="h-4 w-4" />
            <span>Technical &amp; Crawl</span>
            <span className="text-xs font-mono text-[#a1a4a5] bg-[#000000] px-1.5 py-0.2 rounded border border-[#292d30]">
              {tech?.issues?.length || 0} issues
            </span>
          </button>

          <button
            onClick={() => setActiveTab("rendering")}
            className={`pb-3 text-sm font-sans font-medium flex items-center gap-2 border-b-2 transition-all duration-150 shrink-0 ${
              activeTab === "rendering"
                ? "border-[#ffffff] text-[#ffffff]"
                : "border-transparent text-[#a1a4a5] hover:text-[#f0f0f0]"
            }`}
          >
            <Cpu className="h-4 w-4" />
            <span>Playwright Hydration Gap</span>
            {rendering?.risk_level === "HIGH" && (
              <span className="h-1.5 w-1.5 rounded-full bg-[#ff9592]" />
            )}
          </button>

          <button
            onClick={() => setActiveTab("schemas")}
            className={`pb-3 text-sm font-sans font-medium flex items-center gap-2 border-b-2 transition-all duration-150 shrink-0 ${
              activeTab === "schemas"
                ? "border-[#ffffff] text-[#ffffff]"
                : "border-transparent text-[#a1a4a5] hover:text-[#f0f0f0]"
            }`}
          >
            <FileCode className="h-4 w-4" />
            <span>JSON-LD Schemas</span>
          </button>

          <button
            onClick={() => setActiveTab("meta")}
            className={`pb-3 text-sm font-sans font-medium flex items-center gap-2 border-b-2 transition-all duration-150 shrink-0 ${
              activeTab === "meta"
                ? "border-[#ffffff] text-[#ffffff]"
                : "border-transparent text-[#a1a4a5] hover:text-[#f0f0f0]"
            }`}
          >
            <Globe className="h-4 w-4" />
            <span>Meta &amp; SERP Preview</span>
          </button>

          <button
            onClick={() => setActiveTab("images")}
            className={`pb-3 text-sm font-sans font-medium flex items-center gap-2 border-b-2 transition-all duration-150 shrink-0 ${
              activeTab === "images"
                ? "border-[#ffffff] text-[#ffffff]"
                : "border-transparent text-[#a1a4a5] hover:text-[#f0f0f0]"
            }`}
          >
            <ImageIcon className="h-4 w-4" />
            <span>Image SEO</span>
          </button>

          <button
            onClick={() => setActiveTab("drift")}
            className={`pb-3 text-sm font-sans font-medium flex items-center gap-2 border-b-2 transition-all duration-150 shrink-0 ${
              activeTab === "drift"
                ? "border-[#ffffff] text-[#ffffff]"
                : "border-transparent text-[#a1a4a5] hover:text-[#f0f0f0]"
            }`}
          >
            <Layers className="h-4 w-4" />
            <span>SEO Drift</span>
          </button>
        </div>

        <button
          onClick={fetchAudit}
          className="pb-3 text-[#6e727a] hover:text-[#ffffff] transition-colors shrink-0"
          title="Refresh Data"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {/* Tab 1: GEO AI Citation Matrix */}
      {activeTab === "geo" && geo && (
        <div className="space-y-8 animate-in fade-in duration-150">
          {/* 4 Pillars Progress Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(geo.pillars).map(([key, pillar]: [string, any]) => (
              <div key={key} className="p-5 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-3 shadow-subtle">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="capitalize text-[#ffffff] font-medium">
                    {key.replace(/_/g, " ")}
                  </span>
                  <span className="text-[#9281f7]">{pillar.percentage}%</span>
                </div>
                <div className="w-full h-1.5 bg-[#292d30] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[#9281f7]"
                    style={{ width: `${pillar.percentage}%` }}
                  />
                </div>
                <div className="text-xs font-mono text-[#a1a4a5]">
                  Score: {pillar.score} / {pillar.max} pts
                </div>
              </div>
            ))}
          </div>

          {/* Actionable Recommendations Banner */}
          {geo.recommendations?.length > 0 && (
            <div className="p-6 rounded-[16px] bg-[#000000] border border-[#9281f7]/50 space-y-3 shadow-subtle">
              <div className="flex items-center gap-2 text-xs font-mono text-[#9281f7] uppercase tracking-wider">
                <Sparkles className="h-4 w-4" />
                <span>Actionable Recommendations to Maximize AI Citations</span>
              </div>
              <ul className="space-y-2 text-xs font-sans text-[#f0f0f0] list-disc list-inside">
                {geo.recommendations.map((rec: string, idx: number) => (
                  <li key={idx} className="leading-relaxed">{rec}</li>
                ))}
              </ul>
            </div>
          )}

          {/* AI Engine Strategic Positioning & Citation Strategy */}
          {aiInsights && (
            <div className="p-6 rounded-[16px] bg-[#000000] border border-[#9281f7]/60 space-y-5 shadow-subtle relative overflow-hidden">
              <div className="absolute top-0 right-0 w-64 h-64 bg-[#9281f7]/5 rounded-full blur-3xl pointer-events-none" />
              
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#292d30]">
                <div className="flex items-center gap-2">
                  <span className="p-1 rounded bg-[#9281f7]/10 text-[#9281f7]">
                    <Sparkles className="h-4 w-4" />
                  </span>
                  <div>
                    <h3 className="text-sm font-sans font-semibold text-[#ffffff]">
                      AI Engine Strategic Positioning &amp; Citation Strategy
                    </h3>
                    <p className="text-[11px] font-mono text-[#a1a4a5]">
                      Evaluated for Perplexity, ChatGPT Search, and Google Gemini citations
                    </p>
                  </div>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#9281f7]/10 text-[#9281f7] border border-[#9281f7]/30 uppercase self-start sm:self-auto">
                  GEO Ready
                </span>
              </div>

              {/* Brand Positioning & Citation Readiness */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-[12px] bg-[#0a0a0f] border border-[#292d30] space-y-1.5">
                  <div className="text-[10px] font-mono uppercase tracking-wider text-[#a1a4a5]">
                    Recognized Brand Entity
                  </div>
                  <div className="text-xs font-sans text-[#f0f0f0] leading-relaxed">
                    {aiInsights.brand_positioning}
                  </div>
                </div>

                <div className="p-4 rounded-[12px] bg-[#0a0a0f] border border-[#292d30] space-y-1.5">
                  <div className="text-[10px] font-mono uppercase tracking-wider text-[#9281f7]">
                    Citation Readiness Verdict
                  </div>
                  <div className="text-xs font-sans text-[#f0f0f0] leading-relaxed">
                    {aiInsights.geo_readiness}
                  </div>
                </div>
              </div>

              {/* Quotability Actions */}
              {Boolean(aiInsights.llm_quotability_actions && aiInsights.llm_quotability_actions.length > 0) && (
                <div className="space-y-2">
                  <div className="text-[11px] font-mono text-[#ffffff] font-medium flex items-center gap-1.5">
                    <CheckCircle2 className="h-3.5 w-3.5 text-[#3ad389]" />
                    <span>Tactical LLM Quotability Actions</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {aiInsights.llm_quotability_actions!.map((act: string, idx: number) => (
                      <div key={idx} className="p-3 rounded-[8px] bg-[#08090d] border border-[#292d30] text-xs font-sans text-[#c8cbd0] flex items-start gap-2">
                        <span className="text-[#9281f7] font-mono text-[10px] mt-0.5">#{idx + 1}</span>
                        <span className="leading-snug">{act}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* High-CTR Synthesized Title & Meta with Copy buttons */}
              {(aiInsights.high_ctr_serp_title || aiInsights.high_ctr_meta_description) && (
                <div className="p-4 rounded-[12px] bg-[#08090d] border border-[#292d30] space-y-3">
                  <div className="text-[11px] font-mono text-[#ffffff] font-medium">
                    AI-Optimized SERP Title &amp; Description
                  </div>
                  
                  {aiInsights.high_ctr_serp_title && (
                    <div className="flex items-center justify-between gap-3 text-xs font-sans bg-[#000000] p-2.5 rounded-[8px] border border-[#292d30]">
                      <div className="min-w-0 flex-1">
                        <span className="text-[10px] font-mono text-[#a1a4a5] block">Optimized Title:</span>
                        <span className="text-[#8ab4f8] font-medium truncate block">{aiInsights.high_ctr_serp_title}</span>
                      </div>
                      <button
                        onClick={() => copyToClipboard(aiInsights.high_ctr_serp_title!, setCopiedTitle)}
                        className="px-2.5 py-1 rounded bg-[#1f2228] hover:bg-[#2b2e36] text-[10px] font-mono text-[#f0f0f0] flex items-center gap-1 shrink-0 transition-colors"
                      >
                        {copiedTitle ? <Check className="h-3 w-3 text-[#3ad389]" /> : <Copy className="h-3 w-3 text-[#a1a4a5]" />}
                        <span>{copiedTitle ? "Copied" : "Copy"}</span>
                      </button>
                    </div>
                  )}

                  {aiInsights.high_ctr_meta_description && (
                    <div className="flex items-center justify-between gap-3 text-xs font-sans bg-[#000000] p-2.5 rounded-[8px] border border-[#292d30]">
                      <div className="min-w-0 flex-1">
                        <span className="text-[10px] font-mono text-[#a1a4a5] block">Optimized Meta Description:</span>
                        <span className="text-[#bdc1c6] line-clamp-2">{aiInsights.high_ctr_meta_description}</span>
                      </div>
                      <button
                        onClick={() => copyToClipboard(aiInsights.high_ctr_meta_description!, setCopiedMeta)}
                        className="px-2.5 py-1 rounded bg-[#1f2228] hover:bg-[#2b2e36] text-[10px] font-mono text-[#f0f0f0] flex items-center gap-1 shrink-0 transition-colors"
                      >
                        {copiedMeta ? <Check className="h-3 w-3 text-[#3ad389]" /> : <Copy className="h-3 w-3 text-[#a1a4a5]" />}
                        <span>{copiedMeta ? "Copied" : "Copy"}</span>
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Keyword Gap Opportunities */}
              {Boolean(aiInsights.keyword_gaps && aiInsights.keyword_gaps.length > 0) && (
                <div className="space-y-2">
                  <div className="text-[11px] font-mono text-[#a1a4a5] uppercase tracking-wider">
                    High-Intent Keyword Gap Opportunities
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {aiInsights.keyword_gaps!.map((kw: string, idx: number) => (
                      <span key={idx} className="px-2.5 py-1 rounded-full bg-[#161820] border border-[#292d30] text-[11px] font-mono text-[#9281f7]">
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Detailed Pillar Checks Table */}
          <div className="space-y-4">
            <h3 className="text-sm font-mono text-[#ffffff] font-medium">
              4-PILLAR_SIGNAL_EVALUATION
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(geo.pillars).map(([key, pillar]: [string, any]) => (
                <div key={key} className="p-5 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-3">
                  <h4 className="text-xs font-mono uppercase text-[#9281f7] tracking-wider pb-2 border-b border-[#292d30]">
                    {key.replace(/_/g, " ")} ({pillar.score}/{pillar.max} pts)
                  </h4>
                  <div className="space-y-2">
                    {pillar.items?.map((item: any, i: number) => (
                      <div key={i} className="flex items-start justify-between gap-3 text-xs font-mono">
                        <div className="space-y-0.5">
                          <div className="text-[#ffffff] font-medium">{item.rule}</div>
                          <div className="text-[#a1a4a5] text-[11px]">{item.notes}</div>
                        </div>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold shrink-0 ${
                            item.status === "PASS"
                              ? "bg-[#3ad389]/10 text-[#3ad389] border border-[#3ad389]/30"
                              : item.status === "PARTIAL"
                              ? "bg-[#ffca16]/10 text-[#ffca16] border border-[#ffca16]/30"
                              : "bg-[#ff9592]/10 text-[#ff9592] border border-[#ff9592]/30"
                          }`}
                        >
                          {item.status} ({item.score}/{item.max})
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Technical & Crawl Diagnostics */}
      {activeTab === "technical" && tech && (
        <div className="space-y-6 animate-in fade-in duration-150">
          {/* Diagnostics Stat Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-4 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-1">
              <span className="text-[11px] font-mono text-[#a1a4a5]">HTTP STATUS</span>
              <div className="text-xl font-mono text-[#3ad389] font-semibold">{tech.status_code}</div>
            </div>
            <div className="p-4 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-1">
              <span className="text-[11px] font-mono text-[#a1a4a5]">RESPONSE TIME</span>
              <div className="text-xl font-mono text-[#ffffff] font-semibold">{tech.response_time_ms} ms</div>
            </div>
            <div className="p-4 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-1">
              <span className="text-[11px] font-mono text-[#a1a4a5]">CONTENT WORDS</span>
              <div className="text-xl font-mono text-[#ffffff] font-semibold">{tech.word_count}</div>
            </div>
            <div className="p-4 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-1">
              <span className="text-[11px] font-mono text-[#a1a4a5]">CANONICAL STATUS</span>
              <div className="text-xs font-mono text-[#9281f7] truncate">{tech.canonical?.present ? "Declared" : "Missing"}</div>
            </div>
          </div>

          {/* Technical Issues */}
          {tech.issues?.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-xs font-mono text-[#ffffff] uppercase tracking-wider">
                Flagged Technical Vulnerabilities ({tech.issues.length})
              </h3>
              <div className="space-y-2">
                {tech.issues.map((iss: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-[8px] bg-[#000000] border border-[#292d30] flex items-start gap-3 text-xs font-mono"
                  >
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-semibold shrink-0 ${
                        iss.severity === "CRITICAL"
                          ? "bg-[#ff9592]/20 text-[#ff9592] border border-[#ff9592]/40"
                          : iss.severity === "HIGH"
                          ? "bg-[#ffca16]/20 text-[#ffca16] border border-[#ffca16]/40"
                          : "bg-[#292d30] text-[#a1a4a5]"
                      }`}
                    >
                      {iss.severity}
                    </span>
                    <div className="space-y-0.5 flex-1">
                      <span className="text-[#ffffff] font-medium">{iss.field}: </span>
                      <span className="text-[#a1a4a5]">{iss.message}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Headings Hierarchy */}
          <div className="p-6 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-4">
            <h3 className="text-xs font-mono text-[#ffffff] uppercase tracking-wider pb-2 border-b border-[#292d30]">
              Heading Tree Hierarchy
            </h3>
            <div className="space-y-2 text-xs font-mono">
              <div className="text-[#9281f7]">H1 ({tech.headings?.h1_count}):</div>
              {tech.headings?.h1?.map((h: string, i: number) => (
                <div key={i} className="pl-4 text-[#ffffff] border-l border-[#292d30]">{h}</div>
              ))}
              <div className="text-[#9281f7] pt-2">H2 Subheadings ({tech.headings?.h2_count}):</div>
              {tech.headings?.h2?.map((h: string, i: number) => (
                <div key={i} className="pl-4 text-[#a1a4a5] border-l border-[#292d30]">{h}</div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Playwright Hydration Gap */}
      {activeTab === "rendering" && rendering && (
        <div className="space-y-6 animate-in fade-in duration-150">
          {!rendering.tested ? (
            <div className="p-8 rounded-[16px] bg-[#000000] border border-[#292d30] text-center space-y-3">
              <Cpu className="h-6 w-6 text-[#9281f7] mx-auto" />
              <h3 className="text-base font-sans font-medium text-[#ffffff]">
                Playwright Hydration Test
              </h3>
              <p className="text-xs font-mono text-[#a1a4a5] max-w-md mx-auto">
                {rendering.note || "This audit ran in Quick mode. Re-run with 'Full Deep Audit (Playwright CSR)' on the launchpad to measure client-side hydration gaps."}
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Comparison Scorecard */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-5 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-2">
                  <span className="text-xs font-mono text-[#a1a4a5]">SERVER HTML (SSR)</span>
                  <div className="text-2xl font-mono text-[#ffffff]">{rendering.ssr?.word_count} words</div>
                  <div className="text-[11px] font-mono text-[#6e727a]">Initial crawl payload</div>
                </div>

                <div className="p-5 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-2">
                  <span className="text-xs font-mono text-[#9281f7]">PLAYWRIGHT RENDERED (CSR)</span>
                  <div className="text-2xl font-mono text-[#9281f7]">{rendering.csr?.word_count} words</div>
                  <div className="text-[11px] font-mono text-[#6e727a]">Post-JS hydration DOM</div>
                </div>

                <div className="p-5 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-2">
                  <span className="text-xs font-mono text-[#a1a4a5]">HYDRATION GAP</span>
                  <div className="text-2xl font-mono text-[#ffffff]">
                    +{rendering.words_difference} words
                  </div>
                  <div className="text-[11px] font-mono text-[#6e727a]">
                    Growth ratio: {rendering.word_growth_ratio}x
                  </div>
                </div>
              </div>

              {/* Findings */}
              <div className="p-6 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-[#292d30]">
                  <span className="text-xs font-mono uppercase text-[#ffffff]">
                    Hydration Gap Audit Findings
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${
                      rendering.risk_level === "HIGH"
                        ? "bg-[#ff9592]/20 text-[#ff9592] border border-[#ff9592]/40"
                        : "bg-[#3ad389]/20 text-[#3ad389] border border-[#3ad389]/40"
                    }`}
                  >
                    Risk Level: {rendering.risk_level}
                  </span>
                </div>
                <div className="space-y-3">
                  {rendering.findings?.map((f: any, idx: number) => (
                    <div key={idx} className="space-y-1 text-xs font-mono">
                      <div className="text-[#ffffff] font-medium">{f.title}</div>
                      <div className="text-[#a1a4a5] leading-relaxed">{f.description}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 4: JSON-LD Schemas */}
      {activeTab === "schemas" && schemas && (
        <div className="space-y-6 animate-in fade-in duration-150">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-sans font-medium text-[#ffffff]">
                Structured Data Knowledge Graph
              </h3>
              <p className="text-xs font-mono text-[#a1a4a5]">
                {schemas.detected_count} schemas found on page • 5 valid templates generated
              </p>
            </div>
            <button
              onClick={() => copyToClipboard(schemas.html_snippet_sample, setCopiedSchema)}
              className="px-3 py-1.5 rounded-[6px] bg-[#000000] border border-[#292d30] hover:border-[#ffffff] text-xs font-mono text-[#ffffff] flex items-center gap-1.5 transition-all"
            >
              {copiedSchema ? <Check className="h-3.5 w-3.5 text-[#3ad389]" /> : <Copy className="h-3.5 w-3.5" />}
              <span>{copiedSchema ? "Copied" : "Copy Organization Schema"}</span>
            </button>
          </div>

          {/* Generated Schemas Tabs / Code Blocks */}
          <div className="space-y-4">
            {Object.entries(schemas.generated_templates || {}).map(([sname, sdata]: [string, any]) => {
              if (!sdata) return null;
              return (
                <div key={sname} className="rounded-[16px] bg-[#000000] border border-[#292d30] overflow-hidden">
                  <div className="p-3 border-b border-[#292d30] flex items-center justify-between text-xs font-mono">
                    <span className="text-[#9281f7] uppercase font-semibold">{sname} Schema (JSON-LD)</span>
                    <button
                      onClick={() => copyToClipboard(JSON.stringify(sdata, null, 2), setCopiedSchema)}
                      className="text-[#a1a4a5] hover:text-[#ffffff] flex items-center gap-1 transition-colors"
                    >
                      <Copy className="h-3 w-3" />
                      <span>Copy</span>
                    </button>
                  </div>
                  <pre className="p-4 text-xs font-mono text-[#f0f0f0] overflow-x-auto max-h-64 scrollbar-none">
                    {JSON.stringify(sdata, null, 2)}
                  </pre>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Tab 5: Meta & SERP Preview */}
      {activeTab === "meta" && meta && (
        <div className="space-y-8 animate-in fade-in duration-150">
          {/* Google SERP Card Preview */}
          <div className="p-6 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-3 max-w-2xl shadow-subtle">
            <span className="text-xs font-mono text-[#9281f7] uppercase tracking-wider">
              Google SERP Visual Preview
            </span>
            <div className="space-y-1.5 pt-2">
              <div className="text-xs font-sans text-[#a1a4a5] flex items-center gap-1.5">
                <span>{meta.serp_simulation?.domain}</span>
                <span>›</span>
                <span className="truncate">{session.url}</span>
              </div>
              <h3 className="text-lg font-sans text-[#8ab4f8] hover:underline cursor-pointer leading-snug">
                {meta.serp_simulation?.title}
              </h3>
              <p className="text-xs font-sans text-[#bdc1c6] leading-relaxed line-clamp-2">
                {meta.serp_simulation?.description}
              </p>
            </div>
          </div>

          {/* 3 Title Tag Variants */}
          <div className="space-y-4">
            <h3 className="text-xs font-mono uppercase text-[#ffffff] tracking-wider">
              Recommended Title Tag Variants
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {meta.title_variants?.map((tv: any, idx: number) => (
                <div key={idx} className="p-4 rounded-[12px] bg-[#000000] border border-[#292d30] space-y-2 flex flex-col justify-between">
                  <div className="space-y-1">
                    <span className="text-[11px] font-mono text-[#9281f7]">{tv.variant}</span>
                    <p className="text-xs font-sans text-[#ffffff] font-medium leading-snug">{tv.title}</p>
                  </div>
                  <div className="pt-2 border-t border-[#292d30] flex items-center justify-between text-[10px] font-mono text-[#6e727a]">
                    <span>{tv.char_count} chars</span>
                    <button
                      onClick={() => copyToClipboard(tv.title, setCopiedMeta)}
                      className="text-[#a1a4a5] hover:text-[#ffffff] flex items-center gap-1"
                    >
                      <Copy className="h-2.5 w-2.5" />
                      <span>Copy</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Code Block Snippet */}
          <div className="rounded-[16px] bg-[#000000] border border-[#292d30] overflow-hidden">
            <div className="p-3 border-b border-[#292d30] flex items-center justify-between text-xs font-mono">
              <span className="text-[#a1a4a5]">Ready-to-Embed &lt;head&gt; HTML Block</span>
              <button
                onClick={() => copyToClipboard(meta.html_code_block, setCopiedMeta)}
                className="text-[#9281f7] hover:underline flex items-center gap-1"
              >
                {copiedMeta ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                <span>{copiedMeta ? "Copied" : "Copy Code"}</span>
              </button>
            </div>
            <pre className="p-4 text-xs font-mono text-[#f0f0f0] overflow-x-auto max-h-64 scrollbar-none">
              {meta.html_code_block}
            </pre>
          </div>
        </div>
      )}

      {/* Tab 6: Image SEO */}
      {activeTab === "images" && images && (
        <div className="space-y-6 animate-in fade-in duration-150">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-4 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-1">
              <span className="text-[11px] font-mono text-[#a1a4a5]">TOTAL IMAGES</span>
              <div className="text-xl font-mono text-[#ffffff] font-semibold">{images.total_images}</div>
            </div>
            <div className="p-4 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-1">
              <span className="text-[11px] font-mono text-[#a1a4a5]">ALT COVERAGE</span>
              <div className="text-xl font-mono text-[#3ad389] font-semibold">{images.alt_coverage_percent}%</div>
            </div>
            <div className="p-4 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-1">
              <span className="text-[11px] font-mono text-[#a1a4a5]">MODERN FORMAT (WEBP)</span>
              <div className="text-xl font-mono text-[#9281f7] font-semibold">{images.modern_format_percent}%</div>
            </div>
            <div className="p-4 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-1">
              <span className="text-[11px] font-mono text-[#a1a4a5]">CLS DIMENSIONS</span>
              <div className="text-xl font-mono text-[#3b9eff] font-semibold">{images.cls_safe_percent}%</div>
            </div>
          </div>

          {/* Images Table */}
          <div className="rounded-[16px] bg-[#000000] border border-[#292d30] overflow-hidden">
            <div className="p-4 border-b border-[#292d30] text-xs font-mono text-[#ffffff] font-medium">
              Image Assets Audit ({images.images?.length || 0})
            </div>
            <div className="divide-y divide-[#292d30] max-h-96 overflow-y-auto">
              {images.images?.map((img: any, idx: number) => (
                <div key={idx} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
                  <div className="space-y-1 truncate max-w-md">
                    <div className="text-[#ffffff] truncate">{img.src}</div>
                    <div className="text-[#a1a4a5] text-[11px]">Alt: &quot;{img.alt}&quot;</div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="px-2 py-0.5 rounded text-[10px] bg-[#000000] border border-[#292d30] text-[#a1a4a5]">
                      {img.format}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        img.has_alt
                          ? "bg-[#3ad389]/10 text-[#3ad389] border border-[#3ad389]/30"
                          : "bg-[#ff9592]/10 text-[#ff9592] border border-[#ff9592]/30"
                      }`}
                    >
                      {img.has_alt ? "ALT OK" : "NO ALT"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 7: SEO Drift */}
      {activeTab === "drift" && drift && (
        <div className="space-y-6 animate-in fade-in duration-150">
          <div className="p-6 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#292d30]">
              <span className="text-xs font-mono uppercase text-[#ffffff]">
                SEO Drift &amp; Regression Baseline
              </span>
              <span
                className={`px-2.5 py-1 rounded text-xs font-mono font-semibold ${
                  drift.drift_status === "REGRESSION_DETECTED"
                    ? "bg-[#ff9592]/20 text-[#ff9592] border border-[#ff9592]/40"
                    : "bg-[#3ad389]/20 text-[#3ad389] border border-[#3ad389]/40"
                }`}
              >
                {drift.drift_status}
              </span>
            </div>

            <div className="text-xs font-mono text-[#a1a4a5]">
              {drift.has_baseline
                ? `Compared with baseline from ${new Date(drift.baseline_timestamp || Date.now()).toLocaleString()}. Score Delta: ${drift.score_delta > 0 ? "+" : ""}${drift.score_delta} pts.`
                : "No previous baseline snapshot found for this domain. Current audit is now stored as the baseline for future regression checks."}
            </div>

            {drift.regressions?.length > 0 && (
              <div className="space-y-2">
                <span className="text-xs font-mono text-[#ff9592] font-semibold">Regressions:</span>
                {drift.regressions.map((reg: string, idx: number) => (
                  <div key={idx} className="p-3 rounded bg-[#ff9592]/10 border border-[#ff9592]/30 text-xs font-mono text-[#ff9592]">
                    {reg}
                  </div>
                ))}
              </div>
            )}

            {drift.improvements?.length > 0 && (
              <div className="space-y-2">
                <span className="text-xs font-mono text-[#3ad389] font-semibold">Improvements:</span>
                {drift.improvements.map((imp: string, idx: number) => (
                  <div key={idx} className="p-3 rounded bg-[#3ad389]/10 border border-[#3ad389]/30 text-xs font-mono text-[#3ad389]">
                    {imp}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
