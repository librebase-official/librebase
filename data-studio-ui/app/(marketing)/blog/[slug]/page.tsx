import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getBlogPost, listBlogPosts } from "@/lib/blog-posts";
import { SITE_URL } from "@/lib/site";

type Props = { params: Promise<{ slug: string }> };

export function generateStaticParams() {
  return listBlogPosts().map((post) => ({ slug: post.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const post = getBlogPost(slug);
  if (!post) return { title: "Not found | Librebase" };

  const url = `${SITE_URL}/blog/${post.slug}`;
  return {
    title: `${post.title} | Librebase`,
    description: post.description,
    keywords: [post.primaryKeyword, "librebase", "postgres"],
    alternates: { canonical: url },
    openGraph: {
      title: post.title,
      description: post.description,
      url,
      siteName: "Librebase",
      type: "article",
      publishedTime: post.publishedAt,
      modifiedTime: post.updatedAt,
    },
  };
}

export default async function BlogPostPage({ params }: Props) {
  const { slug } = await params;
  const post = getBlogPost(slug);
  if (!post) notFound();

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: post.title,
    description: post.description,
    datePublished: post.publishedAt,
    dateModified: post.updatedAt,
    author: { "@type": "Organization", name: "Librebase" },
    publisher: { "@type": "Organization", name: "Librebase", url: SITE_URL },
    mainEntityOfPage: `${SITE_URL}/blog/${post.slug}`,
  };

  const faqLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: post.faq.map((item) => ({
      "@type": "Question",
      name: item.question,
      acceptedAnswer: { "@type": "Answer", text: item.answer },
    })),
  };

  return (
    <main className="lb-blog">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqLd) }}
      />

      <header className="lb-blog-header">
        <Link href="/" className="lb-wordmark" aria-label="Librebase home">
          Librebase
        </Link>
        <nav className="lb-blog-nav" aria-label="Blog">
          <Link href="/blog">All posts</Link>
          <Link href="/#waitlist">Join the waitlist for early access</Link>
        </nav>
      </header>

      <article className="lb-blog-article">
        <p className="lb-blog-kicker">
          <Link href="/blog">Blog</Link>
          <span aria-hidden="true"> · </span>
          <time dateTime={post.publishedAt}>{post.publishedAt}</time>
        </p>
        <h1>{post.title}</h1>
        <p className="lb-blog-lead">{post.description}</p>

        {post.sections.map((section) => (
          <section key={section.heading}>
            <h2>{section.heading}</h2>
            {section.body.split("\n\n").map((para, i) => (
              <p key={`${section.heading}-${i}`}>{linkifyInternal(para)}</p>
            ))}
          </section>
        ))}

        <section className="lb-blog-faq" aria-labelledby="blog-faq-heading">
          <h2 id="blog-faq-heading">Questions</h2>
          {post.faq.map((item) => (
            <details key={item.question}>
              <summary>{item.question}</summary>
              <p>{item.answer}</p>
            </details>
          ))}
        </section>

        <p className="lb-blog-cta">
          <a className="lb-btn lb-btn-primary" href="/#waitlist">
            Join the waitlist for early access
          </a>
        </p>
      </article>
    </main>
  );
}

/** Render markdown-ish [label](/path) links inside plain paragraphs. */
function linkifyInternal(text: string): ReactNode {
  const parts: ReactNode[] = [];
  const re = /\[([^\]]+)\]\((\/[^)]+)\)/g;
  let last = 0;
  let match: RegExpExecArray | null;
  let key = 0;
  while ((match = re.exec(text)) !== null) {
    if (match.index > last) parts.push(text.slice(last, match.index));
    parts.push(
      <Link key={`l${key++}`} href={match[2]}>
        {match[1]}
      </Link>,
    );
    last = match.index + match[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts.length ? parts : text;
}
