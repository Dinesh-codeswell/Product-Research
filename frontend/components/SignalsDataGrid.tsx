"use client";

import React, { useCallback, useMemo, useState, useEffect } from "react";
import DataGrid, { GridColumn, GridCell, GridCellKind, Item } from "@glideapps/glide-data-grid";
import { ExternalLink, Youtube, Loader2 } from "lucide-react";

/**
 * SignalsDataGrid — real Glide Data Grid (@glideapps/glide-data-grid) integration.
 *
 * Canvas-rendered virtualization (the glide-data-grid pattern): only visible
 * cells are painted, so hundreds of thousands of harvested signals scroll at
 * native speed. Data is fetched from /lab/grid/signals in pages and appended
 * to an in-memory array; getCellForContent feeds the canvas on demand.
 */

export interface GridRow {
  id: string;
  channel: string;
  title: string;
  author?: string | null;
  engagement: number;
  url: string;
  created_at: string;
  preview: string;
  has_transcript: boolean;
}

const CHANNEL_COLORS: Record<string, string> = {
  reddit: "#ff6465",
  youtube: "#ff9592",
  hackernews: "#ffca16",
  github: "#baa7ff",
  twitter: "#70b8ff",
  google: "#9281f7",
  v2ex: "#3ad389",
  xueqiu: "#3ad389",
  bilibili: "#70b8ff",
  arxiv: "#baa7ff",
  techmeme: "#3b9eff",
  hiring: "#3ad389",
  exa: "#9281f7",
  web: "#6e727a",
};

function timeAgo(iso: string): string {
  const d = new Date(iso.endsWith("Z") || iso.includes("+") ? iso : iso + "Z");
  const diff = Date.now() - d.getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "now";
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h`;
  return `${Math.floor(h / 24)}d`;
}

interface Props {
  rows: GridRow[];
  loading?: boolean;
  hasMore?: boolean;
  loadingMore?: boolean;
  onRowClick?: (row: GridRow) => void;
  onLoadMore?: () => void;
  totalEstimate?: number;
}

export function SignalsDataGrid({ rows, loading, hasMore, loadingMore, onRowClick, onLoadMore, totalEstimate }: Props) {
  const [gridW, setGridW] = useState(1100);
  const [gridH, setGridH] = useState(560);
  const wrapRef = React.useRef<HTMLDivElement>(null);

  // Responsive canvas sizing (glide requires explicit px dimensions)
  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect?.width ?? 1100;
      setGridW(Math.max(320, Math.floor(w)));
      setGridH(window.innerHeight < 800 ? Math.max(380, window.innerHeight - 380) : 560);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const columns: GridColumn[] = useMemo(
    () => [
      { title: "Signal", id: "title", width: Math.max(240, Math.floor(gridW * 0.42)) },
      { title: "Channel", id: "channel", width: 110 },
      { title: "Author", id: "author", width: 130 },
      { title: "▲ Eng.", id: "engagement", width: 88 },
      { title: "When", id: "when", width: 72 },
      { title: "", id: "open", width: 44 },
    ],
    [gridW]
  );

  const getCellContent = useCallback(
    (cell: Item): GridCell => {
      const [col, row] = cell;
      const r: GridRow | undefined = rows[row];
      if (!r) return { kind: GridCellKind.Text, data: "", displayData: "", allowOverlay: false };

      const pad = (s: string, max: number) => (s.length > max ? s.slice(0, max - 1) + "…" : s);

      switch (col) {
        case 0:
          return {
            kind: GridCellKind.Text,
            data: pad(r.title || r.preview, 160),
            displayData: pad(r.title || r.preview, 160),
            allowOverlay: false,
          };
        case 1:
          return {
            kind: GridCellKind.Text,
            data: r.channel,
            displayData: r.channel,
            allowOverlay: false,
          };
        case 2:
          return {
            kind: GridCellKind.Text,
            data: r.author || "",
            displayData: pad(r.author || "—", 24),
            allowOverlay: false,
          };
        case 3:
          return {
            kind: GridCellKind.Number,
            data: r.engagement,
            displayData: r.engagement.toLocaleString(),
            allowOverlay: false,
          };
        case 4:
          return {
            kind: GridCellKind.Text,
            data: r.created_at,
            displayData: timeAgo(r.created_at),
            allowOverlay: false,
          };
        case 5:
          return {
            kind: GridCellKind.Text,
            data: r.url,
            displayData: r.has_transcript ? "▶" : "↗",
            allowOverlay: false,
          };
        default:
          return { kind: GridCellKind.Text, data: "", displayData: "", allowOverlay: false };
      }
    },
    [rows]
  );

  // Theme matched to PulseRadar's Resend-style dark palette
  const theme = useMemo(
    () => ({
      accentColor: "#9281f7",
      accentLight: "rgba(146,129,247,0.15)",
      textDark: "#d8dadc",
      textMedium: "#9ba1a6",
      textLight: "#5c6063",
      textHeader: "#a1a4a5",
      headerIconColor: "#9281f7",
      bgCell: "#0c0d10",
      bgCellMedium: "#101216",
      bgHeader: "#000000",
      bgHeaderHasFocus: "#121418",
      horizontalBorder: "#1c1f24",
      verticalBorder: "#1c1f24",
      borderColor: "#292d30",
      headerFontStyle: "600 11px",
      baseFontStyle: "12.5px",
      cellHorizontalPadding: 10,
      lineHeight: 20,
    }),
    []
  );

  return (
    <div ref={wrapRef} className="w-full">
      <div className="flex items-center justify-between mb-2 text-[11px] font-mono text-[#9ba1a6]">
        <span>
          canvas-rendered · {rows.length.toLocaleString()} rows loaded
          {totalEstimate ? ` of ~${totalEstimate.toLocaleString()}` : ""} · glide-data-grid engine
        </span>
        {hasMore && (
          <button
            onClick={onLoadMore}
            disabled={loadingMore}
            className="inline-flex items-center gap-1.5 text-[#9281f7] hover:text-[#ffffff] border border-[#292d30] hover:border-[#9281f7]/50 rounded-[6px] px-2.5 py-1 transition-colors"
          >
            {loadingMore ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
            Load 200 more
          </button>
        )}
      </div>
      <div className="rounded-[10px] border border-[#292d30] overflow-hidden">
        <DataGrid
          columns={columns}
          rows={rows.length}
          getCellContent={getCellContent}
          onCellClicked={(cell: Item) => {
            const [, row] = cell;
            const r = rows[row];
            if (!r) return;
            if (cell[0] === 5 && r.url) {
              window.open(r.url, "_blank", "noopener");
            } else {
              onRowClick?.(r);
            }
          }}
          theme={theme}
          width={gridW}
          height={gridH}
          rowHeight={34}
          headerHeight={36}
          freezeColumns={0}
          smoothScrollX
          smoothScrollY
          rangeSelect="none"
          columnSelect="none"
          rowSelect="none"
          getCellsForSelection
          overscrollX={200}
        />
      </div>
      {loading && rows.length === 0 && (
        <div className="py-10 text-center text-xs font-mono text-[#9ba1a6] flex items-center justify-center gap-2">
          <Loader2 className="h-3.5 w-3.5 animate-spin text-[#9281f7]" /> Loading signals…
        </div>
      )}
      {!loading && rows.length === 0 && (
        <div className="py-10 text-center text-xs font-mono text-[#9ba1a6]">
          No signals match. Run a research sweep first.
        </div>
      )}
    </div>
  );
}
