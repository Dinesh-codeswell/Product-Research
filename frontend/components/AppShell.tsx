"use client";

import React, { Suspense } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

function AppShellContent({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const isPlayground = pathname === "/playground" || (pathname === "/models" && searchParams?.get("tab") === "playground");

  if (isPlayground) {
    return <main className="w-screen h-screen overflow-hidden bg-[#0c0d10]">{children}</main>;
  }

  return (
    <div className="flex-1 flex flex-col min-h-screen justify-between">
      <Navbar />
      <main className="mx-auto w-full max-w-[1200px] px-4 sm:px-6 lg:px-8 py-10 sm:py-14 flex-1">
        {children}
      </main>
      <Footer />
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#000000]">{children}</div>}>
      <AppShellContent>{children}</AppShellContent>
    </Suspense>
  );
}
