"use client";

import React, { useState, useEffect, useRef, useMemo, useCallback, Suspense } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import {
  FileSpreadsheet,
  FileText,
  Download,
  Save,
  RefreshCw,
  Plus,
  Trash2,
  Edit2,
  Check,
  Copy,
  ExternalLink,
  ChevronDown,
  Search,
  Bold,
  Italic,
  Underline,
  Strikethrough,
  AlignLeft,
  AlignCenter,
  AlignRight,
  Sigma,
  DollarSign,
  Percent,
  Table,
  Undo,
  Redo,
  Sparkles,
  Filter,
  Database,
  FolderOpen,
  X,
  FileDown,
  SlidersHorizontal,
  ChevronRight,
  Printer,
  Code
} from "lucide-react";
import {
  listOfficeSources,
  connectOfficeSource,
  getOfficeExportXlsxUrl,
  listOfficeDocuments,
  getOfficeDocument,
  saveOfficeDocument,
  deleteOfficeDocument,
  OfficeSourceItem,
  OfficeSourcesResponse,
  OfficeConnectedData,
  OfficeSavedDocument,
} from "@/lib/api";

// ---------------------------------------------------------------------------
// Type Definitions conforming to Univer SDK Data Models
// ---------------------------------------------------------------------------

export interface UniverCellStyle {
  bold?: boolean;
  italic?: boolean;
  underline?: boolean;
  strike?: boolean;
  color?: string;
  bg?: string;
  align?: "left" | "center" | "right";
  format?: "plain" | "currency" | "percent" | "number";
}

export interface UniverCellData {
  v: string | number;
  s?: UniverCellStyle;
}

export interface UniverWorksheetData {
  id: string;
  name: string;
  rowCount: number;
  columnCount: number;
  cellData: Record<string | number, Record<string | number, UniverCellData>>;
}

export interface UniverWorkbookData {
  id: string;
  name: string;
  sheetOrder: string[];
  sheets: Record<string, UniverWorksheetData>;
}

// ---------------------------------------------------------------------------
// Formula & Range Evaluator Helpers
// ---------------------------------------------------------------------------

function colLetterToIndex(colStr: string): number {
  let index = 0;
  for (let i = 0; i < colStr.length; i++) {
    index = index * 26 + (colStr.charCodeAt(i) - 64);
  }
  return index - 1;
}

function indexToColLetter(index: number): string {
  let letter = "";
  let temp = index;
  while (temp >= 0) {
    letter = String.fromCharCode((temp % 26) + 65) + letter;
    temp = Math.floor(temp / 26) - 1;
  }
  return letter;
}

function parseCellAddress(addr: string): { r: number; c: number } | null {
  const match = addr.trim().toUpperCase().match(/^([A-Z]+)([0-9]+)$/);
  if (!match) return null;
  const col = colLetterToIndex(match[1]);
  const row = parseInt(match[2], 10) - 1;
  return { r: row, c: col };
}

function getCellValue(
  sheet: UniverWorksheetData,
  r: number,
  c: number,
  visited: Set<string> = new Set()
): number | string {
  const cell = sheet.cellData?.[r]?.[c] || sheet.cellData?.[String(r)]?.[String(c)];
  if (!cell || cell.v === undefined || cell.v === null) return "";
  const raw = String(cell.v);
  if (raw.startsWith("=")) {
    const key = `${r}:${c}`;
    if (visited.has(key)) return "#CIRCULAR!";
    visited.add(key);
    return evaluateFormula(raw, sheet, visited);
  }
  const num = Number(raw);
  return isNaN(num) || raw.trim() === "" ? raw : num;
}

function evaluateRange(
  rangeStr: string,
  sheet: UniverWorksheetData,
  visited: Set<string>
): (number | string)[] {
  const [start, end] = rangeStr.split(":").map((s) => s.trim());
  const p1 = parseCellAddress(start);
  const p2 = end ? parseCellAddress(end) : p1;
  if (!p1 || !p2) return [];

  const minR = Math.min(p1.r, p2.r);
  const maxR = Math.max(p1.r, p2.r);
  const minC = Math.min(p1.c, p2.c);
  const maxC = Math.max(p1.c, p2.c);

  const values: (number | string)[] = [];
  for (let r = minR; r <= maxR; r++) {
    for (let c = minC; c <= maxC; c++) {
      values.push(getCellValue(sheet, r, c, new Set(visited)));
    }
  }
  return values;
}

function evaluateFormula(
  formula: string,
  sheet: UniverWorksheetData,
  visited: Set<string>
): number | string {
  const expr = formula.slice(1).trim().toUpperCase();

  const fnMatch = expr.match(/^([A-Z]+)\(([^)]+)\)$/);
  if (fnMatch) {
    const fnName = fnMatch[1];
    const argsStr = fnMatch[2];
    const values = evaluateRange(argsStr, sheet, visited);
    const numValues = values.filter((v): v is number => typeof v === "number" && !isNaN(v));

    switch (fnName) {
      case "SUM":
        return numValues.reduce((a, b) => a + b, 0);
      case "AVERAGE":
      case "AVG":
        return numValues.length > 0
          ? Math.round((numValues.reduce((a, b) => a + b, 0) / numValues.length) * 100) / 100
          : 0;
      case "COUNT":
        return numValues.length;
      case "MAX":
        return numValues.length > 0 ? Math.max(...numValues) : 0;
      case "MIN":
        return numValues.length > 0 ? Math.min(...numValues) : 0;
      default:
        return `#NAME?`;
    }
  }

  // Basic arithmetic evaluation between cell references e.g. =A1+B1
  try {
    const replaced = expr.replace(/[A-Z]+[0-9]+/g, (match) => {
      const p = parseCellAddress(match);
      if (!p) return "0";
      const val = getCellValue(sheet, p.r, p.c, visited);
      return typeof val === "number" ? String(val) : "0";
    });
    // Safe numeric eval
    if (/^[0-9+\-*/().\s]+$/.test(replaced)) {
      // eslint-disable-next-line no-eval
      const res = Function(`"use strict"; return (${replaced});`)();
      return typeof res === "number" ? Math.round(res * 100) / 100 : res;
    }
  } catch (err) {
    return "#VALUE!";
  }

  return formula;
}

// ---------------------------------------------------------------------------
// Default Blank Workbook & Doc Fixtures
// ---------------------------------------------------------------------------

function createInitialWorkbook(): UniverWorkbookData {
  const defaultSheetId = "sheet-1";
  return {
    id: "wb-" + Math.random().toString(36).substring(2, 9),
    name: "Autonomous Office Workbook",
    sheetOrder: [defaultSheetId],
    sheets: {
      [defaultSheetId]: {
        id: defaultSheetId,
        name: "Sheet1",
        rowCount: 30,
        columnCount: 15,
        cellData: {
          0: {
            0: { v: "Metric", s: { bold: true, bg: "#1f2229", color: "#ffffff" } },
            1: { v: "Baseline", s: { bold: true, bg: "#1f2229", color: "#ffffff" } },
            2: { v: "Target", s: { bold: true, bg: "#1f2229", color: "#ffffff" } },
            3: { v: "Growth Delta", s: { bold: true, bg: "#1f2229", color: "#ffffff" } },
          },
          1: {
            0: { v: "Organic Traffic" },
            1: { v: 12500 },
            2: { v: 25000 },
            3: { v: "=C2-B2" },
          },
          2: {
            0: { v: "GEO Citations (AI Search)" },
            1: { v: 140 },
            2: { v: 850 },
            3: { v: "=C3-B3" },
          },
          3: {
            0: { v: "Total Pipeline Impact" },
            1: { v: "=SUM(B2:B3)", s: { bold: true } },
            2: { v: "=SUM(C2:C3)", s: { bold: true } },
            3: { v: "=C4-B4", s: { bold: true, color: "#3ad389" } },
          },
        },
      },
    },
  };
}

