/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        stone: {
          paper: "#f6f4ee",
          surface: "#faf7f0",
          pill: "#eeece2",
          ink: "#24231f",
          inkHover: "#3d3a33",
          muted: "#706e68",
          subtle: "#525048",
          border: "rgba(36, 35, 31, 0.12)",
          borderStrong: "rgba(36, 35, 31, 0.22)",
        },
        brand: {
          DEFAULT: "#5369d9",
          strong: "#4052b3",
          light: "#8d9cf2",
          cyan: "#00d4ff",
        },
        covenant: {
          DEFAULT: "#15803d",
          dark: "#166534",
          light: "#34d399",
        },
        terracotta: {
          DEFAULT: "#bd7652",
          dark: "#985b39",
        },
        crimson: {
          DEFAULT: "#b91c1c",
          dark: "#991b1b",
        },
        "dark-bg": "#080d11",
        "dark-surface": "#0d171d",
      },
      fontFamily: {
        serif: ["'Newsreader'", "'Iowan Old Style'", "Georgia", "serif"],
        sans: ["'Inter'", "-apple-system", "BlinkMacSystemFont", "'Outfit'", "'Space Grotesk'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      boxShadow: {
        tactile: "0 4px 20px rgba(36, 35, 31, 0.04)",
        "tactile-hover": "0 8px 28px rgba(36, 35, 31, 0.07)",
      },
    },
  },
  plugins: [],
};
