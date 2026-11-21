import { defineConfig, globalIgnores } from "next/dist/build/templates/eslint.config.mjs";
import nextVitals from "eslint-config-next/core-web-vitals.js";

export default defineConfig([
  ...nextVitals,
  {
    rules: {
      "no-console": "off",
    },
  },
  {
    files: [
      "src/pages/applications.js",
      "src/pages/index.js",
      "src/pages/jd-analyzer.js",
      "src/pages/job-hunter.js",
      "src/pages/resmat-ai.js",
      "src/pages/student-lab.js",
    ],
    rules: {
      // These pages hydrate browser-only localStorage state after the client mounts.
      "react-hooks/set-state-in-effect": "off",
    },
  },
  globalIgnores([
    ".next/**",
    "out/**",
    "build/**",
    "dist/**",
    "node_modules/**",
    "public/**",
    "__tests__/**",
    "scripts/**",
    "next-env.d.ts",
    "jest.config.js",
    "jest.setup.js",
  ]),
]);
