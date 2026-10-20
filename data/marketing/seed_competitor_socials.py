#!/usr/bin/env python3
"""
Seed competitor_socials table in librebase_competitive.db.

Adds Twitter/X, LinkedIn, blog, YouTube, and newsletter URLs per competitor.
Run once: python3 seed_competitor_socials.py
"""

import os
import sqlite3
from datetime import date

DB = os.environ.get(
    "LIBREBASE_COMPETITIVE_DB",
    os.path.expanduser("~/Documents/coding-projects/librebase/librebase_competitive.db"),
)

SOCIALS = {
    # name: [(platform, handle, url, is_tracked), ...]
    "Supabase": [
        ("twitter", "@supabase", "https://twitter.com/supabase", 1),
        ("linkedin", "Supabase", "https://linkedin.com/company/supabase", 1),
        ("blog", "Supabase Blog", "https://supabase.com/blog", 1),
        ("github", "supabase/supabase", "https://github.com/supabase/supabase", 1),
        ("reddit", "r/supabase", "https://reddit.com/r/supabase", 1),
        ("youtube", "Supabase", "https://youtube.com/@supabase", 0),
        ("newsletter", "Supabase Chronicles", "https://supabase.com/newsletter", 1),
    ],
    "Appwrite": [
        ("twitter", "@appwrite_io", "https://twitter.com/appwrite_io", 1),
        ("linkedin", "Appwrite", "https://linkedin.com/company/appwrite", 1),
        ("blog", "Appwrite Blog", "https://appwrite.io/blog", 1),
        ("github", "appwrite/appwrite", "https://github.com/appwrite/appwrite", 1),
        ("reddit", "r/appwrite", "https://reddit.com/r/appwrite", 1),
    ],
    "Firebase": [
        ("twitter", "@firebase", "https://twitter.com/firebase", 1),
        ("blog", "Firebase Blog", "https://blog.firebase.com", 1),
        ("github", "firebase", "https://github.com/firebase", 1),
        ("youtube", "Google Firebase", "https://youtube.com/firebase", 0),
    ],
    "PocketBase": [
        ("twitter", "@pocketbase_io", "https://twitter.com/pocketbase_io", 1),
        ("blog", "PocketBase Blog", "https://pocketbase.io/blog", 1),
        ("github", "pocketbase/pocketbase", "https://github.com/pocketbase/pocketbase", 1),
        ("reddit", "r/pocketbase", "https://reddit.com/r/pocketbase", 1),
    ],
    "Nhost": [
        ("twitter", "@nhost_io", "https://twitter.com/nhost_io", 1),
        ("linkedin", "Nhost", "https://linkedin.com/company/nhost", 1),
        ("blog", "Nhost Blog", "https://nhost.io/blog", 1),
        ("github", "nhost/nhost", "https://github.com/nhost/nhost", 1),
        ("reddit", "r/nhost", "https://reddit.com/r/nhost", 0),
    ],
    "Directus": [
        ("twitter", "@directuscms", "https://twitter.com/directuscms", 1),
        ("linkedin", "Directus", "https://linkedin.com/company/directus", 1),
        ("blog", "Directus Insights", "https://directus.io/insights/", 1),
        ("github", "directus/directus", "https://github.com/directus/directus", 1),
    ],
    "Xano": [
        ("twitter", "@xano", "https://twitter.com/xano", 1),
        ("linkedin", "Xano", "https://linkedin.com/company/xano", 1),
        ("blog", "Xano Blog", "https://xano.com/blog", 1),
        ("github", "xano", "https://github.com/xano", 0),
    ],
    "Railway": [
        ("twitter", "@railway_app", "https://twitter.com/railway_app", 1),
        ("linkedin", "Railway", "https://linkedin.com/company/railway", 1),
        ("blog", "Railway Blog", "https://railway.app/blog", 1),
        ("github", "railwayapp", "https://github.com/railwayapp", 1),
        ("reddit", "r/railway", "https://reddit.com/r/railway", 1),
    ],
    "Render": [
        ("twitter", "@render", "https://twitter.com/render", 1),
        ("linkedin", "Render", "https://linkedin.com/company/render", 1),
        ("blog", "Render Blog", "https://render.com/blog", 1),
        ("github", "render", "https://github.com/render", 0),
    ],
    "Fly.io": [
        ("twitter", "@flydotio", "https://twitter.com/flydotio", 1),
        ("linkedin", "Fly.io", "https://linkedin.com/company/flydotio", 1),
        ("blog", "Fly.io Blog", "https://fly.io/blog", 1),
        ("github", "superfly/flyctl", "https://github.com/superfly/flyctl", 1),
        ("reddit", "r/flyio", "https://reddit.com/r/flyio", 1),
    ],
    "Heroku": [
        ("twitter", "@heroku", "https://twitter.com/heroku", 1),
        ("linkedin", "Heroku", "https://linkedin.com/company/heroku", 1),
        ("blog", "Heroku Blog", "https://heroku.com/blog", 1),
        ("github", "heroku", "https://github.com/heroku", 1),
    ],
    "AWS Amplify": [
        ("twitter", "@awsamplify", "https://twitter.com/awsamplify", 1),
        ("linkedin", "AWS Amplify", "https://linkedin.com/company/aws-amplify", 1),
        ("blog", "AWS Amplify Blog", "https://aws.amazon.com/blogs/aws/category/amplify/", 1),
        ("github", "aws-amplify", "https://github.com/aws-amplify", 1),
    ],
    "Koywe": [
        ("twitter", "@koywe", "https://twitter.com/koywe", 1),
        ("linkedin", "Koywe", "https://linkedin.com/company/koywe", 1),
        ("blog", "Koywe Blog", "https://koywe.com/blog", 1),
    ],
    "Convex": [
        ("twitter", "@convex_dev", "https://twitter.com/convex_dev", 1),
        ("linkedin", "Convex", "https://linkedin.com/company/convex-dev", 1),
        ("blog", "Convex Blog", "https://convex.dev/blog", 1),
        ("github", "convex-dev/convex", "https://github.com/convex-dev/convex", 1),
        ("reddit", "r/convex", "https://reddit.com/r/convex", 0),
    ],
    "Vercel": [
        ("twitter", "@vercel", "https://twitter.com/vercel", 1),
        ("linkedin", "Vercel", "https://linkedin.com/company/vercel", 1),
        ("blog", "Vercel Blog", "https://vercel.com/blog", 1),
        ("github", "vercel/next.js", "https://github.com/vercel/next.js", 1),
        ("youtube", "Vercel", "https://youtube.com/@vercel", 0),
    ],
    "Cloudflare Workers": [
        ("twitter", "@CloudflareDev", "https://twitter.com/CloudflareDev", 1),
        ("linkedin", "Cloudflare", "https://linkedin.com/company/cloudflare", 1),
        ("blog", "Cloudflare Developers Blog", "https://developers.cloudflare.com/blog/", 1),
        ("github", "cloudflare", "https://github.com/cloudflare", 1),
    ],
    "Retool": [
        ("twitter", "@retool", "https://twitter.com/retool", 1),
        ("linkedin", "Retool", "https://linkedin.com/company/retool", 1),
        ("blog", "Retool Blog", "https://retool.com/blog", 1),
        ("github", "retool", "https://github.com/retool", 1),
    ],
    "Baseten": [
        ("twitter", "@basetenai", "https://twitter.com/basetenai", 1),
        ("linkedin", "Baseten", "https://linkedin.com/company/baseten", 1),
        ("blog", "Baseten Blog", "https://baseten.com/blog", 1),
        ("github", "baseten", "https://github.com/baseten", 1),
    ],
    "LangChain": [
        ("twitter", "@langchainai", "https://twitter.com/langchainai", 1),
        ("linkedin", "LangChain", "https://linkedin.com/company/langchain", 1),
        ("blog", "LangChain Blog", "https://blog.langchain.com", 1),
        ("github", "langchain-ai/langchain", "https://github.com/langchain-ai/langchain", 1),
        ("reddit", "r/langchain", "https://reddit.com/r/langchain", 1),
        ("youtube", "LangChain", "https://youtube.com/@langchain", 0),
        ("discord", "LangChain Discord", "https://discord.gg/langchain", 1),
    ],
    "OpenAI Agents": [
        ("twitter", "@OpenAI", "https://twitter.com/OpenAI", 1),
        ("linkedin", "OpenAI", "https://linkedin.com/company/openai", 1),
        ("blog", "OpenAI Blog", "https://openai.com/blog", 1),
        ("github", "openai", "https://github.com/openai", 1),
        ("youtube", "OpenAI", "https://youtube.com/@openai", 0),
        ("discord", "OpenAI Discord", "https://discord.com/invite/openai", 1),
    ],
    "Anthropic": [
        ("twitter", "@AnthropicAI", "https://twitter.com/AnthropicAI", 1),
        ("linkedin", "Anthropic", "https://linkedin.com/company/anthropic-ai", 1),
        ("blog", "Anthropic News", "https://anthropic.com/news", 1),
        ("github", "anthropic", "https://github.com/anthropic", 1),
        ("youtube", "Anthropic", "https://youtube.com/@anthropic", 0),
    ],
    "ElevenLabs": [
        ("twitter", "@elevenlabsio", "https://twitter.com/elevenlabsio", 1),
        ("linkedin", "ElevenLabs", "https://linkedin.com/company/elevenlabs", 1),
        ("blog", "ElevenLabs Blog", "https://elevenlabs.io/blog", 1),
        ("github", "elevenlabs", "https://github.com/elevenlabs", 1),
        ("youtube", "ElevenLabs", "https://youtube.com/@elevenlabs", 0),
    ],
    "HuggingFace": [
        ("twitter", "@huggingface", "https://twitter.com/huggingface", 1),
        ("linkedin", "Hugging Face", "https://linkedin.com/company/hugging-face", 1),
        ("blog", "HuggingFace Blog", "https://huggingface.co/blog", 1),
        ("github", "huggingface", "https://github.com/huggingface", 1),
        ("youtube", "HuggingFace", "https://youtube.com/@huggingface", 0),
        ("discord", "HuggingFace Discord", "https://discord.com/invite/huggingface", 1),
    ],
    "Nango": [
        ("twitter", "@nango_io", "https://twitter.com/nango_io", 1),
        ("linkedin", "Nango", "https://linkedin.com/company/nango", 1),
        ("blog", "Nango Blog", "https://nango.dev/blog", 1),
        ("github", "NangoHQ/nango", "https://github.com/NangoHQ/nango", 1),
    ],
    "Merge.dev": [
        ("twitter", "@merge_dev", "https://twitter.com/merge_dev", 1),
        ("linkedin", "Merge.dev", "https://linkedin.com/company/merge-dev", 1),
        ("blog", "Merge.dev Blog", "https://merge.dev/blog", 1),
        ("github", "merge-dev", "https://github.com/merge-dev", 1),
    ],
    "Sequin": [
        ("twitter", "@sequin_io", "https://twitter.com/sequin_io", 1),
        ("linkedin", "Sequin", "https://linkedin.com/company/sequin-io", 1),
        ("blog", "Sequin Blog", "https://sequin.io/blog", 1),
        ("github", "sequin-io", "https://github.com/sequin-io", 1),
        ("reddit", "r/sequin", "https://reddit.com/r/sequin", 0),
    ],
    "Neon": [
        ("twitter", "@neon_db", "https://twitter.com/neon_db", 1),
        ("linkedin", "Neon", "https://linkedin.com/company/neon-tech", 1),
        ("blog", "Neon Blog", "https://neon.tech/blog", 1),
        ("github", "neon-tissue/neon", "https://github.com/neon-tissue/neon", 1),
        ("reddit", "r/neon_db", "https://reddit.com/r/neon_db", 1),
    ],
    "ElectricSQL": [
        ("twitter", "@electricsql", "https://twitter.com/electricsql", 1),
        ("linkedin", "ElectricSQL", "https://linkedin.com/company/electricsql", 1),
        ("blog", "ElectricSQL Blog", "https://electric-sql.com/blog", 1),
        ("github", "electric-sql/electric", "https://github.com/electric-sql/electric", 1),
    ],
    "Azure Static Web Apps": [
        ("twitter", "@Azure", "https://twitter.com/Azure", 1),
        ("linkedin", "Microsoft Azure", "https://linkedin.com/company/microsoft-azure", 1),
        ("blog", "Azure Blog", "https://azure.microsoft.com/en-us/blog/", 1),
    ],
    "LoRA": [
        ("twitter", "@lora_company", "https://twitter.com/lora_company", 0),
        ("github", "lora", "https://github.com/lora", 0),
    ],
    "PowerDNS": [
        ("twitter", "@PowerDNS", "https://twitter.com/PowerDNS", 1),
        ("linkedin", "PowerDNS", "https://linkedin.com/company/powerdns", 1),
        ("blog", "PowerDNS Blog", "https://powerdns.com/blog/", 1),
        ("github", "PowerDNS/pdns", "https://github.com/PowerDNS/pdns", 1),
    ],
}


