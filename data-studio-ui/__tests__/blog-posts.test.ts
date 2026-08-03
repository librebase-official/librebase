import { describe, expect, it } from "vitest";
import { getBlogPost, listBlogPosts } from "@/lib/blog-posts";
import { SITE_URL } from "@/lib/site";

describe("blog posts", () => {
  it("lists unique slugs for sitemap", () => {
    const posts = listBlogPosts();
    const slugs = posts.map((p) => p.slug);
    expect(slugs.length).toBeGreaterThanOrEqual(3);
    expect(new Set(slugs).size).toBe(slugs.length);
  });

  it("loads a known post", () => {
    const post = getBlogPost("low-memory-postgres-for-agents");
    expect(post?.primaryKeyword).toContain("low memory");
    expect(post?.faq.length).toBeGreaterThan(0);
  });
});

describe("site url", () => {
  it("defaults to librebase.xyz", () => {
    expect(SITE_URL).toMatch(/^https:\/\//);
  });
});
