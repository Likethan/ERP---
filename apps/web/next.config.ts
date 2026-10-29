import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  reactStrictMode: true,
  transpilePackages: ["@campusos/types"],
  eslint: {
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
