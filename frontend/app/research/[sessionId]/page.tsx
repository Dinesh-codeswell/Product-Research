"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  Download,
  Layers,
  FileCode,
  Share2,
  Check,
  RefreshCw,
  Radio,
  Monitor,
  Sparkles
} from "lucide-react";
import { getResearchSession, getExportUrl, getEventSourceUrl } from "@/lib/api";
import { ResearchSession, InsightCluster, SSEProgressEvent, BrowserActionEvent } from "@/lib/types";
import { LiveProgress } from "@/components/LiveProgress";
import { ClusterMatrix } from "@/components/ClusterMatrix";
import { QuoteDrawer } from "@/components/QuoteDrawer";
import { PrdStudio } from "@/components/PrdStudio";
import { SignalsExplorer } from "@/components/SignalsExplorer";
import { LiveBrowserViewport } from "@/components/LiveBrowserViewport";

export default function ResearchSessionPage() {
  const routeParams = useParams();
  const rawId = routeParams?.sessionId;
  const sessionId = Array.isArray(rawId) ? rawId[0] : (rawId as string) || "";

  const [session, setSession] = useState<ResearchSession | null>(null);
  const [activeTab, setActiveTab] = useState<"viewport" | "clusters" | "signals" | "prd">("clusters");
  const [selectedCluster, setSelectedCluster] = useState<InsightCluster | null>(null);
  const [progress, setProgress] = useState<SSEProgressEvent | null>(null);
  const [browserEvents, setBrowserEvents] = useState<BrowserActionEvent[]>([]);
  const [copiedLink, setCopiedLink] = useState(false);

  const fetchSession = async () => {
    try {
      const data = await getResearchSession(sessionId);
      setSession(data);
      if (data.execution_mode === "browser" && data.status === "RUNNING") {
        setActiveTab("viewport");
      }
    } catch (e) {
      console.error("Error fetching session:", e);
    }
  };

  useEffect(() => {
    fetchSession();

    // Setup SSE listener for live progress and browser actions
    const eventSource = new EventSource(getEventSourceUrl(sessionId));

    eventSource.onmessage = (event) => {
      try {
        const payload: SSEProgressEvent = JSON.parse(event.data);
        setProgress(payload);

        // Capture live browser agent screencast and action events
        if (payload.stage === "browser_action" && payload.data) {
          const actionEvt: BrowserActionEvent = {
            action: payload.data.action || "NAVIGATE",
            url: payload.data.url || "",
            title: payload.data.title,
            description: payload.data.description || payload.message,
            screenshot: payload.data.screenshot,
            channel: payload.data.channel,
            timestamp: payload.data.timestamp || new Date().toLocaleTimeString(),
            items_count: payload.data.items_count,
          };
          setBrowserEvents((prev) => [...prev, actionEvt]);
          setActiveTab((cur) => (cur === "clusters" ? "viewport" : cur));
        }

        if (payload.stage === "scraped") {
          fetchSession();
        }

        if (payload.stage === "completed" || payload.stage === "failed") {
          fetchSession();
          eventSource.close();
        }
      } catch (err) {
        console.error("Error parsing SSE event:", err);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      fetchSession();
    };

    return () => {
      eventSource.close();
    };
  }, [sessionId]);

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  if (!session) {
    return (
      <div className="py-24 text-center space-y-4">
        <LiveProgress progress={progress} status="RUNNING" />
      </div>
    );
  }

  const isBrowserMode = session.execution_mode === "browser" || browserEvents.length > 0;

  return (
    <div className="space-y-10">
      {/* Top Breadcrumb & Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-6 border-b border-[#292d30] pb-6">
        <div className="space-y-2">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-xs font-mono text-[#a1a4a5] hover:text-[#ffffff] transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>back_to_launchpad</span>
          </Link>

          <div className="flex flex-wrap items-center gap-3">
            <h1 className="font-serif text-3xl sm:text-4xl font-normal text-[#ffffff] tracking-[-0.01em]">
              {session.query}
            </h1>

            {/* Mode & Status Badge */}
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
              <span className="text-[#9281f7] uppercase">
                {session.execution_mode === "browser" ? "LIVE BROWSER" : "FOCUS"}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs font-mono text-[#6e727a]">
            <span>ID: {session.id.slice(0, 14)}</span>
            <span>•</span>
            <span>{session.total_items_scraped} raw signals harvested</span>
          </div>
        </div>

        {/* Resend Ghost Action Buttons */}
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
            href={getExportUrl(sessionId, "ai-bundle")}
            download
            className="px-3.5 py-2 rounded-[6px] bg-[#000000] border border-[#9281f7]/60 hover:border-[#9281f7] text-xs font-sans text-[#9281f7] hover:text-[#ffffff] flex items-center gap-2 transition-all duration-150 group shadow-subtle"
            title="Download full Markdown intelligence dossier formatted with instructions for Cursor, Claude Projects, and GPTs"
          >
            <Sparkles className="h-3.5 w-3.5 text-[#9281f7] group-hover:rotate-12 transition-transform" />
            <span>AI Agent Bundle (.md)</span>
          </a>

          <a
            href={getExportUrl(sessionId, "markdown")}
            download
            className="px-3.5 py-2 rounded-[6px] bg-[#000000] border border-[#292d30] hover:border-[#ffffff] text-xs font-sans text-[#ffffff] flex items-center gap-2 transition-all duration-150"
          >
            <Download className="h-3.5 w-3.5 text-[#a1a4a5]" />
            <span>Report (.md)</span>
          </a>

          <a
            href={getExportUrl(sessionId, "json")}
            download
            className="px-3 py-2 rounded-[6px] bg-[#000000] border border-[#292d30] hover:border-[#ffffff] text-xs font-sans text-[#a1a4a5] hover:text-[#ffffff] flex items-center gap-1.5 transition-all duration-150"
            title="Download raw structured JSON dataset"
          >
            <FileCode className="h-3.5 w-3.5 text-[#a1a4a5]" />
            <span>JSON</span>
          </a>
        </div>
      </div>

      {/* Live Progress Banner if running */}
      {session.status !== "COMPLETED" && (
        <LiveProgress progress={progress} status={session.status} />
      )}

      {/* Terminal Style Executive Summary Card */}
      {session.executive_summary && (
        <div className="p-6 sm:p-8 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-4 shadow-subtle">
          <div className="flex items-center justify-between pb-3 border-b border-[#292d30]">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-[#292d30]" />
              <span className="h-2.5 w-2.5 rounded-full bg-[#292d30]" />
              <span className="h-2.5 w-2.5 rounded-full bg-[#292d30]" />
              <span className="text-xs font-mono text-[#a1a4a5] ml-2">
                EXECUTIVE_SYNTHESIS.md
              </span>
            </div>
            <span className="text-[11px] font-mono text-[#9281f7]">
              VERIFIED EVIDENCE
            </span>
          </div>

          <div className="prose prose-invert max-w-none text-sm text-[#f0f0f0] leading-relaxed whitespace-pre-line font-sans">
            {session.executive_summary}
          </div>
        </div>
      )}

      {/* Navigation Tabs (Live Viewport vs Clusters vs Signals vs PRD Studio) */}
      <div className="flex items-center justify-between border-b border-[#292d30]">
        <div className="flex items-center gap-8 overflow-x-auto pb-0.5 scrollbar-none">
          {/* Live Browser Viewport Tab (Only when in browser mode or when browser events exist) */}
          {isBrowserMode && (
            <button
              onClick={() => setActiveTab("viewport")}
              className={`pb-3 text-sm font-sans font-medium flex items-center gap-2 border-b-2 transition-all duration-150 shrink-0 ${
                activeTab === "viewport"
                  ? "border-[#3b9eff] text-[#ffffff]"
                  : "border-transparent text-[#a1a4a5] hover:text-[#f0f0f0]"
              }`}
            >
              <Monitor className="h-4 w-4 text-[#9281f7]" />
              <span>Live Browser Viewport</span>
              {session.status === "RUNNING" && (
                <span className="h-1.5 w-1.5 rounded-full bg-[#3ad389] animate-pulse" />
              )}
            </button>
          )}

          <button
            onClick={() => setActiveTab("clusters")}
            className={`pb-3 text-sm font-sans font-medium flex items-center gap-2 border-b-2 transition-all duration-150 shrink-0 ${
              activeTab === "clusters"
                ? "border-[#ffffff] text-[#ffffff]"
                : "border-transparent text-[#a1a4a5] hover:text-[#f0f0f0]"
            }`}
          >
            <Layers className="h-4 w-4" />
            <span>Theme Clusters</span>
            <span className="text-xs font-mono text-[#9281f7] bg-[#000000] px-1.5 py-0.2 rounded-[6px] border border-[#292d30]">
              {session.clusters.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab("signals")}
            className={`pb-3 text-sm font-sans font-medium flex items-center gap-2 border-b-2 transition-all duration-150 shrink-0 ${
              activeTab === "signals"
                ? "border-[#ffffff] text-[#ffffff]"
                : "border-transparent text-[#a1a4a5] hover:text-[#f0f0f0]"
            }`}
          >
            <Radio className="h-4 w-4" />
            <span>All Raw Signals</span>
            <span className="text-xs font-mono text-[#9281f7] bg-[#000000] px-1.5 py-0.2 rounded-[6px] border border-[#292d30]">
              {session.feedbacks?.length || session.total_items_scraped}
            </span>
          </button>

          <button
            onClick={() => setActiveTab("prd")}
            className={`pb-3 text-sm font-sans font-medium flex items-center gap-2 border-b-2 transition-all duration-150 shrink-0 ${
              activeTab === "prd"
                ? "border-[#ffffff] text-[#ffffff]"
                : "border-transparent text-[#a1a4a5] hover:text-[#f0f0f0]"
            }`}
          >
            <FileCode className="h-4 w-4" />
            <span>PRD & Spec Studio</span>
          </button>
        </div>

        <button
          onClick={fetchSession}
          className="pb-3 text-[#6e727a] hover:text-[#ffffff] transition-colors shrink-0"
          title="Refresh Data"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === "viewport" && isBrowserMode ? (
        <LiveBrowserViewport
          events={browserEvents}
          isSessionRunning={session.status === "RUNNING"}
          feedbacks={session.feedbacks || []}
          clusters={session.clusters || []}
          sessionId={sessionId}
          onSwitchToFocusMode={() => setActiveTab("clusters")}
        />
      ) : activeTab === "clusters" ? (
        <ClusterMatrix
          clusters={session.clusters}
          onSelectCluster={(cl) => setSelectedCluster(cl)}
        />
      ) : activeTab === "signals" ? (
        <SignalsExplorer
          feedbacks={session.feedbacks || []}
          totalExpected={session.total_items_scraped}
        />
      ) : (
        <PrdStudio sessionId={sessionId} />
      )}

      {/* Quote Evidence Drawer */}
      <QuoteDrawer
        cluster={selectedCluster}
        onClose={() => setSelectedCluster(null)}
      />
    </div>
  );
}
