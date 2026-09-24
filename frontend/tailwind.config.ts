import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Resend Core Palette
        "void-black": "#000000",
        "graphite-hairline": "#292d30",
        "bone-white": "#f0f0f0",
        "ash-gray": "#a1a4a5",
        "smoke-gray": "#abafb4",
        iron: "#6e727a",
        charcoal: "#464a4d",

        // Accents & Signals
        "iris-violet": "#9281f7",
        "iris-violet-glow": "#baa7ff",
        "signal-blue": "#3b9eff",
        "sky-blue": "#70b8ff",
        "pulse-green": "#3ad389",
        "alarm-red": "#ff9592",
        crimson: "#ff6465",
        amber: "#ffca16",
        "amber-glow": "#ffd60a",
        "surface-lift": "#0b0e14",

        // Aliased semantic surfaces for compatibility
        background: "#000000",
        surface: {
          DEFAULT: "#000000",
          elevated: "#0b0e14",
        },
        border: {
          subtle: "#292d30",
          focus: "#ffffff",
        },
        radar: {
          cyan: "#9281f7", // mapped to signature Iris Violet
          blue: "#3b9eff", // Signal Blue
        },
        category: {
          pain: "#ff9592",
          workaround: "#ffca16",
          desire: "#70b8ff",
          churn: "#baa7ff",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
        serif: [
          "Domaine",
          "Newsreader",
          "Playfair Display",
          "Georgia",
          "serif",
        ],
        display: [
          "aBC Favorit",
          "Inter Display",
          "Inter",
          "system-ui",
          "sans-serif",
        ],
        mono: [
          "Commit Mono",
          "JetBrains Mono",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "monospace",
        ],
      },
      borderRadius: {
        cards: "16px",
        badges: "6px",
        inputs: "6px",
        buttons: "6px",
        "large-panels": "24px",
      },
      boxShadow: {
        subtle: "rgba(176, 199, 217, 0.145) 0px 0px 0px 1px",
        "subtle-2": "rgb(0, 0, 0) 0px 0px 0px 8px",
        "subtle-3": "rgba(0, 0, 0, 0.1) 0px 1px 3px 0px, rgba(0, 0, 0, 0.1) 0px 1px 2px -1px",
      },
      letterSpacing: {
        tightest: "-0.05em",
        tighter: "-0.025em",
        domaine: "-0.01em",
      },
    },
  },
  plugins: [],
};

export default config;
