import type { NextConfig } from "next";

const isStandalone =
  process.env.BUILD_STANDALONE === "true" || process.env.DOCKER_BUILD === "1";

const nextConfig: NextConfig = {
  ...(isStandalone ? { output: "standalone" } : {}),
  reactStrictMode: false,
  transpilePackages: ["@campusos/types"],
  eslint: {
    ignoreDuringBuilds: true,
  },
  onDemandEntries: {
    maxInactiveAge: 60 * 60 * 1000,
    pagesBufferLength: 50,
  },
  experimental: {
    optimizePackageImports: ["lucide-react", "@campusos/types"],
  },
};

export default nextConfig;
