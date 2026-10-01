"use client";

import React, { useCallback, useEffect, useMemo, useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  Database, RefreshCw, Trash2, RotateCcw, Scissors, Play, ShieldCheck,
  Workflow as WorkflowIcon, Wrench, LayoutGrid, Settings2, Search, Download,
  ExternalLink, Loader2, AlertTriangle, CheckCircle2, XCircle, Plus, Film,
  Globe, Activity, Sparkles, Clock, ChevronDown, ChevronUp, Terminal, Minus,
  Twitter, GitBranch
} from "lucide-react";
import {
  listBackups, createBackup, deleteBackup, restoreBackup,
  rankClips, cutClip, getClipFileUrl,
  runSecurityAudit, runTrafficCorrelation,
  listWorkflows, createWorkflow, deleteWorkflow, runWorkflow,
  fetchGridSignals, fetchGridChannels,
  listGatewayTools, callGatewayTool,
  getBrowserSession, setBrowserSession, getFramesStatus
} from "@/lib/lab-api";
import { SignalsDataGrid } from "@/components/SignalsDataGrid";
import { TweetAnalyzer } from "@/components/TweetAnalyzer";
import type {
  BackupManifest, ClipsRankResponse, ClipCandidate, SecurityAuditResult,
  TrafficCorrelation, Workflow, WorkflowRunResult, GridSignal, GatewayTool,
  GatewayResult, BrowserSessionInfo, FramesStatus
} from "@/lib/lab-types";

// ============================================================================
// Shared bits
// ============================================================================

const CARD = "bg-[#0c0d10] border border-[#292d30] rounded-[10px]";
const BTN_PRIMARY = "inline-flex items-center gap-1.5 text-xs font-medium px-3.5 py-2 rounded-[6px] bg-[#9281f7] text-black hover:bg-[#a99bf8] transition-colors disabled:opacity-50";
const BTN_GHOST = "inline-flex items-center gap-1.5 text-xs font-medium px-3.5 py-2 rounded-[6px] border border-[#292d30] text-[#f0f0f0] hover:border-[#ffffff] transition-colors disabled:opacity-50";
const INPUT = "w-full bg-[#000000] border border-[#292d30] rounded-[6px] px-3 py-2 text-sm text-[#ffffff] placeholder-[#5c6063] focus:outline-none focus:border-[#9281f7]/60";
const LABEL = "text-[11px] font-mono uppercase tracking-wider text-[#9ba1a6]";

function fmtBytes(n?: number): string {
  if (!n && n !== 0) return "—";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(2)} MB`;
}

function timeAgo(iso?: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso.endsWith("Z") || iso.includes("+") ? iso : iso + "Z");
  const diff = Date.now() - d.getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function SectionHeader({ icon: Icon, title, desc }: { icon: any; title: string; desc: string }) {
  return (
    <div className="flex items-start gap-3 mb-5">
      <div className="h-8 w-8 shrink-0 rounded-[8px] border border-[#292d30] bg-[#000000] flex items-center justify-center">
        <Icon className="h-4 w-4 text-[#9281f7]" />
      </div>
      <div>
        <h2 className="text-base font-semibold text-[#ffffff] tracking-tight">{title}</h2>
        <p className="text-xs text-[#9ba1a6] mt-0.5">{desc}</p>
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const map: Record<string, string> = {
    OK: "text-[#3ad389] border-[#3ad389]/40 bg-[#3ad389]/10",
    PASS: "text-[#3ad389] border-[#3ad389]/40 bg-[#3ad389]/10",
    WARN: "text-[#ffca16] border-[#ffca16]/40 bg-[#ffca16]/10",
    PARTIAL: "text-[#ffca16] border-[#ffca16]/40 bg-[#ffca16]/10",
    FAIL: "text-[#ff6465] border-[#ff6465]/40 bg-[#ff6465]/10",
    RUNNING: "text-[#70b8ff] border-[#70b8ff]/40 bg-[#70b8ff]/10",
  };
  const cls = map[status] || "text-[#9ba1a6] border-[#292d30]";
  return <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${cls}`}>{status}</span>;
}

// ============================================================================
// Tab 1 — Backups
// ============================================================================

