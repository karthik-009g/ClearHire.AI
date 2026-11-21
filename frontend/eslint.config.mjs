import nextConfig from "eslint-config-next";

const config = [
  ...nextConfig,
  {
    rules: {
      "no-console": "off",
      "react/no-unescaped-entities": "off",
      "react/jsx-no-comment-textnodes": "off",
      "react-hooks/refs": "off",
      "react-hooks/immutability": "off",
      "react-hooks/exhaustive-deps": "warn",
      "import/no-anonymous-default-export": "off",
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
      "react-hooks/set-state-in-effect": "off",
    },
  },
  {
    ignores: [
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
    ],
  },
];

export default config;
