import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // No server-only features anywhere in the app (no API routes, no
  // server actions, no dynamic route params, no next/image) - verified
  // before enabling this. Static export means the frontend can be
  // hosted as a free static site instead of a paid Node web service.
  output: "export",
};

export default nextConfig;
