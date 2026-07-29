import type { Metadata } from "next";
import Link from "next/link";
import { listBlogPosts } from "@/lib/blog-posts";
import { SITE_URL } from "@/lib/site";

export const metadata: Metadata = {
  title: "Blog | Librebase",
  description:
    "Notes on low-memory Postgres, honest health metrics, and portable data layers for apps and agents.",
  alternates: { canonical: `${SITE_URL}/blog` },
  openGraph: {
    title: "Librebase blog",
    description:
      "Low-memory Postgres, honest health metrics, and portable agent data layers.",
    url: `${SITE_URL}/blog`,
    siteName: "Librebase",
    type: "website",
  },
};

export default function BlogIndexPage() {
  const posts = listBlogPosts();

  return (
    <main className="lb-blog">
      <header className="lb-blog-header">
        <Link href="/" className="lb-wordmark" aria-label="Librebase home">
          Librebase
        </Link>
        <nav className="lb-blog-nav" aria-label="Blog">
          <Link href="/#waitlist">Join the waitlist for early access</Link>
        </nav>
      </header>

      <section className="lb-blog-index">
        <h1>Blog</h1>
        <p className="lb-blog-lead">
          Practical notes on Postgres-compatible backends for apps and agents.
        </p>
        <ul className="lb-blog-list">
          {posts.map((post) => (
            <li key={post.slug}>
              <Link href={`/blog/${post.slug}`}>
                <span className="lb-blog-list-title">{post.title}</span>
                <span className="lb-blog-list-desc">{post.description}</span>
                <time dateTime={post.publishedAt}>{post.publishedAt}</time>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
