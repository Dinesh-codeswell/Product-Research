"use client";

import React, { useState, useMemo, useEffect } from "react";
import {
  X,
  Youtube,
  Copy,
  Check,
  Download,
  Search,
  Sparkles,
  Clock,
  FileText,
  Radio,
  RefreshCw,
  AlertCircle,
  Play,
  Tv,
  Mic,
  Key,
  ExternalLink
} from "lucide-react";
import { YouTubeTranscriptData, YouTubeTranscriptSnippet } from "@/lib/types";
import { fetchYouTubeTranscript, transcribeYouTubeAudio, getYouTubeWhisperStatus } from "@/lib/api";

interface YouTubeTranscriptModalProps {
  videoUrlOrId: string | null;
  videoTitle?: string;
  initialTranscriptData?: YouTubeTranscriptData | null;
  initialSeekSeconds?: number;
  initialMode?: "player" | "transcript";
  onClose: () => void;
}

export function YouTubeTranscriptModal({
  videoUrlOrId,
  videoTitle,
  initialTranscriptData,
  initialSeekSeconds = 0,
  initialMode = "player",
  onClose,
}: YouTubeTranscriptModalProps) {
  const [data, setData] = useState<YouTubeTranscriptData | null>(initialTranscriptData || null);
  const [isLoading, setIsLoading] = useState<boolean>(!initialTranscriptData && !!videoUrlOrId);
  const [isTranscribing, setIsTranscribing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [copiedText, setCopiedText] = useState(false);
  const [copiedPrompt, setCopiedPrompt] = useState(false);
  const [copiedSrt, setCopiedSrt] = useState(false);
  const [activeTab, setActiveTab] = useState<"cues" | "full_text">("cues");

  // In-Website Video Player State
  const [showPlayer, setShowPlayer] = useState<boolean>(initialMode !== "transcript");
  const [currentSeekTime, setCurrentSeekTime] = useState<number>(initialSeekSeconds);
  const [playerKey, setPlayerKey] = useState<number>(0);
  const [whisperKeyInput, setWhisperKeyInput] = useState<string>("");
  const [showKeyPrompt, setShowKeyPrompt] = useState<boolean>(false);
  const [whisperStatus, setWhisperStatus] = useState<{ groq_configured: boolean; openai_configured: boolean; whisper_ready: boolean } | null>(null);
  const [isClient, setIsClient] = useState(false);

  // Load saved Groq key from localStorage if present (client-side only)
  useEffect(() => {
    setIsClient(true);
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("pulseradar_groq_key");
      if (saved) setWhisperKeyInput(saved);
    }
  }, []);

  // Check backend Whisper status
  useEffect(() => {
    getYouTubeWhisperStatus().then(setWhisperStatus).catch(() => {});
  }, []);

  // Sync externally requested seek positions (e.g. clicking a timestamped evidence signal)
  // into the embedded player so the video resumes exactly at the cited second.
  useEffect(() => {
    if (!videoUrlOrId) return;
    const requested = Number.isFinite(initialSeekSeconds) ? Math.max(0, Math.floor(initialSeekSeconds)) : 0;
    setCurrentSeekTime(requested);
    setPlayerKey((k) => k + 1);
  }, [videoUrlOrId, initialSeekSeconds]);

  // Extract clean video ID
  const videoId = useMemo(() => {
    if (!videoUrlOrId) return "";
    const clean = videoUrlOrId.trim();
    if (clean.length === 11 && !clean.includes("/") && !clean.includes("?")) return clean;
    const match = clean.match(/(?:watch\?.*?v=|embed\/|v\/|shorts\/|youtu\.be\/)([a-zA-Z0-9_-]{11})/i);
    return match ? match[1] : (data?.video_id || "");
  }, [videoUrlOrId, data?.video_id]);

  // Is Bilibili or other source
  const isBilibili = useMemo(() => {
    return videoUrlOrId?.includes("bilibili.com") || false;
  }, [videoUrlOrId]);

  const bilibiliBvid = useMemo(() => {
    if (!isBilibili || !videoUrlOrId) return "";
    const m = videoUrlOrId.match(/video\/(BV[a-zA-Z0-9]+)/);
    return m ? m[1] : "";
  }, [isBilibili, videoUrlOrId]);

  // Video embed URL (MUST be computed unconditionally with all hooks)
  const embedUrl = useMemo(() => {
    if (isBilibili && bilibiliBvid) {
      return `https://player.bilibili.com/player.html?bvid=${bilibiliBvid}&page=1&autoplay=1`;
    }
    if (videoId) {
      const seekParam = currentSeekTime > 0 ? `&start=${currentSeekTime}` : "";
      return `https://www.youtube.com/embed/${videoId}?autoplay=1&enablejsapi=1&rel=0${seekParam}`;
    }
    return "";
  }, [isBilibili, bilibiliBvid, videoId, currentSeekTime]);

  // Initial Fetch
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

  // Handle Seeks in the In-Website Player (Zero External Tabs!)
  const handleSeek = (seconds: number) => {
    const s = Math.floor(seconds);
    setCurrentSeekTime(s);
    setPlayerKey((k) => k + 1);
  };

  // Trigger Whisper Transcription on Demand
  const handleRunWhisper = async () => {
    if (!videoUrlOrId) return;
    setIsTranscribing(true);
    setError(null);
    try {
      if (whisperKeyInput && typeof window !== "undefined") {
        localStorage.setItem("pulseradar_groq_key", whisperKeyInput.trim());
      }
      const res = await transcribeYouTubeAudio(videoUrlOrId, whisperKeyInput.trim() || undefined);
      if (res && res.success) {
        setData(res);
        setShowKeyPrompt(false);
      } else {
        setError(res.error || "Whisper audio transcription could not be completed.");
      }
    } catch (err: any) {
      setError(err.message || "Failed to transcribe audio.");
    } finally {
      setIsTranscribing(false);
    }
  };

  const handleCopyFullTranscript = () => {
    if (!data?.text) return;
    navigator.clipboard.writeText(data.text);
    setCopiedText(true);
    setTimeout(() => setCopiedText(false), 2000);
  };

  const handleCopyAiPrompt = () => {
    if (!data?.text) return;
    const prompt = `Please analyze the following YouTube video transcript regarding "${videoTitle || data.video_title || data.video_id}".
Extract the core user pain points, workarounds, product feature requests, and competitor comparisons:

--- TRANSCRIPT (Video: ${data.video_url || `https://www.youtube.com/watch?v=${data.video_id}`}) ---
${data.text}
`;
    navigator.clipboard.writeText(prompt);
    setCopiedPrompt(true);
    setTimeout(() => setCopiedPrompt(false), 2000);
  };

  const handleDownloadMarkdown = () => {
    if (!data) return;
    const title = videoTitle || data.video_title || `YouTube_Video_${data.video_id}`;
    let md = `# Video Transcript: ${title}\n\n`;
    md += `- **Video URL:** ${data.video_url || ""}\n`;
    md += `- **Channel:** ${data.channel || "YouTube"}\n`;
    md += `- **Duration:** ${data.stats?.formatted_duration || "00:00"} (${data.stats?.duration_seconds || 0}s)\n`;
    md += `- **Word Count:** ${data.stats?.word_count || 0} words\n`;
    md += `- **Language:** ${data.language || "en"} (${data.is_transcribed ? "Whisper ASR" : data.is_generated ? "Auto-generated" : "Subtitles"})\n\n`;
    md += `## Timestamped Transcript Cues\n\n`;

    for (const cue of (data.snippets || [])) {
      md += `**[${cue.timestamp}]** ${cue.text}\n\n`;
    }

    const blob = new Blob([md], { type: "text/markdown;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${title.replace(/[^a-z0-9_-]/gi, "_")}_transcript.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadSrt = () => {
    if (!data || !data.snippets?.length) return;
    const title = videoTitle || data.video_title || `YouTube_Video_${data.video_id}`;
    const srt = buildSrtText();

    const blob = new Blob([srt], { type: "text/plain;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${title.replace(/[^a-z0-9_-]/gi, "_")}.srt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Build standards-compliant SRT payload (shared by download + clipboard copy)
  function buildSrtText(): string {
    if (!data || !data.snippets?.length) return "";

    const formatTime = (ms: number) => {
      const h = Math.floor(ms / 3600000);
      const m = Math.floor((ms % 3600000) / 60000);
      const s = Math.floor((ms % 60000) / 1000);
      const milli = ms % 1000;
      return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")},${String(milli).padStart(3, "0")}`;
    };

    let srt = "";
    (data.snippets || []).forEach((cue, index) => {
      const startMs = Math.floor(cue.start * 1000);
      const endMs = Math.floor((cue.start + (cue.duration || 5)) * 1000);
      srt += `${index + 1}\n`;
      srt += `${formatTime(startMs)} --> ${formatTime(endMs)}\n`;
      srt += `${cue.text}\n\n`;
    });
    return srt;
  }

  const handleCopySrt = () => {
    const srt = buildSrtText();
    if (!srt) return;
    navigator.clipboard.writeText(srt);
    setCopiedSrt(true);
    setTimeout(() => setCopiedSrt(false), 2000);
  };

  // Safe client-side and existence guards AFTER all hooks have executed
  if (!videoUrlOrId || !isClient) return null;

  return (
    <div className="fixed inset-0 z-50 bg-[#000000]/85 backdrop-blur-md flex items-center justify-center p-2 sm:p-4 md:p-6 animate-in fade-in duration-200">
      <div className="w-full max-w-6xl h-[92vh] bg-[#0c0d10] border border-[#292d30] rounded-[16px] flex flex-col shadow-2xl overflow-hidden">
        
        {/* Modal Header */}
        <div className="p-4 border-b border-[#292d30] bg-[#121418] flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="h-9 w-9 rounded-[8px] bg-[#ff6465]/15 border border-[#ff6465]/30 flex items-center justify-center text-[#ff6465] shrink-0">
              <Youtube className="h-5 w-5" />
            </div>
            <div className="overflow-hidden">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono text-[#ff6465] font-bold tracking-wider uppercase bg-[#ff6465]/10 px-2 py-0.5 rounded-[4px] border border-[#ff6465]/20 flex items-center gap-1">
                  <Tv className="h-3 w-3" />
                  <span>In-Website Video Player & Dialogue</span>
                </span>
                {data && (
                  <span className="text-[11px] font-mono text-[#3ad389] flex items-center gap-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-[#3ad389]" />
                    <span>
                      {data.is_transcribed
                        ? "Whisper ASR Transcribed"
                        : data.is_chapters_only
                        ? "Video Chapters"
                        : data.is_generated
                        ? "Auto-Subtitles"
                        : "Subtitles"}
                    </span>
                  </span>
                )}
              </div>
              <h3 className="text-sm sm:text-base font-sans font-medium text-[#ffffff] truncate mt-0.5">
                {videoTitle || data?.video_title || (videoId ? `Video ${videoId}` : "Extracting Video Transcript...")}
              </h3>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowPlayer(!showPlayer)}
              className={`p-1.5 px-2.5 rounded-[6px] border text-xs font-mono transition-all flex items-center gap-1.5 ${
                showPlayer
                  ? "bg-[#9281f7]/15 border-[#9281f7]/40 text-[#9281f7]"
                  : "bg-[#181a20] border-[#292d30] text-[#a1a4a5] hover:text-[#ffffff]"
              }`}
              title={showPlayer ? "Collapse video player" : "Show embedded video player"}
            >
              <Tv className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">{showPlayer ? "Hide Player" : "Show Player"}</span>
            </button>

            <button
              onClick={onClose}
              className="p-1.5 rounded-[6px] text-[#a1a4a5] hover:text-[#ffffff] hover:bg-[#1f2229] transition-colors shrink-0"
              title="Close modal"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Content Body: Split View with In-Website Player and Interactive Transcript */}
        {isLoading ? (
          <div className="flex-1 flex flex-col items-center justify-center p-12 text-center space-y-3">
            <RefreshCw className="h-8 w-8 text-[#9281f7] animate-spin" />
            <h4 className="text-sm font-sans font-medium text-[#ffffff]">
              Extracting video dialogue, metadata & cues...
            </h4>
            <p className="text-xs font-mono text-[#a1a4a5] max-w-sm">
              Connecting multi-tier extractor to pull subtitles, video chapters, and dialogue directly for in-website playback.
            </p>
          </div>
        ) : (
          <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
            
            {/* LEFT / TOP: In-Website Video Player */}
            {showPlayer && embedUrl && (
              <div className="w-full md:w-[46%] lg:w-[48%] bg-[#08090a] border-b md:border-b-0 md:border-r border-[#292d30] flex flex-col shrink-0">
                <div className="relative aspect-video w-full bg-[#000000]">
                  <iframe
                    key={playerKey}
                    src={embedUrl}
                    title={videoTitle || data?.video_title || "Video Player"}
                    className="w-full h-full border-0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                    allowFullScreen
                  />
                </div>

                {/* Player Toolbar & Active Seek Details */}
                <div className="p-3 bg-[#121418] border-t border-[#292d30] flex items-center justify-between gap-3 text-xs font-mono">
                  <div className="flex items-center gap-2 overflow-hidden">
                    <span className="text-[#a1a4a5] flex items-center gap-1 shrink-0">
                      <Clock className="h-3.5 w-3.5 text-[#ff6465]" />
                      <span>{Math.floor(currentSeekTime / 60)}:{(currentSeekTime % 60).toString().padStart(2, "0")}</span>
                    </span>
                    <span className="text-[#464a4d]">•</span>
                    <span className="text-[#f0f0f0] truncate">
                      {data?.channel || "Playing In-Site"}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      onClick={() => handleSeek(0)}
                      className="px-2 py-0.5 rounded-[4px] bg-[#181a20] border border-[#292d30] hover:border-[#ffffff] text-[11px] text-[#a1a4a5] hover:text-[#ffffff] transition-all"
                      title="Replay from start"
                    >
                      Restart
                    </button>
                    <span className="text-[10px] text-[#3ad389] bg-[#3ad389]/10 px-1.5 py-0.5 rounded-[4px] border border-[#3ad389]/20 font-bold">
                      LIVE IN-SITE
                    </span>
                  </div>
                </div>

                {/* Video Info Card & Description Preview */}
                {data?.video_title && (
                  <div className="p-3 overflow-y-auto max-h-[140px] text-xs font-sans text-[#a1a4a5] border-t border-[#20232a] bg-[#0c0d10] leading-relaxed select-text hidden md:block">
                    <div className="font-medium text-[#ffffff] mb-1">
                      {data.video_title}
                    </div>
                    {data.description ? (
                      <p className="line-clamp-4 text-[11px] text-[#80848d] whitespace-pre-line">
                        {data.description}
                      </p>
                    ) : null}
                  </div>
                )}
              </div>
            )}

            {/* RIGHT: Transcript Dialogue, Cues, & Whisper Fallback */}
            <div className="flex-1 flex flex-col overflow-hidden bg-[#0c0d10]">
              
              {/* Header Ribbon & Stats */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 p-3 border-b border-[#292d30] bg-[#121418] text-xs font-mono">
                <div className="p-2 rounded-[6px] bg-[#181a20] border border-[#292d30]">
                  <div className="text-[10px] text-[#6e727a] uppercase">Duration</div>
                  <div className="text-xs font-medium text-[#ffffff] mt-0.5 flex items-center gap-1">
                    <Clock className="h-3 w-3 text-[#9281f7]" />
                    <span>{data?.stats?.formatted_duration || "00:00"}</span>
                  </div>
                </div>

                <div className="p-2 rounded-[6px] bg-[#181a20] border border-[#292d30]">
                  <div className="text-[10px] text-[#6e727a] uppercase">Cues / Moments</div>
                  <div className="text-xs font-medium text-[#ffffff] mt-0.5 flex items-center gap-1">
                    <Radio className="h-3 w-3 text-[#3ad389]" />
                    <span>{data?.stats?.snippets_count || 0} items</span>
                  </div>
                </div>

                <div className="p-2 rounded-[6px] bg-[#181a20] border border-[#292d30]">
                  <div className="text-[10px] text-[#6e727a] uppercase">Word Count</div>
                  <div className="text-xs font-medium text-[#ffffff] mt-0.5 flex items-center gap-1">
                    <FileText className="h-3 w-3 text-[#ffca16]" />
                    <span>{(data?.stats?.word_count || 0).toLocaleString()} words</span>
                  </div>
                </div>

                <div className="p-2 rounded-[6px] bg-[#181a20] border border-[#292d30]">
                  <div className="text-[10px] text-[#6e727a] uppercase">Source</div>
                  <div className="text-xs font-medium text-[#ffffff] mt-0.5 truncate uppercase">
                    {data?.source || "YouTube"}
                  </div>
                </div>
              </div>

              {/* Action Toolbar & Search */}
              <div className="p-3 border-b border-[#292d30] bg-[#121418] flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2 flex-1 min-w-[200px]">
                  <div className="flex items-center bg-[#181a20] p-0.5 rounded-[6px] border border-[#292d30]">
                    <button
                      onClick={() => setActiveTab("cues")}
                      className={`px-2.5 py-1 rounded-[4px] text-xs font-mono transition-all ${
                        activeTab === "cues"
                          ? "bg-[#9281f7]/20 text-[#ffffff] border border-[#9281f7]/40"
                          : "text-[#a1a4a5] hover:text-[#ffffff]"
                      }`}
                    >
                      Dialogue Cues
                    </button>
                    <button
                      onClick={() => setActiveTab("full_text")}
                      className={`px-2.5 py-1 rounded-[4px] text-xs font-mono transition-all ${
                        activeTab === "full_text"
                          ? "bg-[#9281f7]/20 text-[#ffffff] border border-[#9281f7]/40"
                          : "text-[#a1a4a5] hover:text-[#ffffff]"
                      }`}
                    >
                      Full Text
                    </button>
                  </div>

                  {activeTab === "cues" && data?.snippets && data.snippets.length > 0 && (
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

                {/* Toolbar Buttons */}
                <div className="flex items-center gap-1.5">
                  {data?.text && (
                    <>
                      <button
                        onClick={handleCopyFullTranscript}
                        className="px-2 py-1 rounded-[6px] bg-[#181a20] border border-[#292d30] hover:border-[#ffffff] text-xs font-mono text-[#a1a4a5] hover:text-[#ffffff] transition-all flex items-center gap-1"
                        title="Copy complete transcript text"
                      >
                        {copiedText ? (
                          <>
                            <Check className="h-3 w-3 text-[#3ad389]" />
                            <span>Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="h-3 w-3" />
                            <span>Copy</span>
                          </>
                        )}
                      </button>

                      <button
                        onClick={handleCopyAiPrompt}
                        className="px-2 py-1 rounded-[6px] bg-[#9281f7]/15 border border-[#9281f7]/40 hover:bg-[#9281f7]/25 text-xs font-mono text-[#9281f7] transition-all flex items-center gap-1"
                        title="Copy formatted as prompt for AI synthesis"
                      >
                        {copiedPrompt ? (
                          <>
                            <Check className="h-3 w-3 text-[#3ad389]" />
                            <span>Prompt Copied</span>
                          </>
                        ) : (
                          <>
                            <Sparkles className="h-3 w-3" />
                            <span>Ask AI</span>
                          </>
                        )}
                      </button>

                      <button
                        onClick={handleDownloadMarkdown}
                        className="px-2 py-1 rounded-[6px] bg-[#181a20] border border-[#292d30] hover:border-[#ffffff] text-xs font-mono text-[#a1a4a5] hover:text-[#ffffff] transition-all flex items-center gap-1"
                        title="Export transcript as Markdown"
                      >
                        <Download className="h-3 w-3" />
                        <span className="hidden sm:inline">.md</span>
                      </button>

                      <button
                        onClick={handleDownloadSrt}
                        className="px-2 py-1 rounded-[6px] bg-[#181a20] border border-[#292d30] hover:border-[#ffffff] text-xs font-mono text-[#a1a4a5] hover:text-[#ffffff] transition-all flex items-center gap-1"
                        title="Export subtitles as SRT"
                      >
                        <Download className="h-3 w-3" />
                        <span className="hidden sm:inline">.srt</span>
                      </button>

                      <button
                        onClick={handleCopySrt}
                        className="px-2 py-1 rounded-[6px] bg-[#181a20] border border-[#292d30] hover:border-[#ffffff] text-xs font-mono text-[#a1a4a5] hover:text-[#ffffff] transition-all flex items-center gap-1"
                        title="Copy SRT subtitle blocks to clipboard"
                      >
                        {copiedSrt ? (
                          <>
                            <Check className="h-3 w-3 text-[#3ad389]" />
                            <span className="hidden sm:inline">SRT Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="h-3 w-3" />
                            <span className="hidden sm:inline">SRT</span>
                          </>
                        )}
                      </button>
                    </>
                  )}
                </div>
              </div>

              {/* Main Transcript Body or Whisper Fallback Card */}
              <div className="flex-1 overflow-y-auto p-4 sm:p-5 bg-[#0a0b0d]">
                
                {/* Notice banner if YouTube captions were blocked or chapter-only */}
                {data?.notice && (
                  <div className="mb-4 p-3 rounded-[8px] bg-[#ffca16]/10 border border-[#ffca16]/30 flex items-start gap-2.5 text-xs font-mono text-[#ffca16]">
                    <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <p>{data.notice}</p>
                    </div>
                  </div>
                )}

                {/* Error Banner */}
                {error && (
                  <div className="mb-4 p-3 rounded-[8px] bg-[#ff6465]/15 border border-[#ff6465]/35 flex items-start gap-2.5 text-xs font-mono text-[#ff6465]">
                    <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <p className="font-semibold">Notice</p>
                      <p className="mt-0.5 text-[#ff9592]">{error}</p>
                    </div>
                  </div>
                )}

                {/* If no transcript dialogue is available: Render Interactive Whisper Transcription Card */}
                {(!data || !data.snippets || data.snippets.length === 0 || data.is_chapters_only) && (
                  <div className="mb-5 p-5 rounded-[12px] bg-[#121418] border border-[#292d30] text-center space-y-4">
                    <div className="h-12 w-12 rounded-full bg-[#9281f7]/15 border border-[#9281f7]/30 mx-auto flex items-center justify-center text-[#9281f7]">
                      <Mic className="h-6 w-6" />
                    </div>

                    <div className="max-w-md mx-auto space-y-1.5">
                      <h4 className="text-sm font-sans font-medium text-[#ffffff]">
                        {data?.is_chapters_only
                          ? "Want word-for-word spoken dialogue?"
                          : "Transcribe Spoken Dialogue with Whisper ASR"}
                      </h4>
                      <p className="text-xs font-mono text-[#a1a4a5] leading-relaxed">
                        YouTube closed captions are restricted or unavailable for this video. You can extract the dialogue in seconds using Whisper Large v3.
                      </p>

                      {/* Backend Whisper readiness indicator */}
                      {whisperStatus && (
                        <div
                          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[4px] text-[10px] font-mono border ${
                            whisperStatus.whisper_ready
                              ? "bg-[#3ad389]/10 border-[#3ad389]/30 text-[#3ad389]"
                              : "bg-[#ffca16]/10 border-[#ffca16]/30 text-[#ffca16]"
                          }`}
                          title={
                            whisperStatus.whisper_ready
                              ? "A Whisper API key is configured on the backend"
                              : "No backend key found — paste a free Groq key below to transcribe"
                          }
                        >
                          <span className="h-1.5 w-1.5 rounded-full bg-current" />
                          <span>
                            {whisperStatus.groq_configured
                              ? "Backend Whisper ready (Groq whisper-large-v3)"
                              : whisperStatus.openai_configured
                              ? "Backend Whisper ready (OpenAI)"
                              : "No backend key — paste a free Groq key below"}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Whisper Key Input (if user wants to provide or override) */}
                    {showKeyPrompt && (
                      <div className="max-w-md mx-auto p-3 rounded-[8px] bg-[#181a20] border border-[#292d30] text-left space-y-2">
                        <label className="text-[11px] font-mono text-[#a1a4a5] flex items-center justify-between">
                          <span className="flex items-center gap-1">
                            <Key className="h-3 w-3 text-[#ffca16]" />
                            <span>Groq API Key (Free) or OpenAI Key:</span>
                          </span>
                          <a
                            href="https://console.groq.com/keys"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[10px] text-[#9281f7] hover:underline flex items-center gap-0.5"
                          >
                            <span>Get Free Groq Key</span>
                            <ExternalLink className="h-2.5 w-2.5" />
                          </a>
                        </label>
                        <input
                          type="password"
                          value={whisperKeyInput}
                          onChange={(e) => setWhisperKeyInput(e.target.value)}
                          placeholder="gsk_... or sk-..."
                          className="w-full px-3 py-1.5 bg-[#0c0d10] border border-[#292d30] rounded-[6px] text-xs font-mono text-[#ffffff] placeholder-[#6e727a] outline-none focus:border-[#9281f7]"
                        />
                      </div>
                    )}

                    {/* Action Button */}
                    <div className="flex flex-wrap items-center justify-center gap-3 pt-1">
                      <button
                        onClick={handleRunWhisper}
                        disabled={isTranscribing}
                        className="px-4 py-2 rounded-[8px] bg-[#9281f7] hover:bg-[#8270eb] disabled:bg-[#464a4d] text-[#ffffff] text-xs font-mono font-medium transition-all shadow-lg flex items-center gap-2"
                      >
                        {isTranscribing ? (
                          <>
                            <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                            <span>Transcribing Audio with Whisper...</span>
                          </>
                        ) : (
                          <>
                            <Mic className="h-3.5 w-3.5" />
                            <span>Transcribe with Whisper ASR</span>
                          </>
                        )}
                      </button>

                      {!showKeyPrompt && (
                        <button
                          onClick={() => setShowKeyPrompt(true)}
                          className="px-3 py-2 rounded-[8px] bg-[#181a20] border border-[#292d30] hover:border-[#ffffff] text-xs font-mono text-[#a1a4a5] hover:text-[#ffffff] transition-all"
                        >
                          Configure Key
                        </button>
                      )}
                    </div>
                  </div>
                )}

                {/* Render Cues */}
                {activeTab === "cues" ? (
                  filteredSnippets.length === 0 ? (
                    <div className="text-center py-12 text-xs font-mono text-[#6e727a]">
                      {data?.snippets && data.snippets.length > 0
                        ? `No dialogue cues match your search "${searchQuery}"`
                        : "Play the video above or click Transcribe with Whisper to generate spoken dialogue."}
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {filteredSnippets.map((cue, idx) => {
                        const isCurrentActive =
                          currentSeekTime >= cue.start &&
                          currentSeekTime < cue.start + (cue.duration || 5);

                        return (
                          <div
                            key={idx}
                            onClick={() => handleSeek(cue.start)}
                            className={`p-3 rounded-[8px] border transition-all flex items-start gap-3 cursor-pointer group ${
                              isCurrentActive
                                ? "bg-[#9281f7]/15 border-[#9281f7]/50 shadow-md"
                                : "bg-[#121418] border-[#20232a] hover:border-[#3e424d]"
                            }`}
                          >
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleSeek(cue.start);
                              }}
                              className={`px-2 py-0.5 rounded-[4px] border text-[11px] font-mono transition-all shrink-0 mt-0.5 flex items-center gap-1 ${
                                isCurrentActive
                                  ? "bg-[#9281f7] text-[#ffffff] border-[#9281f7]"
                                  : "bg-[#1f2229] border-[#292d30] text-[#9281f7] group-hover:bg-[#9281f7]/20 group-hover:border-[#9281f7]"
                              }`}
                              title="Play video in-site from this timestamp"
                            >
                              <Play className="h-2.5 w-2.5 fill-current" />
                              <span>{cue.timestamp}</span>
                            </button>

                            <p className="text-xs sm:text-sm font-sans text-[#f0f0f0] leading-relaxed flex-1 select-text">
                              {cue.text}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  )
                ) : (
                  <div className="p-4 rounded-[12px] bg-[#121418] border border-[#20232a] text-sm font-sans text-[#f0f0f0] leading-relaxed whitespace-pre-line select-text">
                    {data?.text || "No text available."}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
