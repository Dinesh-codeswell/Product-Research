"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Radio, Github, Key, Plus, ExternalLink, Globe, Sparkles, Cpu } from "lucide-react";
import { ChannelSettingsModal } from "@/components/ChannelSettingsModal";

export function Navbar() {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const pathname = usePathname();
  const isSeo = pathname?.startsWith("/seo");
  const isModels = pathname?.startsWith("/models");

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-[#292d30] bg-[#000000]/90 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-[1200px] items-center justify-between px-4 sm:px-6 lg:px-8">
          {/* Brand Logo & Wordmark */}
          <Link href="/" className="flex items-center gap-3 group transition-opacity">
            <div className="flex h-8 w-8 items-center justify-center rounded-[6px] bg-[#000000] border border-[#292d30] text-[#9281f7] group-hover:border-[#9281f7]/50 transition-colors">
              <Radio className="h-4 w-4" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="font-sans font-semibold text-base tracking-tight text-[#ffffff]">
                PulseRadar
              </span>
              <span className="text-[11px] font-mono text-[#9281f7] bg-[#000000] px-2 py-0.5 rounded-[6px] border border-[#292d30]">
                studio
              </span>
            </div>
          </Link>

          {/* Navigation Links (Ghost on black) */}
          <nav className="hidden md:flex items-center gap-1 border border-[#292d30] rounded-[8px] p-1 bg-[#000000]">
            <Link
              href="/"
              className={`px-3 py-1 rounded-[6px] text-xs font-mono transition-all ${
                !isSeo && !isModels
                  ? "bg-[#292d30]/60 text-[#ffffff] font-medium"
                  : "text-[#a1a4a5] hover:text-[#ffffff]"
              }`}
            >
              Consumer Discovery
            </Link>
            <Link
              href="/seo"
              className={`px-3 py-1 rounded-[6px] text-xs font-mono flex items-center gap-1.5 transition-all ${
                isSeo
                  ? "bg-[#9281f7]/20 border border-[#9281f7]/40 text-[#ffffff] font-medium"
                  : "text-[#a1a4a5] hover:text-[#ffffff]"
              }`}
            >
              <Globe className="h-3 w-3 text-[#9281f7]" />
              <span>SEO & GEO Studio</span>
              <span className="h-1.5 w-1.5 rounded-full bg-[#3ad389]" />
            </Link>
            <Link
              href="/models"
              className={`px-3 py-1 rounded-[6px] text-xs font-mono flex items-center gap-1.5 transition-all ${
                isModels
                  ? "bg-[#9281f7]/20 border border-[#9281f7]/40 text-[#ffffff] font-medium"
                  : "text-[#a1a4a5] hover:text-[#ffffff]"
              }`}
            >
              <Cpu className="h-3 w-3 text-[#9281f7]" />
              <span>AI Models & Free Tier</span>
              <span className="text-[10px] font-mono bg-[#3ad389]/20 text-[#3ad389] px-1 py-0.2 rounded border border-[#3ad389]/30">7.4B</span>
            </Link>
          </nav>


          {/* Right Ghost Actions */}
          <div className="flex items-center gap-2.5">
            <button
              onClick={() => setIsSettingsOpen(true)}
              className="hidden sm:inline-flex items-center gap-1.5 text-xs font-sans font-medium text-[#f0f0f0] hover:text-[#ffffff] px-3.5 py-1.5 rounded-[6px] bg-transparent border border-[#292d30] hover:border-[#ffffff] transition-all"
            >
              <Key className="h-3.5 w-3.5 text-[#9281f7]" />
              <span>Platform Auth</span>
            </button>

            <Link
              href="/"
              className="inline-flex items-center gap-1.5 text-xs font-sans font-medium text-[#ffffff] px-3.5 py-1.5 rounded-[6px] bg-transparent border border-[#292d30] hover:border-[#ffffff] transition-all"
            >
              <Plus className="h-3.5 w-3.5 text-[#f0f0f0]" />
              <span>New Sweep</span>
            </Link>

            <a
              href="https://github.com"
              target="_blank"
              rel="noreferrer"
              title="GitHub Repository"
              className="p-1.5 rounded-[6px] text-[#a1a4a5] hover:text-[#ffffff] border border-transparent hover:border-[#292d30] transition-colors"
            >
              <Github className="h-4 w-4" />
            </a>
          </div>
        </div>
      </header>

      <ChannelSettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
    </>
  );
}
