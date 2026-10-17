import type { NextConfig } from "next";

// Behind nginx (docker compose) the browser reaches the API on the same origin
// and these rewrites are never hit. For plain `npm run dev` they proxy API calls
// to the local backend so no frontend .env file is needed.
const DEV_BACKEND = "http://localhost:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  reactStrictMode: true,
  poweredByHeader: false,
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${DEV_BACKEND}/api/:path*` },
      { source: "/health", destination: `${DEV_BACKEND}/health` },
    ];
  },
};

export default nextConfig;
