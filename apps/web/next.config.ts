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
  async redirects() {
    return [
      {
        source: "/faculty",
        destination: "/login?role=faculty",
        permanent: false,
      },
      {
        source: "/student",
        destination: "/login?role=student",
        permanent: false,
      },
      {
        source: "/vice-principal",
        destination: "/login?role=vice_principal",
        permanent: false,
      },
      {
        source: "/hod",
        destination: "/login?role=hod",
        permanent: false,
      },
      {
        source: "/admin",
        destination: "/login?role=admin",
        permanent: false,
      },
    ];
  },
};

export default nextConfig;
