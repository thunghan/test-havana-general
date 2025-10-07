import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  distDir: '../backend/static',
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
