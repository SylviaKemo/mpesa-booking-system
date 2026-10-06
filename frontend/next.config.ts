import type { NextConfig } from "next";

/**
 * Where the booking API lives. Read at runtime, not NEXT_PUBLIC_: a
 * NEXT_PUBLIC_ value is inlined into the client bundle at build time, so one
 * artefact could never be deployed to two environments, and a build without it
 * ships browser calls pointed at the visitor's own machine.
 */
const API_URL = process.env.API_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  reactStrictMode: true,

  // The browser calls /api/* on this origin and Next forwards it, so no API
  // host is baked into the bundle and there is no cross-origin request.
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },

  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "swiftill.co.ke",
        pathname: "/uploads/**",
      },
    ],
  },
};

export default nextConfig;
