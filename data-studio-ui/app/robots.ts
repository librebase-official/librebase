import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  const disallow = ["/api/", "/login", "/admin", "/setup", "/invite", "/projects/"];
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow,
      },
      // AI / answer-engine crawlers: explicitly welcome, so the MCP setup is
      // discoverable and citable (AEO).
      {
        userAgent: [
          "GPTBot",
          "OAI-SearchBot",
          "ClaudeBot",
          "Claude-SearchBot",
          "anthropic-ai",
          "PerplexityBot",
          "Google-Extended",
          "CCBot",
          "Bytespider",
        ],
        allow: ["/", "/for-agents", "/llms.txt"],
        disallow,
      },
    ],
  };
}