const DEFAULT_DOC_MARKDOWN = `# PulseRadar Autonomous Office Intelligence Report
**Generated by Antigravity Autonomous Office Studio**
*Date: ${new Date().toLocaleDateString()} | Author: Autonomous Intelligence Lead*

---

## Executive Summary
This document is live-connected to your **Consumer Discovery**, **SEO & GEO Audits**, and **Browser Sweeps**. All data streams, insight clusters, and algorithmic calculations update here in real time without requiring Microsoft Office or Google Docs subscriptions.

### Strategic Priorities
- [x] Unify consumer discovery signals across Reddit, HackerNews, YouTube, and GitHub.
- [x] Streamline Search Engine Optimization and Generative Engine Optimization (GEO) audits.
- [x] Direct live export to native multi-tab Microsoft Excel (.xlsx) and structured intelligence dossiers.

---

## Real-Time Collaboration & Data Connect
1. Use the **Connect Live Data** button to load any completed Consumer Discovery or SEO audit.
2. Toggle between **Spreadsheet (Sheets)** and **Document (Docs)** mode seamlessly.
3. Apply formulas like \`=SUM(B2:B10)\`, \`=AVERAGE(C2:C10)\`, and format cells with custom colors.
4. Click **Export Excel (.xlsx)** to download ready-to-share executive workbooks.
`;

// ---------------------------------------------------------------------------
// Main Office Studio Component
// ---------------------------------------------------------------------------

function OfficeStudioContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  // Mode: sheets vs docs
  const [docType, setDocType] = useState<"sheets" | "docs">("sheets");

  // Document metadata
  const [docId, setDocId] = useState<string | null>(null);
  const [docTitle, setDocTitle] = useState<string>("Autonomous Office Intelligence");
  const [isEditingTitle, setIsEditingTitle] = useState(false);

  // Connected source metadata
  const [sourceType, setSourceType] = useState<"research" | "seo" | null>(null);
  const [sourceId, setSourceId] = useState<string | null>(null);
  const [sourceSummary, setSourceSummary] = useState<string>("");

  // Workbook state
  const [workbook, setWorkbook] = useState<UniverWorkbookData>(createInitialWorkbook);
  const [activeSheetId, setActiveSheetId] = useState<string>("sheet-1");

  // Document state (Markdown/WYSIWYG)
  const [docMarkdown, setDocMarkdown] = useState<string>(DEFAULT_DOC_MARKDOWN);

  // Selection & cell editing state
  const [selectedCell, setSelectedCell] = useState<{ r: number; c: number }>({ r: 0, c: 0 });
  const [editingCell, setEditingCell] = useState<{ r: number; c: number } | null>(null);
  const [editInputVal, setEditInputVal] = useState<string>("");
  const [formulaInputVal, setFormulaInputVal] = useState<string>("");

  // History for Undo/Redo
  const [history, setHistory] = useState<UniverWorkbookData[]>([]);
  const [historyIndex, setHistoryIndex] = useState<number>(-1);

  // UI state
  const [isSaving, setIsSaving] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [sourcesDrawerOpen, setSourcesDrawerOpen] = useState(false);
  const [savedDocsDrawerOpen, setSavedDocsDrawerOpen] = useState(false);
  const [exportDropdownOpen, setExportDropdownOpen] = useState(false);
  const [autoSumDropdownOpen, setAutoSumDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  // Sources & Saved documents lists
  const [sourcesList, setSourcesList] = useState<OfficeSourcesResponse>({ research: [], seo: [] });
  const [savedDocsList, setSavedDocsList] = useState<OfficeSavedDocument[]>([]);
  const [isLoadingSources, setIsLoadingSources] = useState(false);

  const cellInputRef = useRef<HTMLInputElement>(null);
  const formulaBarRef = useRef<HTMLInputElement>(null);

  // Toast notifier
  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  // Active worksheet helper
  const activeSheet = useMemo(() => {
    return workbook.sheets[activeSheetId] || Object.values(workbook.sheets)[0];
  }, [workbook, activeSheetId]);

  // Push state to undo history
  const pushHistory = useCallback(
    (newWorkbook: UniverWorkbookData) => {
      setHistory((prev) => {
        const sliced = prev.slice(0, historyIndex + 1);
        return [...sliced, JSON.parse(JSON.stringify(newWorkbook))].slice(-25);
      });
      setHistoryIndex((prev) => Math.min(prev + 1, 24));
    },
    [historyIndex]
  );

  const handleUndo = () => {
    if (historyIndex > 0) {
      const prevIndex = historyIndex - 1;
      setWorkbook(JSON.parse(JSON.stringify(history[prevIndex])));
      setHistoryIndex(prevIndex);
    }
  };

  const handleRedo = () => {
    if (historyIndex < history.length - 1) {
      const nextIndex = historyIndex + 1;
      setWorkbook(JSON.parse(JSON.stringify(history[nextIndex])));
      setHistoryIndex(nextIndex);
    }
  };

  // ---------------------------------------------------------------------------
  // Load initial source from query parameters
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const qSource = searchParams?.get("source");
    const qId = searchParams?.get("id");
    const qDoc = searchParams?.get("doc");

    if (qDoc) {
      loadSavedDocumentById(qDoc);
    } else if ((qSource === "research" || qSource === "seo") && qId) {
      handleConnectSource(qSource, qId);
    } else {
      // Initialize history with initial fixture
      setHistory([createInitialWorkbook()]);
      setHistoryIndex(0);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Sync formula bar value with selected cell
  useEffect(() => {
    if (!activeSheet) return;
    const cell =
      activeSheet.cellData?.[selectedCell.r]?.[selectedCell.c] ||
      activeSheet.cellData?.[String(selectedCell.r)]?.[String(selectedCell.c)];
    const val = cell?.v !== undefined && cell?.v !== null ? String(cell.v) : "";
    setFormulaInputVal(val);
  }, [selectedCell, activeSheet]);

  // Focus input when editing cell
  useEffect(() => {
    if (editingCell && cellInputRef.current) {
      cellInputRef.current.focus();
    }
  }, [editingCell]);

  // ---------------------------------------------------------------------------
  // Data Bridge Connection & Sync
  // ---------------------------------------------------------------------------

  const handleConnectSource = async (type: "research" | "seo", id: string) => {
    try {
      setIsSyncing(true);
      const data = await connectOfficeSource(type, id);

      setSourceType(type);
      setSourceId(id);
      setDocTitle(data.title || `${type.toUpperCase()} Live Intelligence`);
      setSourceSummary(data.summary || "");

      if (data.workbook && data.workbook.sheets) {
        setWorkbook(data.workbook);
        const firstSheetId = data.workbook.sheetOrder?.[0] || Object.keys(data.workbook.sheets)[0];
        setActiveSheetId(firstSheetId);
        setHistory([data.workbook]);
        setHistoryIndex(0);
      }

      if (data.document?.markdown) {
        setDocMarkdown(data.document.markdown);
      }

      showToast(`Connected live data from ${type === "research" ? "Consumer Discovery" : "SEO Audit"}!`);
      setSourcesDrawerOpen(false);
    } catch (err: any) {
      console.error("Connection error:", err);
      showToast(`Failed to connect source: ${err.message || err}`);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleRefreshSync = async () => {
    if (!sourceType || !sourceId) {
      showToast("No live source currently attached. Connect one from the Sources panel.");
      return;
    }
    await handleConnectSource(sourceType, sourceId);
  };

  const openSourcesDrawer = async () => {
    setIsLoadingSources(true);
    setSourcesDrawerOpen(true);
    try {
      const res = await listOfficeSources();
      setSourcesList(res);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoadingSources(false);
    }
  };

  const openSavedDocsDrawer = async () => {
    setSavedDocsDrawerOpen(true);
    try {
      const list = await listOfficeDocuments();
      setSavedDocsList(list);
    } catch (e) {
      console.error(e);
    }
  };

  const loadSavedDocumentById = async (id: string) => {
    try {
      setIsSyncing(true);
      const doc = await getOfficeDocument(id);
      setDocId(doc.id);
      setDocTitle(doc.title);
      setDocType(doc.doc_type);
      if (doc.source_type && doc.source_id) {
        setSourceType(doc.source_type as "research" | "seo");
        setSourceId(doc.source_id);
      }
      if (doc.snapshot) {
        if (doc.doc_type === "sheets") {
          setWorkbook(doc.snapshot);
          const firstSheetId = doc.snapshot.sheetOrder?.[0] || Object.keys(doc.snapshot.sheets)[0];
          setActiveSheetId(firstSheetId);
          setHistory([doc.snapshot]);
          setHistoryIndex(0);
        } else if (typeof doc.snapshot === "string") {
          setDocMarkdown(doc.snapshot);
        }
      }
      setSavedDocsDrawerOpen(false);
      showToast(`Opened document "${doc.title}"`);
    } catch (err: any) {
      console.error("Load doc error:", err);
      showToast(`Error opening document: ${err.message || err}`);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleSaveDocument = async () => {
    try {
      setIsSaving(true);
      const snapshot = docType === "sheets" ? workbook : docMarkdown;
      const res = await saveOfficeDocument({
        id: docId || undefined,
        title: docTitle,
        doc_type: docType,
        source_type: sourceType || undefined,
        source_id: sourceId || undefined,
        snapshot: snapshot,
        summary: sourceSummary || `Office Studio ${docType} intelligence document`,
      });
      setDocId(res.id);
      showToast("Document saved securely to storage!");
    } catch (err: any) {
      console.error("Save error:", err);
      showToast(`Failed to save: ${err.message || err}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteSavedDoc = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this document?")) return;
    try {
      await deleteOfficeDocument(id);
      setSavedDocsList((prev) => prev.filter((d) => d.id !== id));
      if (docId === id) setDocId(null);
      showToast("Document deleted.");
    } catch (err: any) {
      showToast("Failed to delete document.");
    }
  };

  // ---------------------------------------------------------------------------
  // Spreadsheet Editing & Formulas
  // ---------------------------------------------------------------------------

  const updateCellValue = (r: number, c: number, rawVal: string | number) => {
    setWorkbook((prev) => {
      const next = JSON.parse(JSON.stringify(prev)) as UniverWorkbookData;
      const currentSheet = next.sheets[activeSheetId];
      if (!currentSheet) return prev;

      if (!currentSheet.cellData) currentSheet.cellData = {};
      if (!currentSheet.cellData[r]) currentSheet.cellData[r] = {};

      const existingCell = currentSheet.cellData[r][c] || {};
      const trimmed = typeof rawVal === "string" ? rawVal.trim() : rawVal;

      if (trimmed === "") {
        delete currentSheet.cellData[r][c];
      } else {
        const isNum = typeof rawVal === "number" || (!isNaN(Number(rawVal)) && !String(rawVal).startsWith("="));
        currentSheet.cellData[r][c] = {
          ...existingCell,
          v: isNum ? Number(rawVal) : rawVal,
        };
      }

      pushHistory(next);
      return next;
    });
  };

  const applyCellStyle = (styleUpdate: Partial<UniverCellStyle>) => {
    setWorkbook((prev) => {
      const next = JSON.parse(JSON.stringify(prev)) as UniverWorkbookData;
      const currentSheet = next.sheets[activeSheetId];
      if (!currentSheet) return prev;

      const { r, c } = selectedCell;
      if (!currentSheet.cellData) currentSheet.cellData = {};
      if (!currentSheet.cellData[r]) currentSheet.cellData[r] = {};

      const currentCell = currentSheet.cellData[r][c] || { v: "" };
      currentCell.s = {
        ...(currentCell.s || {}),
        ...styleUpdate,
      };
      currentSheet.cellData[r][c] = currentCell;

      pushHistory(next);
      return next;
    });
  };

  const handleCellClick = (r: number, c: number) => {
    if (editingCell && (editingCell.r !== r || editingCell.c !== c)) {
      commitEdit();
    }
    setSelectedCell({ r, c });
  };

  const handleCellDoubleClick = (r: number, c: number) => {
    setSelectedCell({ r, c });
    const cell =
      activeSheet?.cellData?.[r]?.[c] || activeSheet?.cellData?.[String(r)]?.[String(c)];
    const rawVal = cell?.v !== undefined && cell?.v !== null ? String(cell.v) : "";
    setEditInputVal(rawVal);
    setEditingCell({ r, c });
  };

  const commitEdit = () => {
    if (!editingCell) return;
    updateCellValue(editingCell.r, editingCell.c, editInputVal);
    setEditingCell(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (editingCell) {
      if (e.key === "Enter") {
        e.preventDefault();
        commitEdit();
        if (selectedCell.r < (activeSheet?.rowCount || 30) - 1) {
          setSelectedCell((p) => ({ ...p, r: p.r + 1 }));
        }
      } else if (e.key === "Escape") {
        setEditingCell(null);
      }
      return;
    }

    // Grid Navigation
    if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedCell((p) => ({ ...p, r: Math.max(0, p.r - 1) }));
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedCell((p) => ({ ...p, r: Math.min((activeSheet?.rowCount || 30) - 1, p.r + 1) }));
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      setSelectedCell((p) => ({ ...p, c: Math.max(0, p.c - 1) }));
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      setSelectedCell((p) => ({ ...p, c: Math.min((activeSheet?.columnCount || 15) - 1, p.c + 1) }));
    } else if (e.key === "Enter") {
      e.preventDefault();
      handleCellDoubleClick(selectedCell.r, selectedCell.c);
    } else if (e.key === "Delete" || e.key === "Backspace") {
      e.preventDefault();
      updateCellValue(selectedCell.r, selectedCell.c, "");
    }
  };

  const insertAutoSumFormula = (fnName: "SUM" | "AVERAGE" | "COUNT" | "MAX" | "MIN") => {
    const { r, c } = selectedCell;
    const colLetter = indexToColLetter(c);
    const startRow = Math.max(1, r);
    const formulaStr = `=${fnName}(${colLetter}1:${colLetter}${startRow})`;
    updateCellValue(r, c, formulaStr);
    setAutoSumDropdownOpen(false);
  };

  // Row / Col manipulation
  const insertRow = (offset: 0 | 1) => {
    setWorkbook((prev) => {
      const next = JSON.parse(JSON.stringify(prev)) as UniverWorkbookData;
      const sheet = next.sheets[activeSheetId];
      if (!sheet) return prev;
      sheet.rowCount = (sheet.rowCount || 30) + 1;
      pushHistory(next);
      return next;
    });
  };

  const insertCol = () => {
    setWorkbook((prev) => {
      const next = JSON.parse(JSON.stringify(prev)) as UniverWorkbookData;
      const sheet = next.sheets[activeSheetId];
      if (!sheet) return prev;
      sheet.columnCount = (sheet.columnCount || 15) + 1;
      pushHistory(next);
      return next;
    });
  };

  const addSheetTab = () => {
    const newSheetId = "sheet-" + (workbook.sheetOrder.length + 1);
    const newSheetName = `Sheet${workbook.sheetOrder.length + 1}`;
    setWorkbook((prev) => {
      const next = {
        ...prev,
        sheetOrder: [...prev.sheetOrder, newSheetId],
        sheets: {
          ...prev.sheets,
          [newSheetId]: {
            id: newSheetId,
            name: newSheetName,
            rowCount: 30,
            columnCount: 15,
            cellData: {},
          },
        },
      };
      pushHistory(next);
      return next;
    });
    setActiveSheetId(newSheetId);
  };

  // ---------------------------------------------------------------------------
  // Export Handlers
  // ---------------------------------------------------------------------------

  const handleExportXlsx = () => {
    if (sourceType && sourceId) {
      window.open(getOfficeExportXlsxUrl(sourceType, sourceId), "_blank");
    } else {
      // Export current sheet as CSV fallback
      handleExportCsv();
    }
  };

  const handleExportCsv = () => {
    if (!activeSheet) return;
    const rows: string[] = [];
    const maxR = activeSheet.rowCount || 30;
    const maxC = activeSheet.columnCount || 15;

    for (let r = 0; r < maxR; r++) {
      const rowVals: string[] = [];
      let hasData = false;
      for (let c = 0; c < maxC; c++) {
        const val = getCellValue(activeSheet, r, c);
        const strVal = String(val || "").replace(/"/g, '""');
        rowVals.push(`"${strVal}"`);
        if (val !== "") hasData = true;
      }
      if (hasData || r < 10) {
        rows.push(rowVals.join(","));
      }
    }

    const csvContent = rows.join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${docTitle.replace(/[^a-z0-9_-]/gi, "_")}_${activeSheet.name}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("Downloaded CSV spreadsheet!");
  };

  const handleExportJson = () => {
    const dataStr = JSON.stringify(workbook, null, 2);
    const blob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${docTitle.replace(/[^a-z0-9_-]/gi, "_")}_workbook.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("Downloaded Univer workbook JSON!");
  };

  const handleExportMarkdownDoc = () => {
    const blob = new Blob([docMarkdown], { type: "text/markdown;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${docTitle.replace(/[^a-z0-9_-]/gi, "_")}_document.md`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("Downloaded Markdown document!");
  };

  // Selected cell styling queries
  const activeCellData = activeSheet?.cellData?.[selectedCell.r]?.[selectedCell.c] ||
    activeSheet?.cellData?.[String(selectedCell.r)]?.[String(selectedCell.c)];
  const isBold = !!activeCellData?.s?.bold;
  const isItalic = !!activeCellData?.s?.italic;
  const isUnderline = !!activeCellData?.s?.underline;
  const currentAlign = activeCellData?.s?.align || "left";

  const totalSheetsCount = workbook.sheetOrder?.length || 1;

  return (
    <div
      className="flex flex-col h-full w-full bg-[#0c0d10] text-[#f0f0f0] select-none"
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      {/* -------------------------------------------------------------------- */}
      {/* TOP APPLICATION BAR */}
      {/* -------------------------------------------------------------------- */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-[#292d30] bg-[#121418] shrink-0">
        {/* Left: Document Title, Mode Switcher & Source Badge */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-[6px] bg-[#9281f7]/20 border border-[#9281f7]/40 flex items-center justify-center text-[#9281f7]">
              {docType === "sheets" ? (
                <FileSpreadsheet className="h-4 w-4" />
              ) : (
                <FileText className="h-4 w-4" />
              )}
            </div>
            {isEditingTitle ? (
              <input
                type="text"
                value={docTitle}
                onChange={(e) => setDocTitle(e.target.value)}
                onBlur={() => setIsEditingTitle(false)}
                onKeyDown={(e) => e.key === "Enter" && setIsEditingTitle(false)}
                autoFocus
                className="bg-[#1f2229] border border-[#9281f7] text-sm text-[#ffffff] px-2 py-0.5 rounded-[4px] outline-none font-sans font-medium"
              />
            ) : (
              <span
                onClick={() => setIsEditingTitle(true)}
                className="text-sm font-medium text-[#ffffff] hover:text-[#9281f7] cursor-pointer flex items-center gap-1.5 px-1 py-0.5 rounded hover:bg-[#1f2229] transition-colors"
                title="Click to rename document"
              >
                {docTitle}
                <Edit2 className="h-3 w-3 text-[#a1a4a5] opacity-60" />
              </span>
            )}
          </div>

          <div className="h-4 w-[1px] bg-[#292d30]" />

          {/* Mode Switcher Tabs */}
          <div className="flex items-center bg-[#181a20] p-0.5 rounded-[6px] border border-[#292d30]">
            <button
              onClick={() => setDocType("sheets")}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-[4px] text-xs font-mono font-medium transition-all ${
                docType === "sheets"
                  ? "bg-[#9281f7]/20 text-[#ffffff] border border-[#9281f7]/50"
                  : "text-[#a1a4a5] hover:text-[#ffffff]"
              }`}
            >
              <FileSpreadsheet className="h-3.5 w-3.5 text-[#9281f7]" />
              <span>Sheets (Excel)</span>
            </button>
            <button
              onClick={() => setDocType("docs")}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-[4px] text-xs font-mono font-medium transition-all ${
                docType === "docs"
                  ? "bg-[#9281f7]/20 text-[#ffffff] border border-[#9281f7]/50"
                  : "text-[#a1a4a5] hover:text-[#ffffff]"
              }`}
            >
              <FileText className="h-3.5 w-3.5 text-[#9281f7]" />
              <span>Docs (Word)</span>
            </button>
          </div>

          {/* Connected Data Indicator */}
          {sourceType && sourceId && (
            <div className="hidden lg:flex items-center gap-2 px-2.5 py-0.5 rounded-[6px] bg-[#181a20] border border-[#292d30] text-[11px] font-mono">
              <span className="h-2 w-2 rounded-full bg-[#3ad389] animate-pulse" />
              <span className="text-[#a1a4a5]">LIVE:</span>
              <span className="text-[#9281f7] uppercase font-medium">{sourceType}</span>
              <span className="text-[#6e727a]">#{sourceId.slice(0, 8)}</span>
              <button
                onClick={handleRefreshSync}
                disabled={isSyncing}
                title="Refresh live data synchronization"
                className="hover:text-[#ffffff] text-[#a1a4a5] ml-1"
              >
                <RefreshCw className={`h-3 w-3 ${isSyncing ? "animate-spin" : ""}`} />
              </button>
            </div>
          )}
        </div>

        {/* Right Action Buttons */}
        <div className="flex items-center gap-2">
          {/* Saved Documents */}
          <button
            onClick={openSavedDocsDrawer}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-[6px] bg-[#181a20] border border-[#292d30] hover:border-[#ffffff] text-xs text-[#a1a4a5] hover:text-[#ffffff] transition-all"
            title="Browse saved office files"
          >
            <FolderOpen className="h-3.5 w-3.5 text-[#9281f7]" />
            <span className="hidden sm:inline">Files</span>
          </button>

          {/* Connect Live Source Drawer */}
          <button
            onClick={openSourcesDrawer}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] bg-[#181a20] border border-[#9281f7]/40 hover:border-[#9281f7] text-xs font-medium text-[#ffffff] transition-all"
            title="Connect Consumer Discovery or SEO audit data in real time"
          >
            <Database className="h-3.5 w-3.5 text-[#9281f7]" />
            <span>Connect Data</span>
          </button>

          {/* Save Document */}
          <button
            onClick={handleSaveDocument}
            disabled={isSaving}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] bg-[#9281f7] hover:bg-[#8370f2] text-xs font-sans font-medium text-[#000000] transition-all shadow-subtle"
          >
            <Save className={`h-3.5 w-3.5 ${isSaving ? "animate-spin" : ""}`} />
            <span>{isSaving ? "Saving..." : "Save"}</span>
          </button>

          {/* Export Dropdown */}
          <div className="relative">
            <button
              onClick={() => setExportDropdownOpen(!exportDropdownOpen)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] bg-[#181a20] border border-[#292d30] hover:border-[#ffffff] text-xs font-sans font-medium text-[#ffffff] transition-all"
            >
              <Download className="h-3.5 w-3.5 text-[#3ad389]" />
              <span>Export</span>
              <ChevronDown className="h-3 w-3 text-[#a1a4a5]" />
            </button>

            {exportDropdownOpen && (
              <div
                className="absolute right-0 mt-1 w-56 bg-[#181a20] border border-[#292d30] rounded-[8px] p-1.5 shadow-2xl z-50 flex flex-col gap-1 text-xs"
                onClick={() => setExportDropdownOpen(false)}
              >
                <button
                  onClick={handleExportXlsx}
                  className="flex items-center gap-2 px-3 py-2 rounded-[6px] text-left hover:bg-[#1f2229] text-[#ffffff] transition-colors"
                >
                  <FileSpreadsheet className="h-4 w-4 text-[#3ad389]" />
                  <div>
                    <div className="font-medium">Excel (.xlsx)</div>
                    <div className="text-[10px] text-[#a1a4a5]">Native multi-tab styled workbook</div>
                  </div>
                </button>

                <button
                  onClick={handleExportCsv}
                  className="flex items-center gap-2 px-3 py-2 rounded-[6px] text-left hover:bg-[#1f2229] text-[#ffffff] transition-colors"
                >
                  <Table className="h-4 w-4 text-[#a1a4a5]" />
                  <div>
                    <div className="font-medium">CSV (.csv)</div>
                    <div className="text-[10px] text-[#a1a4a5]">Current active sheet raw data</div>
                  </div>
                </button>

                <button
                  onClick={handleExportMarkdownDoc}
                  className="flex items-center gap-2 px-3 py-2 rounded-[6px] text-left hover:bg-[#1f2229] text-[#ffffff] transition-colors"
                >
                  <FileText className="h-4 w-4 text-[#9281f7]" />
                  <div>
                    <div className="font-medium">Dossier (.md)</div>
                    <div className="text-[10px] text-[#a1a4a5]">Markdown intelligence report</div>
                  </div>
                </button>

                <button
                  onClick={handleExportJson}
                  className="flex items-center gap-2 px-3 py-2 rounded-[6px] text-left hover:bg-[#1f2229] text-[#ffffff] transition-colors"
                >
                  <Code className="h-4 w-4 text-[#ffca16]" />
                  <div>
                    <div className="font-medium">Univer JSON</div>
                    <div className="text-[10px] text-[#a1a4a5]">Complete workbook state snapshot</div>
                  </div>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* -------------------------------------------------------------------- */}
      {/* SPREADSHEETS (SHEETS) MODE */}
      {/* -------------------------------------------------------------------- */}
      {docType === "sheets" && (
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Ribbon Toolbar */}
          <div className="flex items-center gap-1 px-4 py-1.5 border-b border-[#292d30] bg-[#16181d] text-xs overflow-x-auto shrink-0 scrollbar-none">
            {/* Undo / Redo */}
            <div className="flex items-center gap-0.5 pr-2 border-r border-[#292d30]">
              <button
                onClick={handleUndo}
                disabled={historyIndex <= 0}
                className="p-1.5 rounded hover:bg-[#252830] text-[#a1a4a5] hover:text-[#ffffff] disabled:opacity-30"
                title="Undo (Ctrl+Z)"
              >
                <Undo className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={handleRedo}
                disabled={historyIndex >= history.length - 1}
                className="p-1.5 rounded hover:bg-[#252830] text-[#a1a4a5] hover:text-[#ffffff] disabled:opacity-30"
                title="Redo (Ctrl+Y)"
              >
                <Redo className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* Font Styling */}
            <div className="flex items-center gap-0.5 px-2 border-r border-[#292d30]">
              <button
                onClick={() => applyCellStyle({ bold: !isBold })}
                className={`p-1.5 rounded transition-colors ${
                  isBold ? "bg-[#9281f7]/30 text-[#ffffff]" : "hover:bg-[#252830] text-[#a1a4a5] hover:text-[#ffffff]"
                }`}
                title="Bold (Ctrl+B)"
              >
                <Bold className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => applyCellStyle({ italic: !isItalic })}
                className={`p-1.5 rounded transition-colors ${
                  isItalic ? "bg-[#9281f7]/30 text-[#ffffff]" : "hover:bg-[#252830] text-[#a1a4a5] hover:text-[#ffffff]"
                }`}
                title="Italic (Ctrl+I)"
              >
                <Italic className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => applyCellStyle({ underline: !isUnderline })}
                className={`p-1.5 rounded transition-colors ${
                  isUnderline ? "bg-[#9281f7]/30 text-[#ffffff]" : "hover:bg-[#252830] text-[#a1a4a5] hover:text-[#ffffff]"
                }`}
                title="Underline (Ctrl+U)"
              >
                <Underline className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* Cell Background & Text Color Quick Presets */}
            <div className="flex items-center gap-1 px-2 border-r border-[#292d30]">
              <div className="flex items-center gap-1" title="Fill Color">
                <span className="text-[10px] text-[#6e727a] font-mono">BG:</span>
                {["transparent", "#1f2229", "#1e3a2f", "#3b1e28", "#2a244d"].map((color) => (
                  <button
                    key={color}
                    onClick={() => applyCellStyle({ bg: color === "transparent" ? undefined : color })}
                    style={{ backgroundColor: color === "transparent" ? "#121418" : color }}
                    className="h-4 w-4 rounded border border-[#3e424d] hover:scale-110 transition-transform"
                  />
                ))}
              </div>
              <div className="h-3 w-[1px] bg-[#292d30] mx-1" />
              <div className="flex items-center gap-1" title="Text Color">
                <span className="text-[10px] text-[#6e727a] font-mono">TXT:</span>
                {["#ffffff", "#3ad389", "#ffca16", "#ff9592", "#9281f7"].map((color) => (
                  <button
                    key={color}
                    onClick={() => applyCellStyle({ color })}
                    style={{ backgroundColor: color }}
                    className="h-4 w-4 rounded border border-[#3e424d] hover:scale-110 transition-transform"
                  />
                ))}
              </div>
            </div>

            {/* Alignment */}
            <div className="flex items-center gap-0.5 px-2 border-r border-[#292d30]">
              <button
                onClick={() => applyCellStyle({ align: "left" })}
                className={`p-1.5 rounded ${
                  currentAlign === "left" ? "bg-[#9281f7]/30 text-[#ffffff]" : "hover:bg-[#252830] text-[#a1a4a5]"
                }`}
                title="Align Left"
              >
                <AlignLeft className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => applyCellStyle({ align: "center" })}
                className={`p-1.5 rounded ${
                  currentAlign === "center" ? "bg-[#9281f7]/30 text-[#ffffff]" : "hover:bg-[#252830] text-[#a1a4a5]"
                }`}
                title="Align Center"
              >
                <AlignCenter className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => applyCellStyle({ align: "right" })}
                className={`p-1.5 rounded ${
                  currentAlign === "right" ? "bg-[#9281f7]/30 text-[#ffffff]" : "hover:bg-[#252830] text-[#a1a4a5]"
                }`}
                title="Align Right"
              >
                <AlignRight className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* AutoSum & Formulas Dropdown */}
            <div className="relative px-2 border-r border-[#292d30]">
              <button
                onClick={() => setAutoSumDropdownOpen(!autoSumDropdownOpen)}
                className="flex items-center gap-1 px-2 py-1 rounded bg-[#1f2229] hover:bg-[#292d37] text-xs font-mono text-[#ffffff]"
                title="Insert Formula"
              >
                <Sigma className="h-3.5 w-3.5 text-[#9281f7]" />
                <span>AutoSum</span>
                <ChevronDown className="h-3 w-3 text-[#a1a4a5]" />
              </button>

              {autoSumDropdownOpen && (
                <div
                  className="absolute left-2 mt-1 w-36 bg-[#181a20] border border-[#292d30] rounded-[6px] p-1 shadow-2xl z-50 flex flex-col gap-0.5 text-xs font-mono"
                  onClick={() => setAutoSumDropdownOpen(false)}
                >
                  <button
                    onClick={() => insertAutoSumFormula("SUM")}
                    className="flex items-center justify-between px-2.5 py-1.5 rounded hover:bg-[#1f2229] text-left text-[#ffffff]"
                  >
                    <span>SUM</span>
                    <span className="text-[10px] text-[#a1a4a5]">=SUM(A:B)</span>
                  </button>
                  <button
                    onClick={() => insertAutoSumFormula("AVERAGE")}
                    className="flex items-center justify-between px-2.5 py-1.5 rounded hover:bg-[#1f2229] text-left text-[#ffffff]"
                  >
                    <span>AVERAGE</span>
                    <span className="text-[10px] text-[#a1a4a5]">=AVG(..)</span>
                  </button>
                  <button
                    onClick={() => insertAutoSumFormula("COUNT")}
                    className="flex items-center justify-between px-2.5 py-1.5 rounded hover:bg-[#1f2229] text-left text-[#ffffff]"
                  >
                    <span>COUNT</span>
                    <span className="text-[10px] text-[#a1a4a5]">=COUNT(..)</span>
                  </button>
                  <button
                    onClick={() => insertAutoSumFormula("MAX")}
                    className="flex items-center justify-between px-2.5 py-1.5 rounded hover:bg-[#1f2229] text-left text-[#ffffff]"
                  >
                    <span>MAX</span>
                    <span className="text-[10px] text-[#a1a4a5]">=MAX(..)</span>
                  </button>
                  <button
                    onClick={() => insertAutoSumFormula("MIN")}
                    className="flex items-center justify-between px-2.5 py-1.5 rounded hover:bg-[#1f2229] text-left text-[#ffffff]"
                  >
                    <span>MIN</span>
                    <span className="text-[10px] text-[#a1a4a5]">=MIN(..)</span>
                  </button>
                </div>
              )}
            </div>

            {/* Grid Row / Col Controls */}
            <div className="flex items-center gap-1 px-2 border-r border-[#292d30]">
              <button
                onClick={() => insertRow(1)}
                className="flex items-center gap-1 px-2 py-1 rounded bg-[#181a20] hover:bg-[#252830] text-[#a1a4a5] hover:text-[#ffffff] text-[11px] font-mono"
                title="Add 1 Row Below"
              >
                <Plus className="h-3 w-3 text-[#3ad389]" />
                <span>Row</span>
              </button>
              <button
                onClick={insertCol}
                className="flex items-center gap-1 px-2 py-1 rounded bg-[#181a20] hover:bg-[#252830] text-[#a1a4a5] hover:text-[#ffffff] text-[11px] font-mono"
                title="Add 1 Column Right"
              >
                <Plus className="h-3 w-3 text-[#3ad389]" />
                <span>Col</span>
              </button>
            </div>

            {/* Search within sheet */}
            <div className="flex items-center gap-1 pl-2">
              <div className="relative">
                <Search className="h-3 w-3 text-[#6e727a] absolute left-2 top-2" />
                <input
                  type="text"
                  placeholder="Find in sheet..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="bg-[#121418] border border-[#292d30] rounded-[4px] pl-6 pr-2 py-1 text-[11px] text-[#ffffff] placeholder-[#6e727a] outline-none focus:border-[#9281f7] w-32"
                />
              </div>
            </div>
          </div>

          {/* Formula Bar */}
          <div className="flex items-center gap-2 px-4 py-1.5 border-b border-[#292d30] bg-[#121418] shrink-0 font-mono text-xs">
            {/* Cell Address Badge */}
            <div className="w-16 px-2 py-0.5 rounded bg-[#1f2229] border border-[#292d30] text-center font-bold text-[#9281f7]">
              {indexToColLetter(selectedCell.c)}
              {selectedCell.r + 1}
            </div>

            {/* Formula Function Glyph */}
            <span className="text-[#a1a4a5] font-serif italic text-sm">fx</span>

            {/* Formula Input */}
            <input
              ref={formulaBarRef}
              type="text"
              value={formulaInputVal}
              onChange={(e) => {
                setFormulaInputVal(e.target.value);
                updateCellValue(selectedCell.r, selectedCell.c, e.target.value);
              }}
              placeholder="Enter value or formula like =SUM(A1:B5)"
              className="flex-1 bg-[#181a20] border border-[#292d30] focus:border-[#9281f7] px-3 py-1 rounded text-[#ffffff] outline-none"
            />
          </div>

          {/* High-Performance Spreadsheet Grid Viewport */}
          <div className="flex-1 overflow-auto bg-[#0a0b0d] relative focus:outline-none">
            {activeSheet && (
              <table className="border-collapse table-fixed select-text">
                <thead className="sticky top-0 z-20 bg-[#16181d] shadow-sm">
                  <tr>
                    {/* Top-left corner cell */}
                    <th className="w-12 h-7 border-b border-r border-[#292d30] bg-[#181a20] text-[10px] text-[#6e727a] font-mono text-center sticky left-0 z-30">
                      #
                    </th>
                    {/* Column Headers A, B, C... */}
                    {Array.from({ length: activeSheet.columnCount || 15 }).map((_, c) => (
                      <th
                        key={c}
                        className="w-36 h-7 border-b border-r border-[#292d30] bg-[#16181d] text-xs font-mono text-[#a1a4a5] font-normal text-center"
                      >
                        {indexToColLetter(c)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {Array.from({ length: activeSheet.rowCount || 30 }).map((_, r) => (
                    <tr key={r}>
                      {/* Row Header 1, 2, 3... */}
                      <td className="w-12 h-7 border-b border-r border-[#292d30] bg-[#181a20] text-[11px] font-mono text-[#6e727a] text-center sticky left-0 z-10 select-none">
                        {r + 1}
                      </td>

                      {/* Cells */}
                      {Array.from({ length: activeSheet.columnCount || 15 }).map((_, c) => {
                        const cell =
                          activeSheet.cellData?.[r]?.[c] ||
                          activeSheet.cellData?.[String(r)]?.[String(c)];
                        const isSelected = selectedCell.r === r && selectedCell.c === c;
                        const isEditing = editingCell?.r === r && editingCell?.c === c;

                        // Evaluated display value
                        const evaluatedVal = getCellValue(activeSheet, r, c);
                        const displayStr =
                          evaluatedVal !== undefined && evaluatedVal !== null
                            ? String(evaluatedVal)
                            : "";

                        // Highlight if matches search
                        const matchesSearch =
                          searchQuery.trim() !== "" &&
                          displayStr.toLowerCase().includes(searchQuery.toLowerCase());

                        // Style properties
                        const s = cell?.s || {};
                        const cellStyle: React.CSSProperties = {
                          fontWeight: s.bold ? "bold" : "normal",
                          fontStyle: s.italic ? "italic" : "normal",
                          textDecoration: s.underline ? "underline" : "none",
                          color: s.color || "#ffffff",
                          backgroundColor: matchesSearch
                            ? "#ffca16"
                            : isSelected
                            ? "rgba(146, 129, 247, 0.12)"
                            : s.bg || "transparent",
                          textAlign: s.align || "left",
                        };

                        return (
                          <td
                            key={c}
                            onClick={() => handleCellClick(r, c)}
                            onDoubleClick={() => handleCellDoubleClick(r, c)}
                            style={cellStyle}
                            className={`h-7 px-2 border-b border-r border-[#20232a] text-xs font-mono truncate transition-colors relative cursor-cell ${
                              isSelected
                                ? "outline outline-2 outline-[#9281f7] -outline-offset-1 z-10"
                                : "hover:bg-[#1f2229]/40"
                            }`}
                          >
                            {isEditing ? (
                              <input
                                ref={cellInputRef}
                                type="text"
                                value={editInputVal}
                                onChange={(e) => setEditInputVal(e.target.value)}
                                onBlur={commitEdit}
                                className="absolute inset-0 w-full h-full bg-[#121418] text-[#ffffff] px-2 text-xs font-mono outline-none border border-[#9281f7]"
                              />
                            ) : (
                              displayStr
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* Bottom Worksheet Tabs Bar (Like Univer / Excel) */}
          <div className="flex items-center justify-between px-3 py-1.5 border-t border-[#292d30] bg-[#121418] shrink-0 text-xs font-mono">
            {/* Sheet Tabs */}
            <div className="flex items-center gap-1 overflow-x-auto scrollbar-none">
              {workbook.sheetOrder.map((sId) => {
                const sheet = workbook.sheets[sId];
                if (!sheet) return null;
                const isActive = activeSheetId === sId;
                return (
                  <button
                    key={sId}
                    onClick={() => setActiveSheetId(sId)}
                    className={`flex items-center gap-1.5 px-3 py-1 rounded-[4px] border transition-all text-xs ${
                      isActive
                        ? "bg-[#1f2229] border-[#9281f7] text-[#ffffff] font-medium shadow-sm"
                        : "bg-[#16181d] border-[#292d30] text-[#a1a4a5] hover:text-[#ffffff]"
                    }`}
                  >
                    <span>{sheet.name}</span>
                  </button>
                );
              })}

              {/* Add New Sheet */}
              <button
                onClick={addSheetTab}
                className="p-1 rounded-[4px] bg-[#16181d] border border-[#292d30] text-[#a1a4a5] hover:text-[#ffffff] hover:border-[#9281f7] transition-colors"
                title="Add blank worksheet tab"
              >
                <Plus className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* Status Statistics */}
            <div className="hidden sm:flex items-center gap-4 text-[11px] text-[#6e727a]">
              <span>
                Cell: {indexToColLetter(selectedCell.c)}
                {selectedCell.r + 1}
              </span>
              <span>
                Grid: {activeSheet?.rowCount || 30}R × {activeSheet?.columnCount || 15}C
              </span>
              <span>Sheets: {totalSheetsCount}</span>
            </div>
          </div>
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* DOCUMENTS (DOCS / WORD) MODE */}
      {/* -------------------------------------------------------------------- */}
      {docType === "docs" && (
        <div className="flex-1 flex flex-col overflow-hidden bg-[#0c0d10]">
          {/* Document Ribbon Toolbar */}
          <div className="flex items-center gap-2 px-4 py-2 border-b border-[#292d30] bg-[#16181d] shrink-0 overflow-x-auto text-xs font-mono">
            <span className="text-[#a1a4a5]">Formatting:</span>
            <button
              onClick={() => setDocMarkdown((m) => m + "\n\n# Heading 1\n")}
              className="px-2 py-1 rounded bg-[#1f2229] hover:bg-[#252830] text-[#ffffff]"
            >
              H1
            </button>
            <button
              onClick={() => setDocMarkdown((m) => m + "\n\n## Heading 2\n")}
              className="px-2 py-1 rounded bg-[#1f2229] hover:bg-[#252830] text-[#ffffff]"
            >
              H2
            </button>
            <button
              onClick={() => setDocMarkdown((m) => m + "\n\n### Heading 3\n")}
              className="px-2 py-1 rounded bg-[#1f2229] hover:bg-[#252830] text-[#ffffff]"
            >
              H3
            </button>
            <button
              onClick={() => setDocMarkdown((m) => m + "\n- Item point\n")}
              className="px-2 py-1 rounded bg-[#1f2229] hover:bg-[#252830] text-[#ffffff]"
            >
              • Bullet
            </button>
            <button
              onClick={() => setDocMarkdown((m) => m + "\n| Column 1 | Column 2 |\n|---|---|\n| Data A | Data B |\n")}
              className="px-2 py-1 rounded bg-[#1f2229] hover:bg-[#252830] text-[#ffffff] flex items-center gap-1"
            >
              <Table className="h-3 w-3" />
              <span>Table</span>
            </button>
            <div className="h-4 w-[1px] bg-[#292d30] mx-1" />
            <button
              onClick={() => window.print()}
              className="px-2.5 py-1 rounded bg-[#1f2229] hover:bg-[#252830] text-[#a1a4a5] hover:text-[#ffffff] flex items-center gap-1"
            >
              <Printer className="h-3 w-3" />
              <span>Print / PDF</span>
            </button>
          </div>

          {/* Document Paper Editor Canvas */}
          <div className="flex-1 overflow-auto p-4 sm:p-8 flex justify-center bg-[#090a0d]">
            <div className="w-full max-w-[850px] min-h-[1050px] bg-[#121418] border border-[#292d30] rounded-[8px] p-8 sm:p-14 shadow-2xl flex flex-col">
              <textarea
                value={docMarkdown}
                onChange={(e) => setDocMarkdown(e.target.value)}
                className="w-full flex-1 bg-transparent text-[#e6e8eb] font-sans text-sm sm:text-base leading-relaxed outline-none resize-none border-none selection:bg-[#9281f7]/30"
                placeholder="Start typing your executive intelligence report or paste notes..."
              />
            </div>
          </div>
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* LIVE DATA CONNECTOR DRAWER */}
      {/* -------------------------------------------------------------------- */}
      {sourcesDrawerOpen && (
        <div className="fixed inset-0 z-50 bg-[#000000]/70 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-md h-full bg-[#121418] border-l border-[#292d30] p-6 flex flex-col justify-between shadow-2xl animate-in slide-in-from-right duration-200">
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-[#292d30]">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-[#9281f7]" />
                  <h3 className="font-serif text-lg font-normal text-[#ffffff]">Connect Live Data</h3>
                </div>
                <button
                  onClick={() => setSourcesDrawerOpen(false)}
                  className="p-1 rounded text-[#a1a4a5] hover:text-[#ffffff]"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <p className="text-xs text-[#a1a4a5] leading-relaxed">
                Connect real-time findings from your Consumer Discovery sweeps or SEO & GEO audits directly into your sheets and docs without copy-pasting.
              </p>

              {isLoadingSources ? (
                <div className="py-12 text-center text-xs font-mono text-[#a1a4a5]">
                  <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-[#9281f7]" />
                  Harvesting active project sources...
                </div>
              ) : (
                <div className="space-y-4 max-h-[calc(100vh-220px)] overflow-y-auto pr-1">
                  {/* Research Sources */}
                  <div>
                    <div className="text-[11px] font-mono text-[#9281f7] uppercase font-bold tracking-wider mb-2">
                      Consumer Discovery Sweeps
                    </div>
                    {sourcesList.research?.length === 0 ? (
                      <div className="p-3 rounded bg-[#181a20] border border-[#292d30] text-xs text-[#6e727a]">
                        No completed discovery sessions yet. Run a sweep from Launchpad.
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {sourcesList.research.map((s) => (
                          <div
                            key={s.id}
                            onClick={() => handleConnectSource("research", s.id)}
                            className="p-3 rounded-[6px] bg-[#181a20] border border-[#292d30] hover:border-[#9281f7] cursor-pointer transition-all hover:bg-[#1f2229]"
                          >
                            <div className="flex items-center justify-between text-xs font-medium text-[#ffffff]">
                              <span className="truncate">{s.title}</span>
                              <span className="text-[10px] font-mono text-[#3ad389] uppercase">
                                {s.status}
                              </span>
                            </div>
                            <div className="flex items-center gap-2 mt-1.5 text-[11px] font-mono text-[#6e727a]">
                              <span>{s.meta?.clusters_count || 0} clusters</span>
                              <span>•</span>
                              <span>{s.meta?.signals_count || 0} signals</span>
                              <span>•</span>
                              <span>{new Date(s.created_at).toLocaleDateString()}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* SEO Sources */}
                  <div>
                    <div className="text-[11px] font-mono text-[#3ad389] uppercase font-bold tracking-wider mb-2">
                      SEO & GEO Audits
                    </div>
                    {sourcesList.seo?.length === 0 ? (
                      <div className="p-3 rounded bg-[#181a20] border border-[#292d30] text-xs text-[#6e727a]">
                        No completed SEO audits yet. Run an audit from SEO Studio.
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {sourcesList.seo.map((s) => (
                          <div
                            key={s.id}
                            onClick={() => handleConnectSource("seo", s.id)}
                            className="p-3 rounded-[6px] bg-[#181a20] border border-[#292d30] hover:border-[#3ad389] cursor-pointer transition-all hover:bg-[#1f2229]"
                          >
                            <div className="flex items-center justify-between text-xs font-medium text-[#ffffff]">
                              <span className="truncate">{s.title}</span>
                              <span className="text-[10px] font-mono text-[#3ad389] font-bold">
                                {s.meta?.overall_score || 0}/100
                              </span>
                            </div>
                            <div className="flex items-center gap-2 mt-1.5 text-[11px] font-mono text-[#6e727a]">
                              <span>GEO Score: {s.meta?.geo_score || 0}</span>
                              <span>•</span>
                              <span>{new Date(s.created_at).toLocaleDateString()}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            <div className="pt-4 border-t border-[#292d30]">
              <button
                onClick={() => setSourcesDrawerOpen(false)}
                className="w-full py-2 rounded-[6px] bg-[#181a20] border border-[#292d30] text-xs font-sans text-[#a1a4a5] hover:text-[#ffffff]"
              >
                Close Drawer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* SAVED DOCUMENTS DRAWER */}
      {/* -------------------------------------------------------------------- */}
      {savedDocsDrawerOpen && (
        <div className="fixed inset-0 z-50 bg-[#000000]/70 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-md h-full bg-[#121418] border-l border-[#292d30] p-6 flex flex-col justify-between shadow-2xl animate-in slide-in-from-right duration-200">
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-[#292d30]">
                <div className="flex items-center gap-2">
                  <FolderOpen className="h-4 w-4 text-[#9281f7]" />
                  <h3 className="font-serif text-lg font-normal text-[#ffffff]">Saved Office Files</h3>
                </div>
                <button
                  onClick={() => setSavedDocsDrawerOpen(false)}
                  className="p-1 rounded text-[#a1a4a5] hover:text-[#ffffff]"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              {savedDocsList.length === 0 ? (
                <div className="py-12 text-center text-xs font-mono text-[#6e727a]">
                  No saved files yet. Click "Save" in the top bar to persist your work.
                </div>
              ) : (
                <div className="space-y-2 max-h-[calc(100vh-200px)] overflow-y-auto pr-1">
                  {savedDocsList.map((doc) => (
                    <div
                      key={doc.id}
                      onClick={() => loadSavedDocumentById(doc.id)}
                      className="p-3.5 rounded-[6px] bg-[#181a20] border border-[#292d30] hover:border-[#9281f7] cursor-pointer transition-all hover:bg-[#1f2229] flex items-center justify-between group"
                    >
                      <div className="flex items-center gap-2.5 overflow-hidden">
                        {doc.doc_type === "sheets" ? (
                          <FileSpreadsheet className="h-4 w-4 text-[#3ad389] shrink-0" />
                        ) : (
                          <FileText className="h-4 w-4 text-[#9281f7] shrink-0" />
                        )}
                        <div className="overflow-hidden">
                          <div className="text-xs font-medium text-[#ffffff] truncate">
                            {doc.title}
                          </div>
                          <div className="text-[10px] font-mono text-[#6e727a] mt-0.5">
                            {new Date(doc.updated_at || doc.created_at).toLocaleString()}
                          </div>
                        </div>
                      </div>

                      <button
                        onClick={(e) => handleDeleteSavedDoc(doc.id, e)}
                        className="opacity-0 group-hover:opacity-100 p-1.5 rounded hover:bg-[#ff9592]/20 text-[#a1a4a5] hover:text-[#ff9592] transition-all"
                        title="Delete file"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="pt-4 border-t border-[#292d30]">
              <button
                onClick={() => setSavedDocsDrawerOpen(false)}
                className="w-full py-2 rounded-[6px] bg-[#181a20] border border-[#292d30] text-xs font-sans text-[#a1a4a5] hover:text-[#ffffff]"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* TOAST NOTIFICATION */}
      {/* -------------------------------------------------------------------- */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 px-4 py-2.5 rounded-[8px] bg-[#1f2229] border border-[#9281f7]/50 text-xs font-sans font-medium text-[#ffffff] shadow-2xl flex items-center gap-2 animate-in fade-in duration-150">
          <Sparkles className="h-4 w-4 text-[#9281f7]" />
          <span>{toastMessage}</span>
        </div>
      )}
    </div>
  );
}

export default function OfficeStudioPage() {
  return (
    <Suspense
      fallback={
        <div className="h-screen w-screen bg-[#0c0d10] flex items-center justify-center text-xs font-mono text-[#a1a4a5]">
          <div className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4 animate-spin text-[#9281f7]" />
            <span>Loading Office Studio...</span>
          </div>
        </div>
      }
    >
      <OfficeStudioContent />
    </Suspense>
  );
}