def seed():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    # Create table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS competitor_socials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competitor_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            handle TEXT,
            url TEXT,
            is_tracked INTEGER DEFAULT 1,
            last_check TEXT,
            FOREIGN KEY (competitor_id) REFERENCES competitors(id) ON DELETE CASCADE
        )
    """)

    # Build competitor name → id map
    name_to_id = dict(conn.execute("SELECT name, id FROM competitors").fetchall())

    added = 0
    skipped = 0
    for name, socials in SOCIALS.items():
        cid = name_to_id.get(name)
        if not cid:
            print(f"  ⚠ {name} — not in competitors table, skip")
            skipped += 1
            continue

        for platform, handle, url, is_tracked in socials:
            # Dedupe
            existing = conn.execute(
                "SELECT id FROM competitor_socials WHERE competitor_id=? AND platform=?",
                (cid, platform),
            ).fetchone()
            if existing:
                # Update URL if changed
                conn.execute(
                    "UPDATE competitor_socials SET url=?, handle=?, is_tracked=? WHERE id=?",
                    (url, handle, is_tracked, existing["id"]),
                )
                skipped += 1
                continue

            conn.execute(
                "INSERT INTO competitor_socials (competitor_id, platform, handle, url, is_tracked) VALUES (?, ?, ?, ?, ?)",
                (cid, platform, handle, url, is_tracked),
            )
            added += 1

    conn.commit()
    conn.close()

    print(f"✅ Seeded competitor_socials:")
    print(f"   Added: {added}")
    print(f"   Skipped (already exists / unknown competitor): {skipped}")
    print(f"   Total rows now: {added + skipped}")

    # Verify
    vconn = sqlite3.connect(DB)
    vconn.row_factory = sqlite3.Row
    total = vconn.execute("SELECT COUNT(*) FROM competitor_socials").fetchone()[0]
    tracked = vconn.execute("SELECT COUNT(*) FROM competitor_socials WHERE is_tracked=1").fetchone()[0]
    platforms = vconn.execute("SELECT DISTINCT platform FROM competitor_socials").fetchall()
    print(f"\n   Verification:")
    print(f"   Total socials: {total}")
    print(f"   Tracked: {tracked}")
    print(f"   Platforms: {[p['platform'] for p in platforms]}")
    vconn.close()


if __name__ == "__main__":
    seed()
