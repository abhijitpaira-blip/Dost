import type { Config } from "tailwindcss";

// DOST design tokens — warm, calm, trustworthy companion, not a generic SaaS kit.
// See docs/ARCHITECTURE.md for the design rationale.
const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        linen: {
          50: "#FBFAF6",
          100: "#F4F1E8",
          200: "#E8E2D2",
        },
        ink: {
          600: "#3A4441",
          700: "#293330",
          800: "#1C2422",
          900: "#141B19",
        },
        amber: {
          400: "#E4A339",
          500: "#D8912A",
          600: "#B5761E",
        },
        clay: {
          400: "#C77B65",
          500: "#B6644C",
        },
      },
      fontFamily: {
        display: ["var(--font-fraunces)", "serif"],
        body: ["var(--font-inter)", "sans-serif"],
      },
      borderRadius: {
        xl: "1rem",
        "2xl": "1.5rem",
      },
    },
  },
  plugins: [],
};

export default config;
