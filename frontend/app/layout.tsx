import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/AppShell";

export const metadata: Metadata = {
  title: "PulseRadar — Autonomous Multi-Channel Product Research & SEO/GEO Studio",
  description:
    "Turn raw multi-channel chatter across Reddit, YouTube, Twitter/X, GitHub, and Google into verified, evidence-backed product specifications and 4-pillar Generative Engine Optimization.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark bg-[#000000]">
      <body className="min-h-screen bg-[#000000] text-[#f0f0f0] font-sans antialiased selection:bg-[#9281f7]/25 selection:text-white flex flex-col justify-between">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
