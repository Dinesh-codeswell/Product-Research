"use client";

import React, { useState } from "react";
import { FileText, Sparkles, Copy, Check, Download, Loader2 } from "lucide-react";
import { generatePrd, getExportUrl } from "@/lib/api";

interface PrdStudioProps {
  sessionId: string;
  initialPrd?: string;
}

export function PrdStudio({ sessionId, initialPrd }: PrdStudioProps) {
  const [prdContent, setPrdContent] = useState<string>(initialPrd || "");
  const [customInstructions, setCustomInstructions] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const res = await generatePrd(sessionId, customInstructions.trim() || undefined);
      setPrdContent(res.markdown_content);
    } catch (e: any) {
      alert("Failed to generate PRD: " + e.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(prdContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Action Toolbar (Resend 16px Card, 1px #292d30 Border) */}
      <div className="p-5 rounded-[16px] bg-[#000000] border border-[#292d30] flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <input
            type="text"
            value={customInstructions}
            onChange={(e) => setCustomInstructions(e.target.value)}
            placeholder="Focus instructions (e.g. 'Focus on edge latency, pricing cliffs, and RBAC')..."
            className="px-3.5 py-2 rounded-[6px] bg-[#000000] border border-[#292d30] text-xs font-sans text-[#ffffff] placeholder-[#464a4d] w-full sm:w-96 focus:outline-none focus:border-[#ffffff] transition-colors"
          />

          {/* Primary Signal Blue Action Button */}
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="px-4 py-2 rounded-[6px] bg-[#3b9eff] hover:bg-[#3b9eff]/90 text-[#ffffff] font-sans font-medium text-xs flex items-center gap-2 shrink-0 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isGenerating ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                <span>Synthesizing...</span>
              </>
            ) : (
              <>
                <Sparkles className="h-3.5 w-3.5" />
                <span>{prdContent ? "Regenerate PRD" : "Generate PRD"}</span>
              </>
            )}
          </button>
        </div>

        {prdContent && (
          <div className="flex items-center gap-2.5 w-full sm:w-auto justify-end">
            <button
              onClick={handleCopy}
              className="px-3.5 py-2 rounded-[6px] bg-[#000000] border border-[#292d30] hover:border-[#ffffff] text-xs font-mono text-[#f0f0f0] flex items-center gap-2 transition-all"
            >
              {copied ? (
                <Check className="h-3.5 w-3.5 text-[#3ad389]" />
              ) : (
                <Copy className="h-3.5 w-3.5 text-[#a1a4a5]" />
              )}
              <span>{copied ? "Copied" : "Copy Spec"}</span>
            </button>

            <a
              href={getExportUrl(sessionId, "markdown")}
              download
              className="px-3.5 py-2 rounded-[6px] bg-[#000000] border border-[#292d30] hover:border-[#ffffff] text-xs font-mono text-[#ffffff] flex items-center gap-2 transition-all"
            >
              <Download className="h-3.5 w-3.5 text-[#a1a4a5]" />
              <span>Download .md</span>
            </a>
          </div>
        )}
      </div>

      {/* PRD Terminal Window (Resend Code Block Pattern) */}
      {prdContent ? (
        <div className="p-6 sm:p-8 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-4 shadow-subtle">
          {/* Traffic Light Header */}
          <div className="flex items-center justify-between pb-3 border-b border-[#292d30]">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-[#292d30]" />
              <span className="h-2.5 w-2.5 rounded-full bg-[#292d30]" />
              <span className="h-2.5 w-2.5 rounded-full bg-[#292d30]" />
              <span className="text-xs font-mono text-[#a1a4a5] ml-2">
                PRODUCT_REQUIREMENTS_SPEC.md
              </span>
            </div>
            <span className="text-[11px] font-mono text-[#3ad389]">
              AUTONOMOUS_SPEC
            </span>
          </div>

          <div className="font-mono text-xs sm:text-sm text-[#f0f0f0] leading-relaxed whitespace-pre-wrap max-h-[640px] overflow-y-auto pr-2 selection:bg-[#9281f7]/30">
            {prdContent}
          </div>
        </div>
      ) : (
        <div className="p-16 rounded-[16px] bg-[#000000] border border-dashed border-[#292d30] text-center space-y-3">
          <div className="h-10 w-10 mx-auto rounded-[6px] bg-[#000000] border border-[#292d30] flex items-center justify-center text-[#6e727a]">
            <FileText className="h-5 w-5" />
          </div>
          <h4 className="text-sm font-sans font-medium text-[#ffffff]">
            No PRD Generated Yet
          </h4>
          <p className="text-xs font-sans text-[#a1a4a5] max-w-sm mx-auto">
            Click "Generate PRD" to automatically synthesize all verified customer pain points, workarounds, and quote citations into a structured product specification.
          </p>
        </div>
      )}
    </div>
  );
}
