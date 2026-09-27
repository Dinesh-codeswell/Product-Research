"use client";

import React, { useEffect, useState } from "react";
import {
  X,
  Activity,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Server,
  Shield,
  Layers,
  Sparkles,
  ExternalLink
} from "lucide-react";
import { getDoctorReport } from "@/lib/api";
import { DoctorReport, DoctorChannelInfo } from "@/lib/types";

interface DiagnosticDoctorModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function DiagnosticDoctorModal({ isOpen, onClose }: DiagnosticDoctorModalProps) {
  const [report, setReport] = useState<DoctorReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState<string>("all");

  const loadDoctor = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getDoctorReport();
      setReport(data);
    } catch (err: any) {
      setError(err.message || "Failed to load diagnostic health check");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadDoctor();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const channelList: DoctorChannelInfo[] = report?.channels ? Object.values(report.channels) : [];
  const filteredChannels = activeCategory === "all" 
    ? channelList 
    : channelList.filter(c => c.category === activeCategory);

  const categories = [
    { id: "all", label: "All Platforms" },
    { id: "developer", label: "Developer & Code" },
    { id: "social", label: "Social & Community" },
    { id: "video", label: "Video & Media" },
    { id: "web", label: "Web & Search" },
    { id: "business", label: "B2B & Careers" },
    { id: "finance", label: "Finance & Stocks" },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#000000]/80 backdrop-blur-[25px] p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-3xl rounded-[24px] bg-[#000000] border border-[#292d30] shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="p-6 border-b border-[#292d30] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-[8px] bg-[#9281f7]/10 border border-[#9281f7]/30 text-[#9281f7]">
              <Activity className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-sans font-medium text-[#ffffff]">
                  PulseRadar Diagnostic Doctor
                </h2>
                <span className="text-[10px] font-mono uppercase bg-[#3ad389]/10 text-[#3ad389] px-2 py-0.5 rounded border border-[#3ad389]/30">
                  Agent Reach Core
                </span>
              </div>
              <p className="text-xs font-mono text-[#a1a4a5]">
                Real-time reachability, active backends, and multi-channel telemetry
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={loadDoctor}
              disabled={loading}
              className="p-2 rounded-[6px] text-[#a1a4a5] hover:text-[#ffffff] border border-[#292d30] hover:border-[#ffffff]/40 transition-colors disabled:opacity-40"
              title="Re-run health probe"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin text-[#9281f7]" : ""}`} />
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-[6px] text-[#a1a4a5] hover:text-[#ffffff] border border-[#292d30] hover:border-[#ffffff]/40 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Telemetry Scoreboard */}
        {report && (
          <div className="grid grid-cols-4 border-b border-[#292d30] bg-[#0a0a0a] divide-x divide-[#292d30] text-center py-3">
            <div>
              <div className="text-lg font-sans font-semibold text-[#ffffff]">
                {report.total_channels}
              </div>
              <div className="text-[10px] font-mono uppercase text-[#a1a4a5]">
                Total Platforms
              </div>
            </div>
            <div>
              <div className="text-lg font-sans font-semibold text-[#3ad389]">
                {report.ok_channels}
              </div>
              <div className="text-[10px] font-mono uppercase text-[#a1a4a5]">
                Operational
              </div>
            </div>
            <div>
              <div className="text-lg font-sans font-semibold text-[#ffca16]">
                {report.warn_channels}
              </div>
              <div className="text-[10px] font-mono uppercase text-[#a1a4a5]">
                Warnings / Fallback
              </div>
            </div>
            <div>
              <div className="text-lg font-sans font-semibold text-[#ff9592]">
                {report.error_channels}
              </div>
              <div className="text-[10px] font-mono uppercase text-[#a1a4a5]">
                Offline
              </div>
            </div>
          </div>
        )}

        {/* Category Tabs */}
        <div className="px-6 pt-4 pb-2 border-b border-[#292d30] flex items-center gap-2 overflow-x-auto">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className={`px-3 py-1 rounded-full text-xs font-mono whitespace-nowrap transition-colors ${
                activeCategory === cat.id
                  ? "bg-[#9281f7] text-[#000000] font-medium"
                  : "bg-[#000000] border border-[#292d30] text-[#a1a4a5] hover:text-[#ffffff]"
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Channels List */}
        <div className="p-6 overflow-y-auto space-y-3 flex-1">
          {loading && !report && (
            <div className="py-16 text-center text-xs font-mono text-[#a1a4a5] flex items-center justify-center gap-2">
              <RefreshCw className="h-4 w-4 animate-spin text-[#9281f7]" />
              <span>Probing upstream channels & verifying failover chains...</span>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-[8px] bg-[#ff9592]/10 border border-[#ff9592]/30 text-[#ff9592] text-xs font-mono">
              {error}
            </div>
          )}

          {filteredChannels.map((ch) => (
            <div
              key={ch.id}
              className="p-4 rounded-[16px] bg-[#000000] border border-[#292d30] hover:border-[#6e727a] transition-all space-y-2.5"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  {ch.status === "ok" ? (
                    <CheckCircle2 className="h-4 w-4 text-[#3ad389] shrink-0" />
                  ) : ch.status === "warn" ? (
                    <AlertTriangle className="h-4 w-4 text-[#ffca16] shrink-0" />
                  ) : (
                    <XCircle className="h-4 w-4 text-[#ff9592] shrink-0" />
                  )}
                  <span className="font-sans font-medium text-sm text-[#ffffff]">
                    {ch.display_name}
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#292d30] text-[#a1a4a5] uppercase">
                    {ch.category}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                    ch.tier === 0 
                      ? "bg-[#3ad389]/10 text-[#3ad389] border-[#3ad389]/30" 
                      : ch.tier === 1 
                      ? "bg-[#3b9eff]/10 text-[#3b9eff] border-[#3b9eff]/30" 
                      : "bg-[#ffca16]/10 text-[#ffca16] border-[#ffca16]/30"
                  }`}>
                    {ch.tier === 0 ? "Tier 0: Zero-Auth" : ch.tier === 1 ? "Tier 1: Key/Token" : "Tier 2: Browser Session"}
                  </span>
                  <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded font-medium ${
                    ch.status === "ok" 
                      ? "bg-[#3ad389]/20 text-[#3ad389]" 
                      : ch.status === "warn" 
                      ? "bg-[#ffca16]/20 text-[#ffca16]" 
                      : "bg-[#ff9592]/20 text-[#ff9592]"
                  }`}>
                    {ch.status}
                  </span>
                </div>
              </div>

              <p className="text-xs font-mono text-[#a1a4a5] leading-relaxed">
                {ch.message}
              </p>

              <div className="pt-2 border-t border-[#292d30]/60 flex items-center justify-between text-[11px] font-mono text-[#6e727a]">
                <div className="flex items-center gap-1.5">
                  <Server className="h-3 w-3 text-[#9281f7]" />
                  <span>Active Backend:</span>
                  <span className="text-[#f0f0f0] font-medium">
                    {ch.active_backend || "auto"}
                  </span>
                </div>

                <div className="flex items-center gap-1 text-[10px]">
                  <span>Fallbacks:</span>
                  <span className="text-[#a1a4a5]">
                    {ch.backends?.join(" → ") || "none"}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-[#292d30] bg-[#0a0a0a] flex items-center justify-between text-xs font-mono text-[#a1a4a5]">
          <div className="flex items-center gap-2">
            <Shield className="h-3.5 w-3.5 text-[#3ad389]" />
            <span>Local Cookie Isolation • Zero Token Leakage • Side-Effect Free Health Probing</span>
          </div>

          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-[6px] bg-[#000000] border border-[#292d30] text-xs text-[#ffffff] hover:border-[#ffffff] transition-all"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
