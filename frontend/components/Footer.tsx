"use client";

import React from "react";
import Link from "next/link";
import { Radio, Globe, Sparkles, Terminal, Github, ExternalLink, ShieldCheck, Cpu } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-[#292d30] bg-[#000000] pt-16 pb-12 mt-24">
      <div className="mx-auto max-w-[1200px] px-4 sm:px-6 lg:px-8 space-y-12">
        {/* Top Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-10">
          {/* Brand Column */}
          <div className="lg:col-span-2 space-y-4">
            <Link href="/" className="flex items-center gap-3 group inline-block">
              <div className="flex h-8 w-8 items-center justify-center rounded-[6px] bg-[#000000] border border-[#292d30] text-[#9281f7] group-hover:border-[#9281f7]/50 transition-colors">
                <Radio className="h-4 w-4" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="font-sans font-semibold text-base tracking-tight text-[#ffffff]">
                  PulseRadar
                </span>
                <span className="text-[11px] font-mono text-[#9281f7] bg-[#000000] px-2 py-0.5 rounded-[6px] border border-[#292d30]">
                  studio v2.0
                </span>
              </div>
            </Link>

            <p className="text-xs font-sans text-[#a1a4a5] leading-relaxed max-w-sm">
              Autonomous customer discovery, multi-channel pain point synthesis, and 4-pillar Generative Engine Optimization (GEO) engineered for product builders and engineering teams.
            </p>

            <div className="flex items-center gap-3 pt-2 text-xs font-mono text-[#6e727a]">
              <div className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-[#3ad389] animate-pulse" />
                <span className="text-[#f0f0f0]">Systems Operational</span>
              </div>
              <span>•</span>
              <span className="text-[#9281f7]">7 Search Channels</span>
            </div>
          </div>

          {/* Module 1: Consumer Intelligence */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono uppercase tracking-wider text-[#ffffff]">
              Consumer Discovery
            </h4>
            <ul className="space-y-2 text-xs font-sans text-[#a1a4a5]">
              <li>
                <Link href="/" className="hover:text-[#ffffff] transition-colors">
                  Multi-Channel Sweep
                </Link>
              </li>
              <li>
                <Link href="/" className="hover:text-[#ffffff] transition-colors flex items-center gap-1.5">
                  <span>Live Browser Agent</span>
                  <span className="text-[10px] font-mono px-1 py-0.2 rounded bg-[#9281f7]/20 text-[#9281f7]">NEW</span>
                </Link>
              </li>
              <li>
                <Link href="/" className="hover:text-[#ffffff] transition-colors">
                  Thematic Clustering
                </Link>
              </li>
              <li>
                <Link href="/" className="hover:text-[#ffffff] transition-colors">
                  Verbatim Quotes Matrix
                </Link>
              </li>
              <li>
                <Link href="/" className="hover:text-[#ffffff] transition-colors">
                  PRD &amp; Spec Studio
                </Link>
              </li>
              <li>
                <Link href="/" className="hover:text-[#ffffff] transition-colors">
                  AI Agent Bundles (.md)
                </Link>
              </li>
            </ul>
          </div>

          {/* Module 2: SEO & GEO Studio */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono uppercase tracking-wider text-[#ffffff]">
              SEO &amp; GEO Studio
            </h4>
            <ul className="space-y-2 text-xs font-sans text-[#a1a4a5]">
              <li>
                <Link href="/seo" className="hover:text-[#ffffff] transition-colors flex items-center gap-1.5">
                  <span>GEO AI Citation Audit</span>
                  <Sparkles className="h-3 w-3 text-[#9281f7]" />
                </Link>
              </li>
              <li>
                <Link href="/seo" className="hover:text-[#ffffff] transition-colors">
                  Playwright Hydration Gap
                </Link>
              </li>
              <li>
                <Link href="/seo" className="hover:text-[#ffffff] transition-colors">
                  Structured Data Schemas
                </Link>
              </li>
              <li>
                <Link href="/seo" className="hover:text-[#ffffff] transition-colors">
                  SERP &amp; Meta Generator
                </Link>
              </li>
              <li>
                <Link href="/seo" className="hover:text-[#ffffff] transition-colors">
                  Image SEO &amp; CLS Audit
                </Link>
              </li>
              <li>
                <Link href="/seo" className="hover:text-[#ffffff] transition-colors">
                  Drift &amp; Regression Shield
                </Link>
              </li>
            </ul>
          </div>

          {/* Connected Integrations & Channels */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono uppercase tracking-wider text-[#ffffff]">
              Crawl Engines
            </h4>
            <ul className="space-y-2 text-xs font-mono text-[#a1a4a5]">
              <li className="flex items-center justify-between">
                <span>Google &amp; Web</span>
                <span className="text-[10px] text-[#3ad389]">ZERO-AUTH</span>
              </li>
              <li className="flex items-center justify-between">
                <span>Reddit Discussions</span>
                <span className="text-[10px] text-[#3ad389]">DDG STEALTH</span>
              </li>
              <li className="flex items-center justify-between">
                <span>Twitter / X</span>
                <span className="text-[10px] text-[#9281f7]">SYNDICATED</span>
              </li>
              <li className="flex items-center justify-between">
                <span>YouTube Transcripts</span>
                <span className="text-[10px] text-[#3ad389]">ZERO-AUTH</span>
              </li>
              <li className="flex items-center justify-between">
                <span>Hacker News Algolia</span>
                <span className="text-[10px] text-[#3ad389]">ZERO-AUTH</span>
              </li>
              <li className="flex items-center justify-between">
                <span>GitHub Issues</span>
                <span className="text-[10px] text-[#3ad389]">ZERO-AUTH</span>
              </li>
              <li className="flex items-center justify-between">
                <span>Firecrawl API</span>
                <span className="text-[10px] text-[#9281f7]">MARKDOWN</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-[#292d30] flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-[#6e727a]">
          <div className="flex items-center gap-2">
            <span>&copy; {new Date().getFullYear()} PulseRadar Studio.</span>
            <span>All rights reserved.</span>
            <span className="hidden sm:inline text-[#292d30]">|</span>
            <span className="hidden sm:inline text-[#a1a4a5]">Resend Dark Velvet + Violet Neon</span>
          </div>

          <div className="flex items-center gap-6">
            <a href="https://github.com" target="_blank" rel="noreferrer" className="hover:text-[#ffffff] transition-colors flex items-center gap-1">
              <Github className="h-3.5 w-3.5" />
              <span>GitHub</span>
            </a>
            <Link href="/" className="hover:text-[#ffffff] transition-colors">
              Privacy &amp; Telemetry
            </Link>
            <Link href="/" className="hover:text-[#ffffff] transition-colors">
              Security &amp; Cookies
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