function BackupsTab() {
  const [backups, setBackups] = useState<BackupManifest[]>([]);
  const [rotation, setRotation] = useState<{ keep: number; policy: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [confirmId, setConfirmId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listBackups();
      setBackups(data.backups || []);
      setRotation(data.rotation);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const doCreate = async () => {
    setBusy("create");
    setError(null);
    try {
      await createBackup(name.trim() || "manual", "Created from Lab UI");
      setName("");
      await load();
    } catch (e: any) { setError(e.message); }
    finally { setBusy(null); }
  };

  const doRestore = async (id: string) => {
    setBusy(id);
    setError(null);
    try {
      await restoreBackup(id);
      setConfirmId(null);
      alert("Restore complete. Restart the backend to reconnect the database.");
    } catch (e: any) { setError(e.message); }
    finally { setBusy(null); }
  };

  const doDelete = async (id: string) => {
    setBusy(id);
    try { await deleteBackup(id); await load(); }
    catch (e: any) { setError(e.message); }
    finally { setBusy(null); }
  };

  return (
    <div className="space-y-5">
      <SectionHeader icon={Database} title="Backup Snapshots"
        desc="Borg-style snapshots of pulseradar.db + transcripts cache. Immutable, checksummed, rotated." />

      <div className={`${CARD} p-4 flex flex-col sm:flex-row gap-3 sm:items-end`}>
        <div className="flex-1">
          <label className={LABEL}>Snapshot name</label>
          <input className={`${INPUT} mt-1.5`} placeholder="pre-migration" value={name}
            onChange={(e) => setName(e.target.value)} />
        </div>
        <button className={BTN_PRIMARY} onClick={doCreate} disabled={busy === "create"}>
          {busy === "create" ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />}
          Snapshot now
        </button>
        <button className={BTN_GHOST} onClick={load} disabled={loading}>
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {rotation && (
        <p className="text-[11px] font-mono text-[#9ba1a6]">
          Rotation policy: keep {rotation.keep} newest · {rotation.policy}
        </p>
      )}
      {error && <div className="text-xs text-[#ff6465] flex items-center gap-1.5"><AlertTriangle className="h-3.5 w-3.5" />{error}</div>}
      {loading && <p className="text-xs text-[#9ba1a6]">Loading snapshots…</p>}

      <div className="space-y-3">
        {backups.map((b) => (
          <div key={b.snapshot_id} className={`${CARD} p-4`}>
            <div className="flex flex-col md:flex-row md:items-center gap-3 md:gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-mono text-sm text-[#ffffff]">{b.snapshot_id}</span>
                  {b.name && b.name !== "unknown" && (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded border border-[#9281f7]/40 text-[#9281f7] bg-[#9281f7]/10">{b.name}</span>
                  )}
                </div>
                <p className="text-[11px] font-mono text-[#9ba1a6] mt-1">
                  {timeAgo(b.created_at)} · {b.file_count} files · {fmtBytes(b.total_bytes)}
                  {b.note ? ` · ${b.note}` : ""}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {confirmId === b.snapshot_id ? (
                  <>
                    <button className="text-xs px-3 py-1.5 rounded-[6px] bg-[#ff6465]/20 border border-[#ff6465]/50 text-[#ff6465]" onClick={() => doRestore(b.snapshot_id)} disabled={busy === b.snapshot_id}>
                      Overwrite live DBs?
                    </button>
                    <button className={BTN_GHOST + " !px-2.5"} onClick={() => setConfirmId(null)}>Cancel</button>
                  </>
                ) : (
                  <button className={BTN_GHOST + " !px-2.5"} title="Restore" onClick={() => setConfirmId(b.snapshot_id)}>
                    <RotateCcw className="h-3.5 w-3.5" /> Restore
                  </button>
                )}
                <button className={BTN_GHOST + " !px-2.5 hover:!border-[#ff6465]/60"} title="Delete" onClick={() => doDelete(b.snapshot_id)} disabled={busy === b.snapshot_id}>
                  {busy === b.snapshot_id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
                </button>
              </div>
            </div>
            {b.files?.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {b.files.map((f, i) => (
                  <span key={i} className="text-[10px] font-mono px-2 py-1 rounded border border-[#292d30] text-[#9ba1a6]">
                    {f.target}: {f.status === "ok" ? fmtBytes(f.size_bytes) : f.status}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
        {!loading && backups.length === 0 && (
          <div className={`${CARD} p-8 text-center text-sm text-[#9ba1a6]`}>
            No snapshots yet — create your first one above.
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Tab 2 — Clip Studio
// ============================================================================

function ClipsTab() {
  const [url, setUrl] = useState("");
  const [maxClips, setMaxClips] = useState(3);
  const [loading, setLoading] = useState(false);
  const [cutting, setCutting] = useState<string | null>(null);
  const [result, setResult] = useState<ClipsRankResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);

  const doRank = async () => {
    setLoading(true); setError(null); setResult(null); setDownloadUrl(null);
    try { setResult(await rankClips(url.trim(), maxClips)); }
    catch (e: any) { setError(e.message.replace(/"/g, "")); }
    finally { setLoading(false); }
  };

  const doCut = async (c: ClipCandidate) => {
    setCutting(`${c.start}`);
    setError(null);
    try {
      const res = await cutClip(url.trim(), c.start, c.end);
      setDownloadUrl(getClipFileUrl(res.file));
    } catch (e: any) { setError(e.message.replace(/"/g, "")); }
    finally { setCutting(null); }
  };

  return (
    <div className="space-y-5">
      <SectionHeader icon={Scissors} title="Clip Studio"
        desc="Ranks the most viral-ready segments of any YouTube video (hook words, questions, pacing) and cuts mp4s." />

      <div className={`${CARD} p-4 space-y-3`}>
        <div>
          <label className={LABEL}>YouTube URL or video ID</label>
          <input className={`${INPUT} mt-1.5`} placeholder="https://www.youtube.com/watch?v=…" value={url}
            onChange={(e) => setUrl(e.target.value)} />
        </div>
        <div className="flex flex-col sm:flex-row gap-3 sm:items-end">
          <div className="w-full sm:w-40">
            <label className={LABEL}>Max clips</label>
            <select className={`${INPUT} mt-1.5`} value={maxClips} onChange={(e) => setMaxClips(Number(e.target.value))}>
              {[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
          <button className={BTN_PRIMARY} onClick={doRank} disabled={!url.trim() || loading}>
            {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
            Rank viral segments
          </button>
        </div>
      </div>

      {error && <div className="text-xs text-[#ff6465] flex items-center gap-1.5"><AlertTriangle className="h-3.5 w-3.5" />{error}</div>}
      {downloadUrl && (
        <a href={downloadUrl} download className="text-xs text-[#3ad389] inline-flex items-center gap-1.5 border border-[#3ad389]/40 rounded-[6px] px-3 py-2 hover:bg-[#3ad389]/10">
          <Download className="h-3.5 w-3.5" /> Download your cut clip
        </a>
      )}

      {result && (
        <div className="space-y-3">
          <p className="text-[11px] font-mono text-[#9ba1a6]">
            {result.video_title} · {result.clips.length} clips from {result.candidates_evaluated} candidates · {result.algorithm}
          </p>
          {result.clips.map((c) => (
            <div key={`${c.start}`} className={`${CARD} p-4`}>
              <div className="flex flex-col md:flex-row gap-4">
                <div className="md:w-28 shrink-0">
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-semibold text-[#9281f7]">{Math.round(c.score * 100)}</span>
                    <span className="text-[10px] font-mono text-[#9ba1a6]">/100</span>
                  </div>
                  <div className="h-1.5 mt-1.5 rounded bg-[#292d30]/60 overflow-hidden">
                    <div className="h-full bg-[#9281f7]" style={{ width: `${Math.round(c.score * 100)}%` }} />
                  </div>
                  <p className="text-[10px] font-mono text-[#9ba1a6] mt-2">{c.duration.toFixed(0)}s · #{c.rank}</p>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <a href={c.permalink} target="_blank" rel="noreferrer"
                      className="text-xs font-mono text-[#70b8ff] hover:underline inline-flex items-center gap-1">
                      <Play className="h-3 w-3" /> {c.start_ts} → {c.end.toFixed(0)}s <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                  <p className="text-sm text-[#d8dadc] mt-2 line-clamp-3">{c.text}</p>
                  <button className={BTN_GHOST + " mt-3"} onClick={() => doCut(c)} disabled={cutting === `${c.start}`}>
                    {cutting === `${c.start}` ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Scissors className="h-3.5 w-3.5" />}
                    Cut mp4 (start {c.start_ts})
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Tab 3 — Security Posture
// ============================================================================

function SecurityTab() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SecurityAuditResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setLoading(true); setError(null); setResult(null);
    try { setResult(await runSecurityAudit(url.trim())); }
    catch (e: any) { setError(e.message.replace(/"/g, "")); }
    finally { setLoading(false); }
  };

  const gradeColor = (g: string) =>
    g === "A" ? "text-[#3ad389]" : g === "B" ? "text-[#70b8ff]" : g === "C" ? "text-[#ffca16]" : "text-[#ff6465]";

  return (
    <div className="space-y-5">
      <SectionHeader icon={ShieldCheck} title="Security Posture Audit"
        desc="Passive header hygiene, cookie flags & exposure probes. No exploitation — safe to run on any site you can reach." />

      <div className={`${CARD} p-4 flex flex-col sm:flex-row gap-3 sm:items-end`}>
        <div className="flex-1">
          <label className={LABEL}>Target URL</label>
          <input className={`${INPUT} mt-1.5`} placeholder="example.com" value={url}
            onChange={(e) => setUrl(e.target.value)} onKeyDown={(e) => e.key === "Enter" && url.trim() && run()} />
        </div>
        <button className={BTN_PRIMARY} onClick={run} disabled={!url.trim() || loading}>
          {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <ShieldCheck className="h-3.5 w-3.5" />}
          Run audit
        </button>
      </div>

      {error && <div className="text-xs text-[#ff6465] flex items-center gap-1.5"><AlertTriangle className="h-3.5 w-3.5" />{error}</div>}

      {result && (
        <div className="space-y-4">
          <div className={`${CARD} p-5 flex flex-col sm:flex-row items-center gap-6`}>
            <div className="text-center">
              <div className={`text-5xl font-bold ${gradeColor(result.grade)}`}>{result.grade}</div>
              <div className="text-[11px] font-mono text-[#9ba1a6] mt-1">{result.score}/100</div>
            </div>
            <div className="flex-1 w-full">
              <p className="text-sm text-[#ffffff] font-mono break-all">{result.url}</p>
              <div className="flex gap-4 mt-2 text-[11px] font-mono">
                <span className="text-[#3ad389]">{result.status_counts.PASS} pass</span>
                <span className="text-[#ffca16]">{result.status_counts.PARTIAL} partial</span>
                <span className="text-[#ff6465]">{result.status_counts.FAIL} fail</span>
              </div>
              {result.critical_failures.length > 0 && (
                <div className="mt-3 text-xs text-[#ff6465] flex items-start gap-1.5">
                  <XCircle className="h-4 w-4 shrink-0 mt-0.5" />
                  <span>Critical: {result.critical_failures.map((f) => f.check).join(", ")}</span>
                </div>
              )}
            </div>
          </div>
          <div className={`${CARD} divide-y divide-[#292d30]/60`}>
            {result.findings.map((f, i) => (
              <div key={i} className="p-3.5 flex items-start gap-3">
                <div className="mt-0.5 shrink-0">
                  {f.status === "PASS" ? <CheckCircle2 className="h-4 w-4 text-[#3ad389]" />
                    : f.status === "PARTIAL" ? <AlertTriangle className="h-4 w-4 text-[#ffca16]" />
                    : <XCircle className="h-4 w-4 text-[#ff6465]" />}
                </div>
                <div className="min-w-0">
                  <p className="text-sm text-[#ffffff] font-medium">{f.check}</p>
                  <p className="text-xs text-[#9ba1a6] mt-0.5 break-words">{f.detail}</p>
                </div>
                <div className="ml-auto shrink-0"><StatusPill status={f.status} /></div>
              </div>
            ))}
          </div>
          <p className="text-[11px] font-mono text-[#9ba1a6] flex items-start gap-1.5">
            <Terminal className="h-3.5 w-3.5 shrink-0 mt-0.5" /> {result.boundary}
          </p>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Tab 4 — Workflows
// ============================================================================

const STEP_TYPES = [
  { id: "research.run", label: "Research sweep" },
  { id: "seo.audit", label: "SEO audit" },
  { id: "lab.backup", label: "Backup snapshot" },
  { id: "webhook", label: "Webhook" },
];

interface StepDraft { name: string; type: string; config: Record<string, any>; depends_on: string[] }

function WorkflowsTab() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastRun, setLastRun] = useState<{ name: string; result: WorkflowRunResult } | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  // Builder state
  const [wfName, setWfName] = useState("");
  const [steps, setSteps] = useState<StepDraft[]>([{ name: "sweep", type: "research.run", config: { query: "", channels: "reddit,hackernews", limit: 15 }, depends_on: [] }]);

  const load = useCallback(async () => {
    setLoading(true);
    const data = await listWorkflows();
    setWorkflows(data.workflows || []);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const updateStep = (i: number, patch: Partial<StepDraft>) => {
    setSteps((s) => s.map((st, idx) => idx === i ? { ...st, ...patch } : st));
  };
  const updateConfig = (i: number, key: string, value: any) => {
    setSteps((s) => s.map((st, idx) => idx === i ? { ...st, config: { ...st.config, [key]: value } } : st));
  };

  const doCreate = async () => {
    setCreating(true); setError(null);
    try {
      const payloadSteps = steps.map((s) => ({
        name: s.name.trim(),
        type: s.type,
        config: s.type === "research.run"
          ? { query: s.config.query, channels: String(s.config.channels || "").split(",").map((c: string) => c.trim()).filter(Boolean), limit: Number(s.config.limit) || 15 }
          : s.config,
        depends_on: s.depends_on,
      }));
      await createWorkflow({ name: wfName.trim(), steps: payloadSteps });
      setWfName(""); setSteps([{ name: "sweep", type: "research.run", config: { query: "", channels: "reddit,hackernews", limit: 15 }, depends_on: [] }]);
      await load();
    } catch (e: any) { setError(e.message.replace(/"/g, "")); }
    finally { setCreating(false); }
  };

  const doRun = async (wf: Workflow) => {
    setBusy(wf.id); setError(null); setLastRun(null);
    try {
      const result = await runWorkflow(wf.id);
      setLastRun({ name: wf.name, result });
      await load();
    } catch (e: any) { setError(e.message.replace(/"/g, "")); }
    finally { setBusy(null); }
  };

  const doDelete = async (id: string) => {
    setBusy(id);
    try { await deleteWorkflow(id); await load(); }
    catch (e: any) { setError(e.message); }
    finally { setBusy(null); }
  };

  return (
    <div className="space-y-5">
      <SectionHeader icon={WorkflowIcon} title="Workflow Orchestrator"
        desc="Dagu-style DAGs: chain research sweeps, SEO audits, backups and webhooks. Cycle-safe, run history included." />

      {/* Builder */}
      <div className={`${CARD} p-4 space-y-4`}>
        <div>
          <label className={LABEL}>Workflow name</label>
          <input className={`${INPUT} mt-1.5`} placeholder="weekly-pulse" value={wfName} onChange={(e) => setWfName(e.target.value)} />
        </div>

        <div className="space-y-3">
          <label className={LABEL}>Steps (DAG)</label>
          {steps.map((s, i) => (
            <div key={i} className="border border-[#292d30] rounded-[8px] p-3 space-y-3 bg-[#000000]/40">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="text-[10px] font-mono text-[#9ba1a6]">Step name</label>
                  <input className={`${INPUT} mt-1`} value={s.name} onChange={(e) => updateStep(i, { name: e.target.value })} />
                </div>
                <div>
                  <label className="text-[10px] font-mono text-[#9ba1a6]">Type</label>
                  <select className={`${INPUT} mt-1`} value={s.type} onChange={(e) => updateStep(i, { type: e.target.value })}>
                    {STEP_TYPES.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-mono text-[#9ba1a6]">Depends on (comma names)</label>
                  <input className={`${INPUT} mt-1`} placeholder="—" value={s.depends_on.join(",")}
                    onChange={(e) => updateStep(i, { depends_on: e.target.value.split(",").map((d) => d.trim()).filter(Boolean) })} />
                </div>
              </div>
              {s.type === "research.run" && (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="sm:col-span-2">
                    <label className="text-[10px] font-mono text-[#9ba1a6]">Query</label>
                    <input className={`${INPUT} mt-1`} value={s.config.query || ""} onChange={(e) => updateConfig(i, "query", e.target.value)} />
                  </div>
                  <div>
                    <label className="text-[10px] font-mono text-[#9ba1a6]">Channels</label>
                    <input className={`${INPUT} mt-1`} value={s.config.channels || ""} onChange={(e) => updateConfig(i, "channels", e.target.value)} />
                  </div>
                </div>
              )}
              {s.type === "seo.audit" && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-[10px] font-mono text-[#9ba1a6]">URL</label>
                    <input className={`${INPUT} mt-1`} value={s.config.url || ""} onChange={(e) => updateConfig(i, "url", e.target.value)} />
                  </div>
                  <div>
                    <label className="text-[10px] font-mono text-[#9ba1a6]">Audit type</label>
                    <select className={`${INPUT} mt-1`} value={s.config.audit_type || "quick"} onChange={(e) => updateConfig(i, "audit_type", e.target.value)}>
                      <option value="quick">quick</option><option value="full">full</option><option value="geo">geo</option>
                    </select>
                  </div>
                </div>
              )}
              {s.type === "lab.backup" && (
                <div>
                  <label className="text-[10px] font-mono text-[#9ba1a6]">Snapshot name</label>
                  <input className={`${INPUT} mt-1`} value={s.config.name || ""} onChange={(e) => updateConfig(i, "name", e.target.value)} />
                </div>
              )}
              {s.type === "webhook" && (
                <div>
                  <label className="text-[10px] font-mono text-[#9ba1a6]">Webhook URL</label>
                  <input className={`${INPUT} mt-1`} value={s.config.url || ""} onChange={(e) => updateConfig(i, "url", e.target.value)} />
                </div>
              )}
              {steps.length > 1 && (
                <button className="text-[11px] font-mono text-[#ff6465] hover:underline inline-flex items-center gap-1"
                  onClick={() => setSteps((st) => st.filter((_, idx) => idx !== i))}>
                  <Minus className="h-3 w-3" /> Remove step
                </button>
              )}
            </div>
          ))}
          <button className={BTN_GHOST} onClick={() => setSteps((s) => [...s, { name: `step${s.length + 1}`, type: "research.run", config: { query: "", channels: "reddit", limit: 15 }, depends_on: [] }])}>
            <Plus className="h-3.5 w-3.5" /> Add step
          </button>
        </div>

        <button className={BTN_PRIMARY} onClick={doCreate} disabled={!wfName.trim() || creating}>
          {creating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <WorkflowIcon className="h-3.5 w-3.5" />}
          Create workflow
        </button>
      </div>

      {error && <div className="text-xs text-[#ff6465] flex items-center gap-1.5"><AlertTriangle className="h-3.5 w-3.5" />{error}</div>}

      {lastRun && (
        <div className={`${CARD} p-4`}>
          <p className="text-xs font-mono text-[#9ba1a6] mb-2">Last run: {lastRun.name} → <StatusPill status={lastRun.result.run.status} /></p>
          <div className="space-y-1.5">
            {lastRun.result.logs.map((l, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <StatusPill status={l.status} />
                <span className="font-mono text-[#ffffff]">{l.step}</span>
                <span className="text-[#9ba1a6] truncate">{l.error || (l.result?.items != null ? `${l.result.items} items` : "")}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Workflow list */}
      {loading && <p className="text-xs text-[#9ba1a6]">Loading workflows…</p>}
      <div className="space-y-3">
        {workflows.map((wf) => (
          <div key={wf.id} className={`${CARD} p-4`}>
            <div className="flex flex-col sm:flex-row sm:items-center gap-3">
              <div className="flex-1 min-w-0">
                <p className="font-mono text-sm text-[#ffffff]">{wf.name}</p>
                <p className="text-[11px] font-mono text-[#9ba1a6] mt-0.5">
                  {wf.steps.map((s) => s.name).join(" → ")} · {wf.runs.length} runs · created {timeAgo(wf.created_at)}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <button className={BTN_PRIMARY} onClick={() => doRun(wf)} disabled={busy === wf.id}>
                  {busy === wf.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />} Run
                </button>
                <button className={BTN_GHOST + " !px-2.5"} onClick={() => setExpanded(expanded === wf.id ? null : wf.id)}>
                  {expanded === wf.id ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                </button>
                <button className={BTN_GHOST + " !px-2.5 hover:!border-[#ff6465]/60"} onClick={() => doDelete(wf.id)} disabled={busy === wf.id}>
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
            {expanded === wf.id && wf.runs.length > 0 && (
              <div className="mt-3 border-t border-[#292d30]/60 pt-3 space-y-1.5">
                {wf.runs.slice().reverse().map((r) => (
                  <div key={r.id} className="flex items-center gap-2 text-[11px] font-mono">
                    <StatusPill status={r.status} />
                    <span className="text-[#9ba1a6]">{timeAgo(r.started)}</span>
                    <span className="text-[#5c6063]">{r.steps.map((s) => `${s.step}:${s.status}`).join(" · ")}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
        {!loading && workflows.length === 0 && (
          <div className={`${CARD} p-8 text-center text-sm text-[#9ba1a6]`}>No workflows yet — build one above.</div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Tab 5 — Tool Gateway
// ============================================================================

function GatewayTab() {
  const [tools, setTools] = useState<GatewayTool[]>([]);
  const [category, setCategory] = useState<string>("");
  const [activeTool, setActiveTool] = useState<GatewayTool | null>(null);
  const [paramValues, setParamValues] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [calling, setCalling] = useState(false);
  const [result, setResult] = useState<GatewayResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (cat: string) => {
    setLoading(true);
    try {
      const data = await listGatewayTools(cat || undefined);
      setTools(data.tools || []);
    } catch { setTools([]); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(category); }, [category, load]);

  const categories = useMemo(() => Array.from(new Set(tools.map((t) => t.category))), [tools]);

  const openTool = (t: GatewayTool) => {
    setActiveTool(t); setResult(null); setError(null);
    const init: Record<string, string> = {};
    t.params.forEach((p) => { init[p.name] = ""; });
    setParamValues(init);
  };

  const doCall = async () => {
    if (!activeTool) return;
    setCalling(true); setError(null); setResult(null);
    try {
      setResult(await callGatewayTool(activeTool.id, paramValues));
    } catch (e: any) { setError(e.message.replace(/"/g, "")); }
    finally { setCalling(false); }
  };

  return (
    <div className="space-y-5">
      <SectionHeader icon={Wrench} title="Tool Gateway"
        desc="treg philosophy — ask for the task, not the tool. One request shape across SERP, video, HN, arXiv, GitHub & web providers." />

      <div className="flex gap-2 overflow-x-auto pb-1">
        <button onClick={() => setCategory("")} className={`shrink-0 text-xs font-mono px-3 py-1.5 rounded-[6px] border transition-colors ${category === "" ? "bg-[#9281f7]/20 border-[#9281f7]/40 text-white" : "border-[#292d30] text-[#9ba1a6] hover:text-white"}`}>all</button>
        {categories.map((c) => (
          <button key={c} onClick={() => setCategory(c)} className={`shrink-0 text-xs font-mono px-3 py-1.5 rounded-[6px] border transition-colors ${category === c ? "bg-[#9281f7]/20 border-[#9281f7]/40 text-white" : "border-[#292d30] text-[#9ba1a6] hover:text-white"}`}>{c}</button>
        ))}
      </div>

      {loading && <p className="text-xs text-[#9ba1a6]">Loading catalog…</p>}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {tools.map((t) => (
          <button key={t.id} onClick={() => openTool(t)}
            className={`${CARD} p-4 text-left hover:border-[#9281f7]/50 transition-colors ${activeTool?.id === t.id ? "border-[#9281f7]/60" : ""}`}>
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-medium text-[#ffffff]">{t.name}</p>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded border border-[#292d30] text-[#9ba1a6]">{t.category}</span>
            </div>
            <p className="text-xs text-[#9ba1a6] mt-1.5 line-clamp-2">{t.description}</p>
            <p className="text-[10px] font-mono text-[#3ad389] mt-2">{t.price_hint}</p>
          </button>
        ))}
      </div>

      {activeTool && (
        <div className={`${CARD} p-4 space-y-4`}>
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-[#ffffff]">{activeTool.name}</h3>
            <button className="text-[#9ba1a6] hover:text-white" onClick={() => setActiveTool(null)}>✕</button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {activeTool.params.map((p) => (
              <div key={p.name}>
                <label className={LABEL}>{p.name}{p.required ? " *" : ""}</label>
                <input className={`${INPUT} mt-1.5`} placeholder={p.description} value={paramValues[p.name] || ""}
                  onChange={(e) => setParamValues((v) => ({ ...v, [p.name]: e.target.value }))} />
              </div>
            ))}
          </div>
          <button className={BTN_PRIMARY} onClick={doCall} disabled={calling}>
            {calling ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />} Call tool
          </button>

          {error && <div className="text-xs text-[#ff6465] flex items-center gap-1.5"><AlertTriangle className="h-3.5 w-3.5" />{error}</div>}
          {result?.markdown && (
            <pre className="text-[11px] font-mono text-[#d8dadc] bg-[#000000] border border-[#292d30] rounded-[8px] p-3 max-h-80 overflow-auto whitespace-pre-wrap">{result.markdown.slice(0, 4000)}</pre>
          )}
          {result?.results && result.results.length > 0 && (
            <div className="divide-y divide-[#292d30]/60 border border-[#292d30] rounded-[8px]">
              {result.results.slice(0, 20).map((r: any, i: number) => (
                <a key={i} href={r.url} target="_blank" rel="noreferrer" className="block p-3 hover:bg-[#9281f7]/5">
                  <div className="flex items-center gap-2">
                    {r.rank && <span className="text-[10px] font-mono text-[#9281f7]">#{r.rank}</span>}
                    <p className="text-xs text-[#70b8ff] truncate">{r.title || r.external_id}</p>
                    {r.engagement_score != null && <span className="ml-auto text-[10px] font-mono text-[#9ba1a6] shrink-0">▲ {r.engagement_score}</span>}
                  </div>
                  <p className="text-[11px] text-[#9ba1a6] mt-0.5 line-clamp-2">{r.snippet || r.content}</p>
                </a>
              ))}
            </div>
          )}
          {result && !result.success && !error && (
            <p className="text-xs text-[#ffca16]">{result.error || "No results."}</p>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Tab 6 — Signals Mega-Grid
// ============================================================================

function SignalsTab() {
  const [items, setItems] = useState<GridSignal[]>([]);
  const [channels, setChannels] = useState<{ channel: string; count: number }[]>([]);
  const [q, setQ] = useState("");
  const [channel, setChannel] = useState("");
  const [sort, setSort] = useState("engagement");
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [detail, setDetail] = useState<GridSignal | null>(null);

  const load = useCallback(async (reset: boolean) => {
    if (reset) { setLoading(true); setOffset(0); }
    else { setLoadingMore(true); }
    try {
      const off = reset ? 0 : offset;
      const data = await fetchGridSignals({ q: q || undefined, channel: channel || undefined, sort, offset: off, limit: 200 });
      setItems((prev) => reset ? data.items : [...prev, ...data.items]);
      setOffset(off + data.items.length);
      setHasMore(data.items.length >= 200);
    } catch { /* keep prior items */ }
    finally { setLoading(false); setLoadingMore(false); }
  }, [q, channel, sort, offset]);

  useEffect(() => { fetchGridChannels().then(setChannels); }, []);
  useEffect(() => { load(true); /* eslint-disable-line */ }, [channel, sort]);

  return (
    <div className="space-y-5">
      <SectionHeader icon={LayoutGrid} title="Signals Mega-Grid"
        desc="Every raw signal across all sessions — millions-ready virtualization feed with channel facets and engagement sort." />

      <div className={`${CARD} p-4 flex flex-col md:flex-row gap-3 md:items-end`}>
        <div className="flex-1">
          <label className={LABEL}>Search content</label>
          <input className={`${INPUT} mt-1.5`} placeholder="search full text…" value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && load(true)} />
        </div>
        <div className="w-full md:w-44">
          <label className={LABEL}>Channel</label>
          <select className={`${INPUT} mt-1.5`} value={channel} onChange={(e) => setChannel(e.target.value)}>
            <option value="">All channels</option>
            {channels.map((c) => <option key={c.channel} value={c.channel}>{c.channel} ({c.count})</option>)}
          </select>
        </div>
        <div className="w-full md:w-40">
          <label className={LABEL}>Sort</label>
          <select className={`${INPUT} mt-1.5`} value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="engagement">Top engagement</option>
            <option value="recent">Most recent</option>
          </select>
        </div>
        <button className={BTN_GHOST} onClick={() => load(true)} disabled={loading}>
          <Search className="h-3.5 w-3.5" /> Apply
        </button>
      </div>

      {loading && <p className="text-xs text-[#9ba1a6]">Loading signals…</p>}

      {/* Glide Data Grid — canvas virtualization for every device */}
      <SignalsDataGrid
        rows={items}
        loading={loading}
        hasMore={hasMore}
        loadingMore={loadingMore}
        onRowClick={(r) => setDetail(r)}
        onLoadMore={() => load(false)}
      />

      {/* Row detail drawer */}
      {detail && (
        <div className="fixed inset-0 z-50 bg-[#000000]/70 backdrop-blur-sm flex items-end sm:items-center justify-center sm:justify-end" onClick={() => setDetail(null)}>
          <div className={`${CARD} w-full sm:w-[440px] max-h-[80vh] sm:max-h-[86vh] sm:mr-4 overflow-y-auto p-5 space-y-3 rounded-t-[16px] sm:rounded-[16px]`}
            onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded border border-[#292d30] text-[#9ba1a6] uppercase">{detail.channel}</span>
              <button onClick={() => setDetail(null)} className="text-[#9ba1a6] hover:text-white text-sm">✕</button>
            </div>
            <a href={detail.url} target="_blank" rel="noreferrer" className="text-sm text-[#9281f7] hover:underline font-medium break-words">{detail.title} ↗</a>
            <p className="text-xs text-[#a1a4a5] leading-relaxed">{detail.preview}…</p>
            <div className="flex items-center gap-3 text-[11px] font-mono text-[#6e727a] pt-2 border-t border-[#292d30]/60">
              <span>{detail.author || "—"}</span>
              <span>▲ {detail.engagement.toLocaleString()}</span>
              <span>{timeAgo(detail.created_at)}</span>
              {detail.has_transcript && <span className="text-[#3ad389]">▶ transcript</span>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Tab 7 — System (browser session, frames status, traffic correlation)
// ============================================================================

function Sparkline({ values }: { values: number[] }) {
  if (values.length < 2) return null;
  const max = Math.max(...values), min = Math.min(...values);
  const range = max - min || 1;
  const pts = values.map((v, i) => `${(i / (values.length - 1)) * 100},${34 - ((v - min) / range) * 30}`).join(" ");
  return (
    <svg viewBox="0 0 100 36" className="w-full h-10" preserveAspectRatio="none">
      <polyline points={pts} fill="none" stroke="#9281f7" strokeWidth="1.6" />
    </svg>
  );
}

function SystemTab() {
  const [session, setSession] = useState<BrowserSessionInfo | null>(null);
  const [frames, setFrames] = useState<FramesStatus | null>(null);
  const [dirInput, setDirInput] = useState("");
  const [busy, setBusy] = useState(false);

  const [domain, setDomain] = useState("");
  const [corrLoading, setCorrLoading] = useState(false);
  const [corr, setCorr] = useState<TrafficCorrelation | null>(null);
  const [corrError, setCorrError] = useState<string | null>(null);

  useEffect(() => {
    getBrowserSession().then((s) => { setSession(s); setDirInput(s.user_data_dir); }).catch(() => {});
    getFramesStatus().then(setFrames).catch(() => {});
  }, []);

  const saveDir = async () => {
    setBusy(true);
    try { await setBrowserSession(dirInput); setSession(await getBrowserSession()); }
    finally { setBusy(false); }
  };

  const runCorr = async () => {
    setCorrLoading(true); setCorrError(null); setCorr(null);
    try { setCorr(await runTrafficCorrelation(domain.trim())); }
    catch (e: any) { setCorrError(e.message.replace(/"/g, "")); }
    finally { setCorrLoading(false); }
  };

  return (
    <div className="space-y-5">
      <SectionHeader icon={Settings2} title="System & Sessions"
        desc="Authenticated browsing profile, frame-extraction capabilities, and SEO→traffic correlation." />

      {/* Browser session */}
      <div className={`${CARD} p-4 space-y-3`}>
        <div className="flex items-center gap-2">
          <Globe className="h-4 w-4 text-[#9281f7]" />
          <h3 className="text-sm font-medium text-[#ffffff]">Authenticated Browser Session (BrowserSkill pattern)</h3>
        </div>
        {session?.configured ? (
          <p className="text-xs text-[#3ad389] font-mono break-all">✓ {session.user_data_dir}</p>
        ) : (
          <p className="text-xs text-[#9ba1a6]">{session?.benefit}</p>
        )}
        <div className="flex flex-col sm:flex-row gap-2">
          <input className={INPUT} placeholder="C:\Users\you\AppData\Local\Google\Chrome\User Data"
            value={dirInput} onChange={(e) => setDirInput(e.target.value)} />
          <button className={BTN_PRIMARY + " shrink-0"} onClick={saveDir} disabled={busy}>
            {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />} Save
          </button>
        </div>
        {session && (
          <ul className="text-[11px] font-mono text-[#9ba1a6] space-y-1">
            {session.how_to.map((h, i) => <li key={i}>· {h}</li>)}
          </ul>
        )}
      </div>

      {/* Frames capabilities */}
      <div className={`${CARD} p-4 space-y-3`}>
        <div className="flex items-center gap-2">
          <Film className="h-4 w-4 text-[#9281f7]" />
          <h3 className="text-sm font-medium text-[#ffffff]">Frame Extraction & OCR capabilities</h3>
        </div>
        {frames ? (
          <div className="flex flex-wrap gap-2">
            {[["yt-dlp", frames.yt_dlp], ["ffmpeg", frames.ffmpeg], ["tesseract", frames.tesseract], ["pillow", frames.pil]].map(([name, ok]) => (
              <span key={name as string} className={`text-[10px] font-mono px-2 py-1 rounded border ${ok ? "text-[#3ad389] border-[#3ad389]/40" : "text-[#ff6465] border-[#ff6465]/40"}`}>
                {ok ? "✓" : "✕"} {name as string}
              </span>
            ))}
          </div>
        ) : <p className="text-xs text-[#9ba1a6]">Probing…</p>}
        {frames && !frames.ocr_ready && (
          <div className="text-[11px] font-mono text-[#9ba1a6] space-y-0.5">
            <p>Install to unlock OCR on video frames:</p>
            {frames.install.map((c, i) => <p key={i} className="text-[#70b8ff]">  {c}</p>)}
          </div>
        )}
      </div>

      {/* Traffic correlation */}
      <div className={`${CARD} p-4 space-y-3`}>
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-[#9281f7]" />
          <h3 className="text-sm font-medium text-[#ffffff]">SEO Score → Traffic Correlation</h3>
        </div>
        <div className="flex flex-col sm:flex-row gap-2">
          <input className={INPUT} placeholder="yourdomain.com" value={domain}
            onChange={(e) => setDomain(e.target.value)} onKeyDown={(e) => e.key === "Enter" && domain.trim() && runCorr()} />
          <button className={BTN_PRIMARY + " shrink-0"} onClick={runCorr} disabled={!domain.trim() || corrLoading}>
            {corrLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <BarIcon />} Correlate
          </button>
        </div>
        {corrError && <p className="text-xs text-[#ff6465]">{corrError}</p>}
        {corr && (
          <div className="space-y-3">
            <p className="text-xs text-[#d8dadc]">{corr.interpretation}</p>
            {corr.traffic_series.length >= 2 && (
              <div className="border border-[#292d30] rounded-[8px] p-3">
                <p className="text-[10px] font-mono text-[#9ba1a6] mb-1">Sessions across audit history</p>
                <Sparkline values={corr.traffic_series.map((t) => t.sessions)} />
              </div>
            )}
            <p className="text-[11px] font-mono text-[#9ba1a6]">{corr.note}</p>
            {corr.audits.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {corr.audits.slice(0, 6).map((a) => (
                  <span key={a.audit_id} className="text-[10px] font-mono px-2 py-1 rounded border border-[#292d30] text-[#9ba1a6]">
                    {new Date(a.date).toLocaleDateString()}: {a.overall_score}/100
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function BarIcon() {
  return <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18" /><path d="M7 16v-5" /><path d="M12 16V8" /><path d="M17 16v-9" /></svg>;
}

// ============================================================================
// Tab 8 — Interactive Diagrams (Archify pattern)
// ============================================================================

function DiagramTab() {
  const [markdown, setMarkdown] = useState("# Product Plan\n\n## Goals\n- Cut research time from hours to minutes\n- Every claim permalinked to evidence\n\n## Channels\n- Reddit pain-point sweeps\n- YouTube transcript mining\n- X/Twitter discourse\n\n## Deliverables\n- Grounded PRD\n- Office workbook\n- Viral promo clips");
  const [title, setTitle] = useState("Product Plan");
  const [building, setBuilding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const build = async () => {
    setBuilding(true); setError(null);
    try {
      const { renderInteractiveDiagram } = await import("@/lib/lab-api");
      const html = await renderInteractiveDiagram(title.trim() || "Interactive Diagram", markdown);
      const blob = new Blob([html], { type: "text/html" });
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank");
      setTimeout(() => URL.revokeObjectURL(url), 120000);
    } catch (e: any) {
      setError(e.message?.replace(/"/g, "") || "Diagram build failed");
    } finally {
      setBuilding(false);
    }
  };

  return (
    <div className="space-y-5">
      <SectionHeader icon={GitBranch} title="Interactive Diagram Studio"
        desc="Archify pattern — paste a PRD or plan, get an explorable mindmap: pan, zoom, collapse branches. Deterministic layout, zero hallucination." />

      <div className={`${CARD} p-4 space-y-3`}>
        <div className="flex flex-col sm:flex-row gap-3 sm:items-end">
          <div className="flex-1">
            <label className={LABEL}>Diagram title</label>
            <input className={`${INPUT} mt-1.5`} value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <button className={BTN_PRIMARY} onClick={build} disabled={building || !markdown.trim()}>
            {building ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <GitBranch className="h-3.5 w-3.5" />}
            Build interactive diagram
          </button>
        </div>
        <div>
          <label className={LABEL}>Markdown (## sections become branches, bullets become leaves)</label>
          <textarea
            className={`${INPUT} mt-1.5 font-mono text-xs min-h-[220px]`}
            value={markdown}
            onChange={(e) => setMarkdown(e.target.value)}
            spellCheck={false}
          />
        </div>
        {error && <p className="text-xs text-[#ff6465]">{error}</p>}
      </div>

      <div className={`${CARD} p-4`}>
        <p className="text-xs text-[#9ba1a6] leading-relaxed">
          <span className="text-[#9281f7] font-medium">How it works:</span> the parser reads ## sections and bullet
          lists from any markdown — PRDs, briefs, plans. Layout is a collision-free left-to-right tree rendered as
          inline SVG with pointer pan, wheel zoom, per-branch collapse, and hover highlighting. Output is one
          self-contained HTML file you can share with anyone.
        </p>
      </div>
    </div>
  );
}

// ============================================================================
// Page shell with tabs
// ============================================================================

const TABS = [
  { id: "backups", label: "Backups", icon: Database },
  { id: "clips", label: "Clip Studio", icon: Scissors },
  { id: "security", label: "Security", icon: ShieldCheck },
  { id: "workflows", label: "Workflows", icon: WorkflowIcon },
  { id: "gateway", label: "Tool Gateway", icon: Wrench },
  { id: "signals", label: "Signals Grid", icon: LayoutGrid },
  { id: "tweets", label: "Tweet Analyzer", icon: Twitter },
  { id: "diagrams", label: "Diagrams", icon: GitBranch },
  { id: "system", label: "System", icon: Settings2 },
];

export default function LabPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#000000]" />}>
      <LabPageContent />
    </Suspense>
  );
}

function LabPageContent() {
  const searchParams = useSearchParams();
  const initialTab = searchParams?.get("tab") || "backups";
  const validTabs = TABS.map((t) => t.id);
  const [tab, setTab] = useState(validTabs.includes(initialTab) ? initialTab : "backups");

  return (
    <div className="min-h-screen bg-[#000000]">
      <div className="mx-auto w-full max-w-[1200px] px-4 sm:px-6 lg:px-8 py-8 sm:py-10">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-[10px] border border-[#9281f7]/40 bg-[#9281f7]/10 flex items-center justify-center">
              <Sparkles className="h-5 w-5 text-[#9281f7]" />
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-semibold text-[#ffffff] tracking-tight">Lab</h1>
              <p className="text-xs sm:text-sm text-[#9ba1a6]">
                Seven new capability modules integrated from your OS project library.
              </p>
            </div>
          </div>
        </div>

        {/* Tabs — horizontally scrollable on mobile */}
        <div className="mb-7 -mx-4 px-4 overflow-x-auto sm:mx-0 sm:px-0">
          <div className="flex gap-1 border border-[#292d30] rounded-[8px] p-1 bg-[#0c0d10] w-max min-w-full sm:w-max">
            {TABS.map((t) => {
              const Icon = t.icon;
              const active = tab === t.id;
              return (
                <button key={t.id} onClick={() => setTab(t.id)}
                  className={`shrink-0 px-3 py-1.5 rounded-[6px] text-xs font-mono flex items-center gap-1.5 transition-all ${
                    active ? "bg-[#9281f7]/20 border border-[#9281f7]/40 text-[#ffffff] font-medium"
                           : "text-[#a1a4a5] hover:text-[#ffffff] border border-transparent"}`}>
                  <Icon className="h-3.5 w-3.5 text-[#9281f7]" />
                  <span>{t.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Tab content */}
        <div key={tab} className="animate-[fadeIn_0.2s_ease-out]">
          {tab === "backups" && <BackupsTab />}
          {tab === "clips" && <ClipsTab />}
          {tab === "security" && <SecurityTab />}
          {tab === "workflows" && <WorkflowsTab />}
          {tab === "gateway" && <GatewayTab />}
          {tab === "signals" && <SignalsTab />}
          {tab === "tweets" && <TweetAnalyzer />}
          {tab === "diagrams" && <DiagramTab />}
          {tab === "system" && <SystemTab />}
        </div>
      </div>
    </div>
  );
}
