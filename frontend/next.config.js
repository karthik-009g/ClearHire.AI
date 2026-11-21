/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  distDir: process.env.NEXT_DIST_DIR || ".next",
  experimental: {
    agentUpgrade: "security",
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.API_PROXY_TARGET || "http://127.0.0.1:8000"}/api/:path*`,
      },
      {
        source: "/ready",
        destination: `${process.env.API_PROXY_TARGET || "http://127.0.0.1:8000"}/ready`,
      },
    ];
  },
};

module.exports = nextConfig;
