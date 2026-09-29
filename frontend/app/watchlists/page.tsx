"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  Bell,
  Zap,
  Plus,
  Trash2,
  Play,
  RefreshCw,
  ChevronRight,
  Activity,
  Globe,
  TrendingUp,
  TrendingDown,
  ArrowRight,
  Loader2,
  Webhook
} from "lucide-react";
import {
  listWatchlists,
  createWatchlist,
  deleteWatchlist,
  runWatchlist,
  listAutomations,
  createAutomation,
  deleteAutomation,
  toggleAutomation,
} from "@/lib/api";
import type { Watchlist, WatchlistDetail, AutomationRule } from "@/lib/api";

export default function WatchlistPage() {
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [automations, setAutomations] = useState<AutomationRule[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create watchlist form
  const [newTopic, setNewTopic] = useState("");
  const [creating, setCreating] = useState(false);

  // Create automation form
  const [showAutoForm, setShowAutoForm] = useState(false);
  const [autoName, setAutoName] = useState("");
  const [autoEvent, setAutoEvent] = useState<"research.completed" | "seo.completed">("research.completed");
  const [autoWebhookUrl, setAutoWebhookUrl] = useState("");
  const [autoCondition, setAutoCondition] = useState("");
  const [autoConditionValue, setAutoConditionValue] = useState("");
  const [creatingAuto, setCreatingAuto] = useState(false);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    const [w, a] = await Promise.all([listWatchlists(), listAutomations()]);
    setWatchlists(w);
    setAutomations(a);
    setIsLoading(false);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleCreateWatchlist = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTopic.trim()) return;
    setCreating(true);
    setError(null);
    try {
      await createWatchlist({ topic: newTopic.trim(), interval_hours: 24 });
      setNewTopic("");
      await refresh();
    } catch (err: any) {
      setError(err.message || "Failed to create watchlist");
    } finally {
      setCreating(false);
    }
  };

  const handleRun = async (id: string) => {
    setError(null);
    try {
      const res = await runWatchlist(id);
      window.location.href = `/research/${res.session_id}`;
    } catch (err: any) {
      setError(err.message || "Failed to run watchlist");
    }
  };

  const handleCreateAutomation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!autoName.trim() || !autoWebhookUrl.trim()) return;
    setCreatingAuto(true);
    setError(null);
    try {
      const conditions: Record<string, any> = {};
      if (autoCondition && autoConditionValue) {
        const num = parseFloat(autoConditionValue);
        conditions[autoCondition] = isNaN(num) ? autoConditionValue : num;
      }
      await createAutomation({
        name: autoName.trim(),
        event_type: autoEvent,
        conditions,
        action_config: { url: autoWebhookUrl.trim() },
      });
      setAutoName("");
      setAutoWebhookUrl("");
      setAutoCondition("");
      setAutoConditionValue("");
      setShowAutoForm(false);
      await refresh();
    } catch (err: any) {
      setError(err.message || "Failed to create automation");
    } finally {
      setCreatingAuto(false);
    }
  };

  return (
    <div className="space-y-12 animate-in fade-in duration-200">
      {/* Hero */}
      <div className="space-y-4 pt-4">
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full border border-[#292d30] text-xs font-mono text-[#a1a4a5]">
          <span className="h-1.5 w-1.5 rounded-full bg-[#9281f7]" />
          <span className="text-[#9281f7]">Trend Monitoring &amp; Automations</span>
        </div>
        <h1 className="font-serif text-4xl sm:text-5xl text-[#ffffff] tracking-tight">
          Watchlists &amp; <span className="italic text-[#f0f0f0]">always-on sweeps.</span>
        </h1>
        <p className="text-sm sm:text-base text-[#a1a4a5] max-w-2xl">
          Track topics over time and see what changed since the last sweep &mdash; new pain
          themes, worsening severity, resolved friction. Wire webhooks to fire the moment
          research or an SEO audit completes.
        </p>
      </div>

      {error && (
        <div className="p-3 rounded-[6px] bg-[#ff9592]/10 border border-[#ff9592]/30 text-[#ff9592] text-xs font-mono">
          {error}
        </div>
      )}

      {/* Watchlists */}
      <section className="space-y-6">
        <div className="flex items-end justify-between border-b border-[#292d30] pb-4">
          <div className="flex items-center gap-2">
            <Bell className="h-4 w-4 text-[#9281f7]" />
            <h2 className="text-xl font-serif text-[#ffffff]">Topic Watchlists</h2>
            <span className="text-xs font-mono text-[#6e727a]">{watchlists.length} tracked</span>
          </div>
          <button
            onClick={refresh}
            className="p-1.5 rounded-[6px] border border-[#292d30] text-[#a1a4a5] hover:text-[#ffffff] hover:border-[#6e727a] transition-all"
            title="Refresh"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>

        <form onSubmit={handleCreateWatchlist} className="flex flex-col sm:flex-row gap-2.5">
          <input
            type="text"
            placeholder="Topic to track (e.g. 'MCP servers', 'AI code review tools')..."
            value={newTopic}
            onChange={(e) => setNewTopic(e.target.value)}
            className="flex-1 px-4 py-3 bg-[#000000] border border-[#292d30] rounded-[6px] text-sm text-[#ffffff] placeholder-[#464a4d] focus:outline-none focus:border-[#ffffff] transition-colors"
          />
          <button
            type="submit"
            disabled={creating || !newTopic.trim()}
            className="px-5 py-3 bg-[#ffffff] hover:bg-[#ffffff]/90 text-[#000000] font-medium text-sm rounded-[6px] flex items-center gap-2 transition-all disabled:opacity-40"
          >
            {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
            <span>Track Topic</span>
          </button>
        </form>

        {watchlists.length === 0 && !isLoading ? (
          <div className="p-8 rounded-[16px] bg-[#000000] border border-[#292d30] text-center">
            <Activity className="h-8 w-8 text-[#464a4d] mx-auto mb-3" />
            <p className="text-sm text-[#a1a4a5]">
              No watchlists yet. Track a topic above, then run periodic sweeps &mdash;
              PulseRadar snapshots the themes and diffs them against the previous run.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {watchlists.map((w) => (
              <div
                key={w.id}
                className="p-5 rounded-[16px] bg-[#000000] border border-[#292d30] hover:border-[#6e727a] transition-all space-y-4 group"
              >
                <div className="flex items-start justify-between gap-2">
                  <h3 className="text-sm font-medium text-[#ffffff] leading-snug line-clamp-2">
                    {w.topic}
                  </h3>
                  <button
                    onClick={() => deleteWatchlist(w.id).then(refresh)}
                    className="p-1 rounded text-[#6e727a] hover:text-[#ff9592] transition-colors shrink-0"
                    title="Delete watchlist"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>

                <div className="flex flex-wrap gap-1.5">
                  {(w.channels || []).map((c) => (
                    <span key={c} className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#292d30]/50 text-[#a1a4a5] border border-[#292d30]">
                      {c}
                    </span>
                  ))}
                </div>

                <div className="flex items-center justify-between text-[11px] font-mono text-[#6e727a] pt-2 border-t border-[#292d30]">
                  <span>{w.runs} runs</span>
                  <span>{w.last_run_at ? new Date(w.last_run_at).toLocaleDateString() : "never run"}</span>
                </div>

                <button
                  onClick={() => handleRun(w.id)}
                  className="w-full py-2 rounded-[6px] bg-[#9281f7]/10 border border-[#9281f7]/40 hover:bg-[#9281f7]/20 text-[#9281f7] text-xs font-mono flex items-center justify-center gap-1.5 transition-all"
                >
                  <Play className="h-3 w-3" />
                  Run Sweep Now
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Automations */}
      <section className="space-y-6">
        <div className="flex items-end justify-between border-b border-[#292d30] pb-4">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-[#ffca16]" />
            <h2 className="text-xl font-serif text-[#ffffff]">Automation Rules</h2>
            <span className="text-xs font-mono text-[#6e727a]">{automations.length} rules</span>
          </div>
          <button
            onClick={() => setShowAutoForm(!showAutoForm)}
            className="px-3 py-1.5 rounded-[6px] border border-[#292d30] text-xs font-mono text-[#a1a4a5] hover:text-[#ffffff] hover:border-[#ffffff] transition-all flex items-center gap-1.5"
          >
            <Plus className="h-3.5 w-3.5" />
            New Rule
          </button>
        </div>

        {showAutoForm && (
          <form onSubmit={handleCreateAutomation} className="p-5 rounded-[16px] bg-[#000000] border border-[#292d30] space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-[11px] font-mono text-[#a1a4a5] uppercase">Rule name</label>
                <input
                  type="text"
                  value={autoName}
                  onChange={(e) => setAutoName(e.target.value)}
                  placeholder="Alert: severity spike"
                  className="w-full px-3 py-2.5 bg-[#000000] border border-[#292d30] rounded-[6px] text-sm text-[#ffffff] focus:outline-none focus:border-[#ffffff]"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-[11px] font-mono text-[#a1a4a5] uppercase">Event</label>
                <select
                  value={autoEvent}
                  onChange={(e) => setAutoEvent(e.target.value as any)}
                  className="w-full px-3 py-2.5 bg-[#000000] border border-[#292d30] rounded-[6px] text-sm text-[#ffffff] focus:outline-none focus:border-[#ffffff]"
                >
                  <option value="research.completed">research.completed</option>
                  <option value="seo.completed">seo.completed</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <label className="text-[11px] font-mono text-[#a1a4a5] uppercase">Webhook URL</label>
                <input
                  type="url"
                  value={autoWebhookUrl}
                  onChange={(e) => setAutoWebhookUrl(e.target.value)}
                  placeholder="https://hooks.slack.com/..."
                  className="w-full px-3 py-2.5 bg-[#000000] border border-[#292d30] rounded-[6px] text-sm text-[#ffffff] focus:outline-none focus:border-[#ffffff]"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1.5">
                  <label className="text-[11px] font-mono text-[#a1a4a5] uppercase">Condition</label>
                  <select
                    value={autoCondition}
                    onChange={(e) => setAutoCondition(e.target.value)}
                    className="w-full px-3 py-2.5 bg-[#000000] border border-[#292d30] rounded-[6px] text-sm text-[#ffffff] focus:outline-none focus:border-[#ffffff]"
                  >
                    <option value="">Always fire</option>
                    {autoEvent === "research.completed" ? (
                      <>
                        <option value="min_severity">min cluster severity</option>
                        <option value="min_clusters">min cluster count</option>
                        <option value="query_contains">query contains</option>
                      </>
                    ) : (
                      <>
                        <option value="score_below">overall score below</option>
                        <option value="score_above">overall score above</option>
                        <option value="domain_contains">domain contains</option>
                      </>
                    )}
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-[11px] font-mono text-[#a1a4a5] uppercase">Value</label>
                  <input
                    type="text"
                    value={autoConditionValue}
                    onChange={(e) => setAutoConditionValue(e.target.value)}
                    disabled={!autoCondition}
                    placeholder={autoCondition === "query_contains" || autoCondition === "domain_contains" ? "text" : "0.8"}
                    className="w-full px-3 py-2.5 bg-[#000000] border border-[#292d30] rounded-[6px] text-sm text-[#ffffff] focus:outline-none focus:border-[#ffffff] disabled:opacity-40"
                  />
                </div>
              </div>
            </div>
            <button
              type="submit"
              disabled={creatingAuto || !autoName.trim() || !autoWebhookUrl.trim()}
              className="px-5 py-2.5 bg-[#ffffff] hover:bg-[#ffffff]/90 text-[#000000] font-medium text-sm rounded-[6px] flex items-center gap-2 transition-all disabled:opacity-40"
            >
              {creatingAuto ? <Loader2 className="h-4 w-4 animate-spin" /> : <Webhook className="h-4 w-4" />}
              Create Rule
            </button>
          </form>
        )}

        {automations.length === 0 ? (
          <div className="p-8 rounded-[16px] bg-[#000000] border border-[#292d30] text-center">
            <Webhook className="h-8 w-8 text-[#464a4d] mx-auto mb-3" />
            <p className="text-sm text-[#a1a4a5]">
              No automation rules yet. Create one to POST a signed JSON payload to any
              webhook when research completes or an SEO audit finishes.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {automations.map((r) => (
              <div key={r.id} className="p-4 rounded-[12px] bg-[#000000] border border-[#292d30] flex items-center justify-between gap-4">
                <div className="space-y-1.5 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-[#ffffff]">{r.name}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#9281f7]/10 text-[#9281f7] border border-[#9281f7]/30">
                      {r.event_type}
                    </span>
                    {Object.entries(r.conditions || {}).map(([k, v]) => (
                      <span key={k} className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#292d30]/50 text-[#a1a4a5]">
                        {k}: {String(v)}
                      </span>
                    ))}
                  </div>
                  <div className="text-[11px] font-mono text-[#6e727a] truncate">
                    {String(r.action_config?.url || "")} &bull; fired {r.fire_count}x
                    {r.last_fired_at ? ` (last: ${new Date(r.last_fired_at).toLocaleString()})` : ""}
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => toggleAutomation(r.id).then(refresh)}
                    className={`px-2.5 py-1 rounded-[6px] text-[11px] font-mono border transition-all ${
                      r.enabled
                        ? "text-[#3ad389] border-[#3ad389]/40 bg-[#3ad389]/5"
                        : "text-[#6e727a] border-[#292d30]"
                    }`}
                  >
                    {r.enabled ? "enabled" : "paused"}
                  </button>
                  <button
                    onClick={() => deleteAutomation(r.id).then(refresh)}
                    className="p-1.5 rounded text-[#6e727a] hover:text-[#ff9592] transition-colors"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
