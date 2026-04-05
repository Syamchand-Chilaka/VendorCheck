import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static export only for GitHub Pages landing-page build
  ...(process.env.GITHUB_PAGES ? { output: "export" as const } : {}),
  basePath: process.env.GITHUB_PAGES ? "/VendorCheck" : "",
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
