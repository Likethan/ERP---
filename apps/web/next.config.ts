import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@campusos/types"],
  eslint: {
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
