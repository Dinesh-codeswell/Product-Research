"use client";

import React from "react";
import { Loader2 } from "lucide-react";
import { SSEProgressEvent } from "@/lib/types";

interface LiveProgressProps {
  progress: SSEProgressEvent | null;
  status: string;
}

export function LiveProgress({ progress, status }: LiveProgressProps) {
  const percent = progress?.percent ?? (status === "COMPLETED" ? 100 : 10);
  const message = progress?.message ?? "Dispatching unauthenticated multi-channel crawlers...";
  const stage = progress?.stage ?? "init";

  const getStageLabel = (st: string) => {
    if (st.includes("reddit")) return "Reddit Community Ingestion";
    if (st.includes("youtube")) return "YouTube Review Transcripts";
    if (st.includes("twitter")) return "Twitter / X Discourse Indexing";
    if (st.includes("cleaning")) return "Deduplication & Noise Stripping";
    if (st.includes("clustering")) return "Semantic Vector Agglomeration";
    if (st.includes("synthesizing")) return "Executive Grounding & PRD Synthesis";
    if (st.includes("completed")) return "Discovery Complete";
    return "Pipeline Orchestrator";
  };

  return (
    <div className="w-full max-w-3xl mx-auto p-6 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-4 shadow-subtle">
      {/* Terminal Bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-[#292d30]" />
            <span className="h-2.5 w-2.5 rounded-full bg-[#292d30]" />
            <span className="h-2.5 w-2.5 rounded-full bg-[#292d30]" />
          </div>

          <div className="flex items-center gap-2 pl-2 border-l border-[#292d30]">
            <span
              className={`h-2 w-2 rounded-full ${
                status === "COMPLETED"
                  ? "bg-[#3ad389]"
                  : status === "FAILED"
                  ? "bg-[#ff9592]"
                  : "bg-[#70b8ff] animate-pulse"
              }`}
            />
            <span className="text-xs font-mono uppercase tracking-wider text-[#a1a4a5]">
              {getStageLabel(stage)}
            </span>
          </div>
        </div>

        <span className="text-xs font-mono text-[#ffffff] px-2 py-0.5 rounded-[6px] border border-[#292d30] bg-[#000000]">
          {percent}%
        </span>
      </div>

      {/* Hairline 2px Progress Bar */}
      <div className="w-full h-1 rounded-full bg-[#292d30] overflow-hidden">
        <div
          className="h-full bg-[#3b9eff] transition-all duration-300 ease-out"
          style={{ width: `${percent}%` }}
        />
      </div>

      {/* Commit Mono Message Ticker */}
      <div className="flex items-center gap-2 text-xs text-[#a1a4a5] font-mono bg-[#000000] px-3.5 py-2 rounded-[6px] border border-[#292d30]">
        {status !== "COMPLETED" && status !== "FAILED" && (
          <Loader2 className="h-3 w-3 animate-spin text-[#9281f7] shrink-0" />
        )}
        <span className="truncate">{message}</span>
      </div>
    </div>
  );
}
