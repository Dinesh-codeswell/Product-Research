"use client";

import React, { useState } from "react";
import { Loader2, Twitter, ExternalLink, Heart, Repeat2, MessageCircle, Eye, Quote, BarChart2 } from "lucide-react";
import { fetchTweetEmbeds } from "@/lib/lab-api";
import type { TweetEmbeds } from "@/lib/lab-types";

const CARD = "bg-[#0c0d10] border border-[#292d30] rounded-[10px]";
const INPUT = "w-full bg-[#000000] border border-[#292d30] rounded-[6px] px-3 py-2 text-sm text-[#ffffff] placeholder-[#5c6063] focus:outline-none focus:border-[#9281f7]/60";
const BTN_PRIMARY = "inline-flex items-center gap-1.5 text-xs font-medium px-3.5 py-2 rounded-[6px] bg-[#9281f7] text-black hover:bg-[#a99bf8] transition-colors disabled:opacity-50";

/**
 * TweetAnalyzer — FxEmbed-powered tweet intelligence.
 * Paste any x.com / twitter.com status URL and get the FxTwitter-normalised
 * payload: photo gallery, video/GIF chips, live poll results with bars,
 * quoted tweet, translations and true engagement metrics.
 */

function Metric({ icon: Icon, value, label }: { icon: any; value?: number; label: string }) {
  return (
    <div className="flex items-center gap-1.5 text-[11px] font-mono text-[#9ba1a6]">
      <Icon className="h-3.5 w-3.5 text-[#70b8ff]" />
      <span className="text-[#f0f0f0]">{typeof value === "number" ? value.toLocaleString() : "—"}</span>
      <span className="hidden sm:inline">{label}</span>
    </div>
  );
}

export function TweetAnalyzer() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [embeds, setEmbeds] = useState<TweetEmbeds | null>(null);
  const [error, setError] = useState<string | null>(null);

  const analyze = async () => {
    const clean = url.trim();
    if (!/(twitter\.com|x\.com)\/.+\/status\/\d+/i.test(clean)) {
      setError("Enter a valid tweet URL, e.g. https://x.com/user/status/1234567890");
      return;
    }
    setLoading(true); setError(null); setEmbeds(null);
    try {
      const data = await fetchTweetEmbeds(clean);
      if (!data) {
        setError("Could not fetch embed data (tweet may be deleted, protected, or the fx API is unreachable).");
      } else {
        setEmbeds(data);
      }
    } catch (e: any) {
      setError(e.message?.replace(/"/g, "") || "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className={`${CARD} p-4 space-y-3`}>
        <div className="flex items-center gap-2">
          <Twitter className="h-4 w-4 text-[#70b8ff]" />
          <h3 className="text-sm font-medium text-[#ffffff]">Tweet Analyzer</h3>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded border border-[#292d30] text-[#9ba1a6]">FxEmbed engine</span>
        </div>
        <p className="text-xs text-[#9ba1a6]">
          Extract media galleries, poll results, quoted tweets and true engagement from any X/Twitter post —
          the same normalised payload FxTwitter/FixupX serve to Discord & Telegram.
        </p>
        <div className="flex flex-col sm:flex-row gap-2">
          <input
            className={INPUT}
            placeholder="https://x.com/user/status/1234567890"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && analyze()}
          />
          <button className={BTN_PRIMARY + " shrink-0"} onClick={analyze} disabled={loading}>
            {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Twitter className="h-3.5 w-3.5" />}
            Analyze
          </button>
        </div>
        {error && <p className="text-xs text-[#ff6465]">{error}</p>}
      </div>

      {embeds && (
        <div className={`${CARD} p-5 space-y-4`}>
          {/* Author + metrics */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-[#ffffff]">@{embeds.screen_name}</span>
              {embeds.created_at && (
                <span className="text-[10px] font-mono text-[#6e727a]">
                  {new Date(embeds.created_at).toLocaleDateString()}
                </span>
              )}
            </div>
            <a
              href={`https://x.com/${embeds.screen_name}/status/${embeds.status_id}`}
              target="_blank" rel="noreferrer"
              className="text-[11px] font-mono text-[#70b8ff] hover:underline inline-flex items-center gap-1"
            >
              open on X <ExternalLink className="h-3 w-3" />
            </a>
          </div>

          <div className="flex flex-wrap gap-4">
            <Metric icon={Heart} value={embeds.likes} label="likes" />
            <Metric icon={Repeat2} value={embeds.retweets} label="reposts" />
            <Metric icon={MessageCircle} value={embeds.replies} label="replies" />
            {embeds.views != null && <Metric icon={Eye} value={embeds.views} label="views" />}
          </div>

          {/* Media gallery */}
          {embeds.media?.length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {embeds.media.slice(0, 6).map((m, i) =>
                m.type === "photo" && (m.thumbnail || m.url) ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img key={i} src={m.thumbnail || m.url || ""} alt={m.alt || "tweet media"}
                    className="w-full h-28 object-cover rounded-[8px] border border-[#292d30]" />
                ) : (
                  <a key={i} href={m.url || "#"} target="_blank" rel="noreferrer"
                    className="h-28 rounded-[8px] border border-[#292d30] bg-[#000000] flex items-center justify-center gap-2 text-xs font-mono text-[#70b8ff] hover:border-[#70b8ff]/50">
                    {m.type === "video" ? "▶ video" : "GIF"} {m.duration_ms ? `${Math.round(m.duration_ms / 1000)}s` : ""}
                  </a>
                )
              )}
            </div>
          )}

          {/* Poll */}
          {embeds.poll && (
            <div className="space-y-2">
              <p className="text-[11px] font-mono text-[#a1a4a5] flex items-center gap-1.5">
                <BarChart2 className="h-3.5 w-3.5 text-[#9281f7]" />
                Poll · {embeds.poll.total_votes.toLocaleString()} votes
              </p>
              {embeds.poll.options.map((o, i) => (
                <div key={i} className="flex items-center gap-2">
                  <span className="text-xs text-[#f0f0f0] w-36 sm:w-48 truncate">{o.label}</span>
                  <div className="flex-1 h-2 rounded bg-[#292d30]/60 overflow-hidden">
                    <div className="h-full bg-[#9281f7]" style={{ width: `${o.percent}%` }} />
                  </div>
                  <span className="text-[11px] font-mono text-[#9ba1a6] w-10 text-right">{o.percent}%</span>
                </div>
              ))}
            </div>
          )}

          {/* Quote */}
          {embeds.quote && (
            <div className="border-l-2 border-[#9281f7] pl-3 py-1.5 space-y-1">
              <p className="text-[11px] font-mono text-[#9281f7] flex items-center gap-1.5">
                <Quote className="h-3 w-3" /> @{embeds.quote.author}
                {embeds.quote.likes != null && <span className="text-[#6e727a]">· {embeds.quote.likes.toLocaleString()} likes</span>}
              </p>
              <p className="text-xs text-[#d8dadc]">{embeds.quote.text}</p>
            </div>
          )}

          {/* Translation */}
          {embeds.translated_text && (
            <div className="text-xs text-[#a1a4a5] border-t border-[#292d30]/60 pt-3">
              <span className="text-[10px] font-mono text-[#6e727a] uppercase tracking-wider block mb-1">Translation</span>
              {embeds.translated_text}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
