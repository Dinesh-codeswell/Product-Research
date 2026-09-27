"use client";

import React, { useState, useMemo, useEffect } from "react";
import {
  X,
  Youtube,
  Copy,
  Check,
  Download,
  Search,
  ExternalLink,
  Sparkles,
  Clock,
  FileText,
  Radio,
  Layers,
  RefreshCw,
  AlertCircle
} from "lucide-react";
import { YouTubeTranscriptData, YouTubeTranscriptSnippet } from "@/lib/types";
import { fetchYouTubeTranscript } from "@/lib/api";

interface YouTubeTranscriptModalProps {
  videoUrlOrId: string | null;
  videoTitle?: string;
  initialTranscriptData?: YouTubeTranscriptData | null;
  onClose: () => void;
}

export function YouTubeTranscriptModal({
  videoUrlOrId,
  videoTitle,
  initialTranscriptData,
  onClose,
}: YouTubeTranscriptModalProps) {
  const [data, setData] = useState<YouTubeTranscriptData | null>(initialTranscriptData || null);
  const [isLoading, setIsLoading] = useState<boolean>(!initialTranscriptData && !!videoUrlOrId);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [copiedText, setCopiedText] = useState(false);
  const [copiedPrompt, setCopiedPrompt] = useState(false);
  const [activeTab, setActiveTab] = useState<"cues" | "full_text">("cues");

  useEffect(() => {
    if (!videoUrlOrId) return;
    if (initialTranscriptData) {
      setData(initialTranscriptData);
      setIsLoading(false);
      return;
    }

    let isMounted = true;
    setIsLoading(true);
    setError(null);

    fetchYouTubeTranscript(videoUrlOrId)
      .then((res) => {
        if (isMounted) {
          setData(res);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || "Failed to retrieve YouTube transcript.");
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [videoUrlOrId, initialTranscriptData]);

  const filteredSnippets = useMemo(() => {
    if (!data?.snippets) return [];
    if (!searchQuery.trim()) return data.snippets;
    const q = searchQuery.toLowerCase();
    return data.snippets.filter((s) => s.text.toLowerCase().includes(q));
  }, [data?.snippets, searchQuery]);

  if (!videoUrlOrId) return null;

  const handleCopyFullTranscript = () => {
    if (!data?.text) return;
    navigator.clipboard.writeText(data.text);
    setCopiedText(true);
    setTimeout(() => setCopiedText(null as any), 2000);
  };

  const handleCopyAiPrompt = () => {
    if (!data?.text) return;
    const prompt = `Please analyze the following YouTube video transcript regarding "${videoTitle || data.video_id}".
Extract the core user pain points, workarounds, product feature requests, and competitor comparisons:

--- TRANSCRIPT (Video: ${data.video_url}) ---
${data.text}
`;
    navigator.clipboard.writeText(prompt);
    setCopiedPrompt(true);
    setTimeout(() => setCopiedPrompt(null as any), 2000);
  };

  const handleDownloadMarkdown = () => {
    if (!data) return;
    const title = videoTitle || `YouTube_Video_${data.video_id}`;
    let md = `# Video Transcript: ${title}\n\n`;
    md += `- **Video URL:** ${data.video_url}\n`;
    md += `- **Duration:** ${data.stats.formatted_duration} (${data.stats.duration_seconds}s)\n`;
    md += `- **Word Count:** ${data.stats.word_count} words\n`;
    md += `- **Language:** ${data.language} (${data.is_generated ? "Auto-generated" : "Manual subtitles"})\n\n`;
    md += `## Timestamped Transcript Cues\n\n`;

    for (const cue of data.snippets) {
      md += `**[${cue.timestamp}]** [Watch at ${cue.timestamp}](${cue.permalink})\n`;
      md += `> ${cue.text}\n\n`;
    }

    const blob = new Blob([md], { type: "text/markdown;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${title.replace(/[^a-z0-9_-]/gi, "_")}_transcript.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 bg-[#000000]/80 backdrop-blur-md flex items-center justify-center p-3 sm:p-6 animate-in fade-in duration-200">
      <div className="w-full max-w-4xl h-[90vh] bg-[#0c0d10] border border-[#292d30] rounded-[16px] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="p-5 border-b border-[#292d30] bg-[#121418] flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="h-9 w-9 rounded-[8px] bg-[#ff6465]/15 border border-[#ff6465]/30 flex items-center justify-center text-[#ff6465] shrink-0">
              <Youtube className="h-5 w-5" />
            </div>
            <div className="overflow-hidden">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono text-[#ff6465] font-bold tracking-wider uppercase bg-[#ff6465]/10 px-2 py-0.5 rounded-[4px] border border-[#ff6465]/20">
                  YouTube Real-Time Subtitles
                </span>
                {data && (
                  <span className="text-[11px] font-mono text-[#3ad389] flex items-center gap-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-[#3ad389]" />
                    <span>{data.is_generated ? "Auto-Subtitles" : "Manual Transcript"}</span>
                  </span>
                )}
              </div>
              <h3 className="text-sm sm:text-base font-sans font-medium text-[#ffffff] truncate mt-0.5">
                {videoTitle || (data ? `Video ${data.video_id}` : "Extracting Video Transcript...")}
              </h3>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-[6px] text-[#a1a4a5] hover:text-[#ffffff] hover:bg-[#1f2229] transition-colors shrink-0"
            title="Close modal"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content Body */}
        {isLoading ? (
          <div className="flex-1 flex flex-col items-center justify-center p-12 text-center space-y-3">
            <RefreshCw className="h-8 w-8 text-[#9281f7] animate-spin" />
            <h4 className="text-sm font-sans font-medium text-[#ffffff]">
              Extracting spoken subtitles and cues...
            </h4>
            <p className="text-xs font-mono text-[#a1a4a5] max-w-sm">
              Using zero-key YouTube transcript extraction to pull verbatim dialogue and timestamps directly from video audio tracks.
            </p>
          </div>
        ) : error ? (
          <div className="flex-1 flex flex-col items-center justify-center p-12 text-center space-y-3">
            <AlertCircle className="h-8 w-8 text-[#ff9592]" />
            <h4 className="text-sm font-sans font-medium text-[#ffffff]">
              Transcript Unavailable
            </h4>
            <p className="text-xs font-mono text-[#a1a4a5] max-w-md">
              {error}
            </p>
            {data?.video_url && (
              <a
                href={data.video_url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] bg-[#181a20] border border-[#292d30] hover:border-[#ffffff] text-xs font-mono text-[#ffffff]"
              >
                <span>Open Video Directly on YouTube</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </div>
        ) : data ? (
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Metadata Ribbon & Stats */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 p-4 border-b border-[#292d30] bg-[#0c0d10] text-xs font-mono">
              <div className="p-2.5 rounded-[6px] bg-[#121418] border border-[#292d30]">
                <div className="text-[10px] text-[#6e727a] uppercase">Duration</div>
                <div className="text-xs font-medium text-[#ffffff] mt-0.5 flex items-center gap-1">
                  <Clock className="h-3 w-3 text-[#9281f7]" />
                  <span>{data.stats.formatted_duration}</span>
                </div>
              </div>

              <div className="p-2.5 rounded-[6px] bg-[#121418] border border-[#292d30]">
                <div className="text-[10px] text-[#6e727a] uppercase">Subtitle Cues</div>
                <div className="text-xs font-medium text-[#ffffff] mt-0.5 flex items-center gap-1">
                  <Radio className="h-3 w-3 text-[#3ad389]" />
                  <span>{data.stats.snippets_count} cues</span>
                </div>
              </div>

              <div className="p-2.5 rounded-[6px] bg-[#121418] border border-[#292d30]">
                <div className="text-[10px] text-[#6e727a] uppercase">Word Count</div>
                <div className="text-xs font-medium text-[#ffffff] mt-0.5 flex items-center gap-1">
                  <FileText className="h-3 w-3 text-[#ffca16]" />
                  <span>{data.stats.word_count.toLocaleString()} words</span>
                </div>
              </div>

              <div className="p-2.5 rounded-[6px] bg-[#121418] border border-[#292d30]">
                <div className="text-[10px] text-[#6e727a] uppercase">Language</div>
                <div className="text-xs font-medium text-[#ffffff] mt-0.5 uppercase truncate">
                  {data.language || "English"}
                </div>
              </div>
            </div>

            {/* Action Toolbar & Search */}
            <div className="p-3 border-b border-[#292d30] bg-[#121418] flex flex-wrap items-center justify-between gap-3">
              {/* Tab Switcher & Search */}
              <div className="flex items-center gap-2 flex-1 min-w-[240px]">
                <div className="flex items-center bg-[#181a20] p-0.5 rounded-[6px] border border-[#292d30]">
                  <button
                    onClick={() => setActiveTab("cues")}
                    className={`px-3 py-1 rounded-[4px] text-xs font-mono transition-all ${
                      activeTab === "cues"
                        ? "bg-[#9281f7]/20 text-[#ffffff] border border-[#9281f7]/40"
                        : "text-[#a1a4a5] hover:text-[#ffffff]"
                    }`}
                  >
                    Timestamp Cues
                  </button>
                  <button
                    onClick={() => setActiveTab("full_text")}
                    className={`px-3 py-1 rounded-[4px] text-xs font-mono transition-all ${
                      activeTab === "full_text"
                        ? "bg-[#9281f7]/20 text-[#ffffff] border border-[#9281f7]/40"
                        : "text-[#a1a4a5] hover:text-[#ffffff]"
                    }`}
                  >
                    Full Text
                  </button>
                </div>

                {activeTab === "cues" && (
                  <div className="relative flex-1 max-w-xs">
                    <Search className="h-3.5 w-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-[#6e727a]" />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search spoken dialogue..."
                      className="w-full pl-8 pr-3 py-1 bg-[#181a20] border border-[#292d30] rounded-[6px] text-xs text-[#ffffff] placeholder-[#6e727a] outline-none focus:border-[#9281f7]"
                    />
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCopyFullTranscript}
                  className="px-2.5 py-1 rounded-[6px] bg-[#181a20] border border-[#292d30] hover:border-[#ffffff] text-xs font-mono text-[#a1a4a5] hover:text-[#ffffff] transition-all flex items-center gap-1.5"
                  title="Copy complete transcript text"
                >
                  {copiedText ? (
                    <>
                      <Check className="h-3.5 w-3.5 text-[#3ad389]" />
                      <span>Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3.5 w-3.5" />
                      <span>Copy Text</span>
                    </>
                  )}
                </button>

                <button
                  onClick={handleCopyAiPrompt}
                  className="px-2.5 py-1 rounded-[6px] bg-[#9281f7]/15 border border-[#9281f7]/40 hover:bg-[#9281f7]/25 text-xs font-mono text-[#9281f7] transition-all flex items-center gap-1.5"
                  title="Copy transcript formatted as prompt for AI synthesis"
                >
                  {copiedPrompt ? (
                    <>
                      <Check className="h-3.5 w-3.5 text-[#3ad389]" />
                      <span>Prompt Copied!</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-3.5 w-3.5" />
                      <span>Ask AI</span>
                    </>
                  )}
                </button>

                <button
                  onClick={handleDownloadMarkdown}
                  className="px-2.5 py-1 rounded-[6px] bg-[#181a20] border border-[#292d30] hover:border-[#ffffff] text-xs font-mono text-[#a1a4a5] hover:text-[#ffffff] transition-all flex items-center gap-1.5"
                  title="Download transcript as Markdown"
                >
                  <Download className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Export .md</span>
                </button>

                <a
                  href={data.video_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-2.5 py-1 rounded-[6px] bg-[#ff6465]/15 border border-[#ff6465]/40 hover:bg-[#ff6465]/25 text-xs font-mono text-[#ff6465] transition-all flex items-center gap-1"
                >
                  <span>Watch</span>
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </div>

            {/* Transcript Viewer Body */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 bg-[#0a0b0d]">
              {activeTab === "cues" ? (
                filteredSnippets.length === 0 ? (
                  <div className="text-center py-12 text-xs font-mono text-[#6e727a]">
                    No subtitle cues match your search "{searchQuery}"
                  </div>
                ) : (
                  <div className="space-y-2">
                    {filteredSnippets.map((cue, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-[8px] bg-[#121418] border border-[#20232a] hover:border-[#3e424d] transition-colors flex items-start gap-3 group"
                      >
                        <a
                          href={cue.permalink}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-2 py-0.5 rounded-[4px] bg-[#1f2229] border border-[#292d30] text-[11px] font-mono text-[#9281f7] hover:text-[#ffffff] hover:border-[#9281f7] transition-all shrink-0 mt-0.5 flex items-center gap-1 group-hover:bg-[#9281f7]/15"
                          title="Open video at this timestamp"
                        >
                          <span>{cue.timestamp}</span>
                          <ExternalLink className="h-2.5 w-2.5 opacity-60" />
                        </a>
                        <p className="text-xs sm:text-sm font-sans text-[#f0f0f0] leading-relaxed flex-1 select-text">
                          {cue.text}
                        </p>
                      </div>
                    ))}
                  </div>
                )
              ) : (
                <div className="p-4 rounded-[12px] bg-[#121418] border border-[#20232a] text-sm font-sans text-[#f0f0f0] leading-relaxed whitespace-pre-line select-text">
                  {data.text}
                </div>
              )}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
