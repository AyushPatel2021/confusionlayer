import type { Config } from "tailwindcss";

// Design tokens sourced from DESIGN.md (paper & slate / calm teal / clay).
export default {
  content: ["./index.html", "./src/**/*.{vue,ts}"],
  theme: {
    extend: {
      colors: {
        paper: "#FAF8F3",
        surface: { DEFAULT: "#FFFFFF", sunken: "#F1EDE4" },
        hairline: "#E4DED2",
        ink: { 900: "#1F2A2E", 700: "#3C4A4F", 500: "#6B7880", 300: "#A6AFB4" },
        primary: { 50: "#EBF4F3", 100: "#D6EAE9", 500: "#178A8A", 600: "#0F6E6E" },
        accent: { 100: "#F6E3D8", 600: "#C1592E" },
        success: { DEFAULT: "#2E7D5B", bg: "#E2EFE8" },
        warning: { DEFAULT: "#B8862B", bg: "#F6ECD6" },
        danger: { DEFAULT: "#B23A3A", bg: "#F3DEDE" },
        info: { DEFAULT: "#2F6690", bg: "#DCE7F0" },
      },
      fontFamily: {
        serif: ["Fraunces", "Georgia", "serif"],
        sans: ['"Public Sans"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      borderRadius: { sm: "6px", md: "10px", lg: "16px" },
      boxShadow: {
        raised: "0 1px 2px rgba(31,42,46,.06), 0 2px 8px rgba(31,42,46,.05)",
        overlay: "0 8px 30px rgba(31,42,46,.14)",
      },
      maxWidth: { content: "1120px", reading: "720px" },
    },
  },
  plugins: [],
} satisfies Config;
