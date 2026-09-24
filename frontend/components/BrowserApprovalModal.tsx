"use client";

import React from "react";
import { X, Monitor, ShieldCheck, Check, Sparkles, Terminal, Eye } from "lucide-react";

interface BrowserApprovalModalProps {
  isOpen: boolean;
  onClose: () => void;
  onApprove: () => void;
  onFallbackFocus: () => void;
  query: string;
}

export function BrowserApprovalModal({
  isOpen,
  onClose,
  onApprove,
  onFallbackFocus,
  query,
}: BrowserApprovalModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#000000]/80 backdrop-blur-[25px] p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-xl rounded-[24px] bg-[#000000] border border-[#292d30] shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-[#292d30] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-[6px] bg-[#000000] border border-[#292d30] text-[#9281f7]">
              <Monitor className="h-4 w-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-sans font-medium text-[#ffffff]">
                  Authorize Agent Browser Session
                </h2>
                <span className="text-[10px] font-mono text-[#3ad389] bg-[#000000] px-1.5 py-0.2 rounded border border-[#292d30]">
                  HUMAN_IN_THE_LOOP
                </span>
              </div>
              <p className="text-xs font-mono text-[#a1a4a5]">
                Permission required to spawn and control visible browser
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-[6px] text-[#a1a4a5] hover:text-[#ffffff] border border-transparent hover:border-[#292d30] transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-5 text-xs font-sans">
          <p className="text-sm text-[#f0f0f0] leading-relaxed">
            The autonomous research agent is requesting authorization to launch a <strong>parallel, visible browser instance</strong> on your machine to investigate:
          </p>

          <div className="p-3.5 rounded-[6px] bg-[#000000] border border-[#292d30] font-mono text-xs text-[#ffffff] flex items-center gap-2">
            <span className="text-[#9281f7]">query:</span>
            <span className="truncate">"{query}"</span>
          </div>

          {/* Capabilities Grid */}
          <div className="space-y-2.5 pt-2">
            <div className="p-3.5 rounded-[16px] bg-[#000000] border border-[#292d30] flex items-start gap-3">
              <Eye className="h-4 w-4 text-[#9281f7] shrink-0 mt-0.5" />
              <div>
                <span className="font-mono text-[#ffffff] block mb-0.5">Real-Time Visual Control</span>
                <span className="text-[#a1a4a5] text-[11px] leading-relaxed">
                  A real browser window will appear on your desktop. You will see the agent type search queries, scroll discussion threads, and highlight target quotes with violet borders.
                </span>
              </div>
            </div>

            <div className="p-3.5 rounded-[16px] bg-[#000000] border border-[#292d30] flex items-start gap-3">
              <Terminal className="h-4 w-4 text-[#3ad389] shrink-0 mt-0.5" />
              <div>
                <span className="font-mono text-[#ffffff] block mb-0.5">Dashboard Screencast Stream</span>
                <span className="text-[#a1a4a5] text-[11px] leading-relaxed">
                  Live screencast frames and action telemetry will also stream directly to your PulseRadar dashboard so you can monitor progress anywhere.
                </span>
              </div>
            </div>

            <div className="p-3.5 rounded-[16px] bg-[#000000] border border-[#292d30] flex items-start gap-3">
              <ShieldCheck className="h-4 w-4 text-[#70b8ff] shrink-0 mt-0.5" />
              <div>
                <span className="font-mono text-[#ffffff] block mb-0.5">Full Privacy & Hand-off</span>
                <span className="text-[#a1a4a5] text-[11px] leading-relaxed">
                  The agent only accesses target research channels. You can pause the agent or switch back to silent Focus Mode at any time.
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-[#292d30] flex flex-col sm:flex-row items-center justify-between gap-3 bg-[#000000]">
          <button
            type="button"
            onClick={onFallbackFocus}
            className="w-full sm:w-auto px-4 py-2.5 rounded-[6px] bg-[#000000] border border-[#292d30] hover:border-[#ffffff] text-xs font-mono text-[#a1a4a5] hover:text-[#ffffff] transition-all text-center"
          >
            Stay in Focus Mode (Silent)
          </button>

          <button
            type="button"
            onClick={onApprove}
            className="w-full sm:w-auto px-5 py-2.5 rounded-[6px] bg-[#3b9eff] hover:bg-[#3b9eff]/90 text-white font-sans font-medium text-xs flex items-center justify-center gap-2 transition-all shadow-subtle"
          >
            <Check className="h-4 w-4" />
            <span>Approve & Launch Live Browser</span>
          </button>
        </div>
      </div>
    </div>
  );
}
