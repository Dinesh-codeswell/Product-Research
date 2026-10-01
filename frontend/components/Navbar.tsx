"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Radio, Github, Key, Plus, Globe, Cpu, FileSpreadsheet, Bell, FlaskConical, Menu, X } from "lucide-react";
import { ChannelSettingsModal } from "@/components/ChannelSettingsModal";

const NAV_LINKS = [
  { href: "/", label: "Discovery", full: "Consumer Discovery", icon: null },
  { href: "/seo", label: "SEO & GEO", full: "SEO & GEO Studio", icon: Globe, accent: "text-[#9281f7]", dot: "bg-[#3ad389]" },
  { href: "/models", label: "AI Models", full: "AI Models & Free Tier", icon: Cpu, accent: "text-[#9281f7]", badge: "7.4B" },
  { href: "/office", label: "Office", full: "Office Studio", icon: FileSpreadsheet, accent: "text-[#9281f7]" },
  { href: "/watchlists", label: "Watchlists", full: "Watchlists", icon: Bell, accent: "text-[#ffca16]" },
  { href: "/lab", label: "Lab", full: "Lab", icon: FlaskConical, accent: "text-[#9281f7]", dot: "bg-[#9281f7]" },
];

export function Navbar() {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const pathname = usePathname();

  // Close the mobile menu whenever the route changes
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [pathname]);

  const isActive = (href: string) => {
    if (href === "/") return !["/seo", "/models", "/office", "/watchlists", "/lab"].some((p) => pathname?.startsWith(p));
    return pathname?.startsWith(href) || false;
  };

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-[#292d30] bg-[#000000]/90 backdrop-blur-xl pt-[env(safe-area-inset-top)]">
        <div className="mx-auto flex h-16 max-w-[1200px] items-center justify-between gap-2 px-3 sm:px-6 lg:px-8">
          {/* Brand Logo & Wordmark — never shrinks, never overlaps */}
          <Link href="/" className="flex items-center gap-2 sm:gap-3 group transition-opacity shrink-0 min-w-0">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[6px] bg-[#000000] border border-[#292d30] text-[#9281f7] group-hover:border-[#9281f7]/50 transition-colors">
              <Radio className="h-4 w-4" />
            </div>
            <div className="flex items-baseline gap-2 min-w-0">
              <span className="font-sans font-semibold text-sm sm:text-base tracking-tight text-[#ffffff] whitespace-nowrap">
                PulseRadar
              </span>
              <span className="hidden sm:inline-block text-[11px] font-mono text-[#9281f7] bg-[#000000] px-2 py-0.5 rounded-[6px] border border-[#292d30] whitespace-nowrap">
                studio
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Links (ghost pill on black; scrollable safety net) */}
          <nav className="hidden lg:flex items-center gap-1 border border-[#292d30] rounded-[8px] p-1 bg-[#000000] max-w-full overflow-x-auto no-scrollbar">
            {NAV_LINKS.map((link) => {
              const Icon = link.icon;
              const active = isActive(link.href);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-1 rounded-[6px] text-xs font-mono flex items-center gap-1.5 transition-all whitespace-nowrap ${
                    active
                      ? "bg-[#9281f7]/20 border border-[#9281f7]/40 text-[#ffffff] font-medium"
                      : "text-[#a1a4a5] hover:text-[#ffffff] border border-transparent"
                  }`}
                >
                  {Icon && <Icon className={`h-3 w-3 ${link.accent || ""}`} />}
                  <span>{link.label}</span>
                  {link.badge && (
                    <span className="text-[10px] font-mono bg-[#3ad389]/20 text-[#3ad389] px-1 py-0.2 rounded border border-[#3ad389]/30">
                      {link.badge}
                    </span>
                  )}
                  {link.dot && <span className={`h-1.5 w-1.5 rounded-full ${link.dot}`} />}
                </Link>
              );
            })}
          </nav>

          {/* Right Actions — condense gracefully on small screens */}
          <div className="flex items-center gap-1.5 sm:gap-2.5 shrink-0">
            <button
              onClick={() => setIsSettingsOpen(true)}
              className="hidden md:inline-flex items-center gap-1.5 text-xs font-sans font-medium text-[#f0f0f0] hover:text-[#ffffff] px-3.5 py-1.5 rounded-[6px] bg-transparent border border-[#292d30] hover:border-[#ffffff] transition-all whitespace-nowrap"
            >
              <Key className="h-3.5 w-3.5 text-[#9281f7]" />
              <span>Platform Auth</span>
            </button>

            <Link
              href="/"
              className="inline-flex items-center gap-1.5 text-xs font-sans font-medium text-[#ffffff] px-2.5 sm:px-3.5 py-1.5 rounded-[6px] bg-transparent border border-[#292d30] hover:border-[#ffffff] transition-all whitespace-nowrap"
              aria-label="New Sweep"
            >
              <Plus className="h-3.5 w-3.5 text-[#f0f0f0] shrink-0" />
              <span className="hidden min-[400px]:inline">New Sweep</span>
            </Link>

            <a
              href="https://github.com"
              target="_blank"
              rel="noreferrer"
              title="GitHub Repository"
              className="hidden sm:block p-1.5 rounded-[6px] text-[#a1a4a5] hover:text-[#ffffff] border border-transparent hover:border-[#292d30] transition-colors"
            >
              <Github className="h-4 w-4" />
            </a>

            {/* Mobile Menu Toggle */}
            <button
              onClick={() => setIsMobileMenuOpen((v) => !v)}
              className="lg:hidden inline-flex items-center justify-center p-2 rounded-[6px] text-[#a1a4a5] hover:text-[#ffffff] border border-[#292d30] hover:border-[#ffffff]/40 transition-colors"
              aria-label="Toggle navigation menu"
              aria-expanded={isMobileMenuOpen}
            >
              {isMobileMenuOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
            </button>
          </div>
        </div>

        {/* Mobile / Tablet Slide-Down Menu */}
        {isMobileMenuOpen && (
          <nav className="lg:hidden border-t border-[#292d30] bg-[#000000]/98 backdrop-blur-xl">
            <div className="mx-auto max-w-[1200px] px-3 sm:px-6 py-3 space-y-1">
              {NAV_LINKS.map((link) => {
                const Icon = link.icon;
                const active = isActive(link.href);
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`flex items-center gap-2.5 px-3 py-2.5 rounded-[8px] text-xs font-mono transition-all ${
                      active
                        ? "bg-[#9281f7]/20 border border-[#9281f7]/40 text-[#ffffff] font-medium"
                        : "text-[#a1a4a5] hover:text-[#ffffff] hover:bg-[#121418] border border-transparent"
                    }`}
                  >
                    {Icon ? (
                      <Icon className={`h-3.5 w-3.5 shrink-0 ${link.accent || ""}`} />
                    ) : (
                      <span className="h-3.5 w-3.5 shrink-0 rounded-[4px] border border-[#292d30] flex items-center justify-center">
                        <span className="h-1 w-1 rounded-full bg-[#9281f7]" />
                      </span>
                    )}
                    <span className="flex-1">{link.full || link.label}</span>
                    {link.badge && (
                      <span className="text-[10px] font-mono bg-[#3ad389]/20 text-[#3ad389] px-1 py-0.2 rounded border border-[#3ad389]/30">
                        {link.badge}
                      </span>
                    )}
                    {link.dot && <span className={`h-1.5 w-1.5 rounded-full ${link.dot}`} />}
                  </Link>
                );
              })}
              <button
                onClick={() => setIsSettingsOpen(true)}
                className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-[8px] text-xs font-mono text-[#a1a4a5] hover:text-[#ffffff] hover:bg-[#121418] border border-transparent transition-all"
              >
                <Key className="h-3.5 w-3.5 text-[#9281f7] shrink-0" />
                <span>Platform Auth</span>
              </button>
            </div>
          </nav>
        )}
      </header>

      <ChannelSettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
    </>
  );
}
