import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

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
        <div className="flex-1">
          <Navbar />
          <main className="mx-auto max-w-[1200px] px-4 sm:px-6 lg:px-8 py-10 sm:py-14">
            {children}
          </main>
        </div>
        <Footer />
      </body>
    </html>
  );
}
