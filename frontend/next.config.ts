import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",  // Required for Docker
  reactCompiler: true,
};

export default nextConfig;
