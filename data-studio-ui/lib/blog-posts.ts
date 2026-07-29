export type BlogPost = {
  slug: string;
  title: string;
  description: string;
  primaryKeyword: string;
  publishedAt: string;
  updatedAt: string;
  sections: { heading: string; body: string }[];
  faq: { question: string; answer: string }[];
};

/**
 * Marketing blog posts (Majico pipeline → host app).
 * Keep copy concrete; no example.com placeholders; no AI-slop filler.
 */
export const BLOG_POSTS: BlogPost[] = [
  {
    slug: "low-memory-postgres-for-agents",
    title: "Low-memory Postgres for agent backends",
    description:
      "How agent builders cut memory overhead on Postgres-compatible backends without fake-green dashboards.",
    primaryKeyword: "low memory postgres alternative agents",
    publishedAt: "2026-07-29",
    updatedAt: "2026-07-29",
    sections: [
      {
        heading: "Why memory overhead matters for autonomous agents",
        body: `Autonomous agents run in continuous loops where query speed drives throughput. When you scale a Postgres-compatible backend for that load, memory overhead becomes the first bottleneck. Heavy plugins and client libraries burn RAM before your agents finish useful work.

Excessive memory use stops agents from finishing multiple tasks in one window. Latency spikes when background processes compete with query threads. Agents stall on complex reads or miss context before their timer ends.

You need predictable allocation under load, and health signals that show real cost. That is why agent-first stacks move toward smaller runtimes instead of managed dashboards that hide spend.`,
      },
      {
        heading: "Hidden costs of managed dashboards",
        body: `Many vendors ship feature-rich dashboards with green status while true utilization stays opaque. You pay for capacity you cannot audit. Heavy client libraries keep sessions alive and inflate memory exactly when agents need headroom.

Proprietary auth and sync layers also create lock-in. Prefer open protocols and Postgres-compatible interfaces so you can move or self-host without rewriting agents. Regulated teams need honest metrics they can reconcile to spend, not marketing traffic lights.`,
      },
      {
        heading: "How Li keeps the footprint small",
        body: `Librebase writes database and platform logic in Li and ships a small runtime instead of stacking foreign adapters. Agents query without spawning helper processes for every integration. Memory stays predictable because there is less plugin surface to load.

Schemas and indexes stay under your control. Health indicators reflect what the runtime actually spends. Security defaults stay on without bolting on a second product for Auth, REST, and live updates.`,
      },
      {
        heading: "Honest health without fake-green UI",
        body: `Built-in Auth, REST, and real-time sync should not require proprietary lock mechanisms or megabytes of client SDK. Operators should read status from logs and runtime metrics, then map that to cost.

Teams can wire agents through open tooling without cloud-region lock-in. Start from the [Librebase waitlist](/#waitlist) or open the [console](/projects) when you are ready to try a dedicated instance.`,
      },
    ],
    faq: [
      {
        question: "How does a Li-based stack reduce memory versus a heavy managed Postgres layer?",
        answer:
          "Less plugin and client-library weight in the agent path. The runtime stays small, so query loops compete less with dashboard and SDK overhead.",
      },
      {
        question: "What is wrong with green-only managed dashboards for agents?",
        answer:
          "They often hide swap, connection pressure, and true spend. Agents then fail late, after the UI still looked healthy.",
      },
      {
        question: "Can Librebase work with open agent tooling?",
        answer:
          "Yes. Prefer Postgres-compatible access and open protocols so agents are not stuck on one vendor client library.",
      },
    ],
  },
  {
    slug: "honest-database-health-metrics",
    title: "Honest database health metrics vs fake-green dashboards",
    description:
      "Why traffic-light SaaS dashboards miss memory churn, and how to monitor Postgres-compatible backends with real signals.",
    primaryKeyword: "honest database health metrics vs saas dashboards",
    publishedAt: "2026-07-29",
    updatedAt: "2026-07-29",
    sections: [
      {
        heading: "The green dashboard fallacy",
        body: `Executive views often show green while memory churn, pool exhaustion, and silent latency stay invisible. That is a fake-green dashboard: the color looks correct, the system is not.

Traffic-light UI ignores agent-specific pressure. Queries may succeed while new agent sessions cannot open. Vendors still bill for the illusion of health. Regulated teams cannot rely on that for compliance or cost control.`,
      },
      {
        heading: "When on-track indicators lie about memory",
        body: `Success codes are not health. When a Postgres-compatible store spills to disk, every agent read slows down while the dashboard stays green. Connection pools exhaust without a color change until hard errors appear.

Track swap, pool wait, and active agent connections from backend signals. Alert on rising pressure before agents miss their windows. See also [low-memory Postgres for agents](/blog/low-memory-postgres-for-agents).`,
      },
      {
        heading: "Open standards and a small runtime",
        body: `Honest metrics pair well with open protocols and a small footprint. Librebase keeps Auth, REST, and live updates in the product path so you are not paying for a separate monitoring story that hides cost.

Platform teams should prefer raw runtime state over decorative status bars. That is the difference between operating and guessing.`,
      },
      {
        heading: "Backend logs as source of truth",
        body: `Shift trust from color chips to logs and metrics that name the failure mode. When swap starts, logs should show it before users or agents feel the cliff.

[Join the waitlist](/#waitlist) if you want hosted Librebase with status that stays incomplete until tests pass.`,
      },
    ],
    faq: [
      {
        question: "What is a fake-green SaaS dashboard?",
        answer:
          "A UI that reports healthy status while memory pressure, latency, or pool exhaustion is already hurting agent and app traffic.",
      },
      {
        question: "Why do traffic lights miss memory churn?",
        answer:
          "They often key off request success, not swap, cache miss rate, or pool wait time.",
      },
      {
        question: "How should teams monitor instead?",
        answer:
          "Use backend metrics and logs as primary truth, and treat green UI as a summary only when it is backed by those signals.",
      },
    ],
  },
  {
    slug: "avoid-vendor-lock-in-agent-data",
    title: "Avoid vendor lock-in in agent data layers",
    description:
      "How to keep agent SQL, auth, and sync portable with Postgres-compatible open standards instead of proprietary client libraries.",
    primaryKeyword: "prevent vendor lockin database agents postgres compatible",
    publishedAt: "2026-07-29",
    updatedAt: "2026-07-29",
    sections: [
      {
        heading: "Lock-in is deeper than Docker",
        body: `Containers and ORMs do not free you from proprietary auth APIs or vendor-only client libraries. Agent stacks that call a managed login or sync path directly inherit that vendor’s failure modes and pricing.

True portability starts at the wire: Postgres-compatible access, standard HTTP, and protocols you can re-point. Wrap vendor SDKs only when you must, and keep the core data path replaceable.`,
      },
      {
        heading: "Cost of proprietary auth on autonomous systems",
        body: `External identity and sync services add latency, token expiry, and opaque billing. Agents that depend on them cannot adapt when the vendor changes rate limits or breaks an API.

Own identity and data access against interfaces you control. Prefer clear health metrics over black-box dashboards. Read more on [honest health metrics](/blog/honest-database-health-metrics).`,
      },
      {
        heading: "Open protocols without heavy clients",
        body: `Build agents against Postgres-compatible SQL and open tool protocols instead of megabyte SDKs. You keep visibility into memory and failures, and you can move hosts without rewriting every agent loop.

Librebase targets that shape: small Li runtime, strong defaults, and no requirement to adopt a proprietary client to get Auth, REST, and live updates.`,
      },
      {
        heading: "A practical exit path",
        body: `Start managed if you must, but keep schemas, migrations, and agent data access portable. Test restore and reconnect early. Document what is vendor-specific.

When you are ready for a dedicated or shared Librebase instance, [join the waitlist](/#waitlist) or open the [console](/projects).`,
      },
    ],
    faq: [
      {
        question: "Why does vendor lock-in matter for agent networks?",
        answer:
          "Agents amplify API and auth coupling. A vendor change can stall every loop at once.",
      },
      {
        question: "Does Docker prevent lock-in?",
        answer:
          "No. Packaging helps portability of your code, not of proprietary auth or client APIs you hard-coded.",
      },
      {
        question: "What standards help?",
        answer:
          "Postgres-compatible SQL, open HTTP APIs, and thin adapters instead of vendor-only SDKs in the hot path.",
      },
    ],
  },
];

export function getBlogPost(slug: string): BlogPost | undefined {
  return BLOG_POSTS.find((p) => p.slug === slug);
}

export function listBlogPosts(): BlogPost[] {
  return [...BLOG_POSTS].sort((a, b) => b.publishedAt.localeCompare(a.publishedAt));
}
