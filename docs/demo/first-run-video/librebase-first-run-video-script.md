# Librebase first-run film — scene script (v1)

**Job:** Sign up. Name a project. Link an agent. Two minutes. No hustle.

**Cut:** v1, 2026-08-20 — 43.2s, 1280×720, 25fps, silent, H.264  
**File:** `Documents/coding-projects/librebase-first-run.mp4`  
**Linear:** [LIB-14](https://linear.app/librebase/issue/LIB-14/north-star-signup-first-project-link-agents-no-hustle)  
**Product:** [app.librebase.xyz/login](https://app.librebase.xyz/login)

v1 is a **Ken Burns still-cut**, not a live mouse screencast. Cinematic plates are Imagine stills with a slow push-in. Product frames are a live capture of `/login` plus HTML mocks of New project and Connect an agent (the Imagine video API was blocked on this team — no `upload_url`). There is **no VO** yet. Recut from this script, not from memory.

Storyboard: `storyboard.html` in this folder.

---

## Shot list

| # | Time | Dur | Kind | Plate | On screen | Purpose |
|---|------|-----|------|-------|-----------|---------|
| 01 | 0:00–0:04 | 4.0s | Cine | Teal spark in a dark rack hall | *none* | Hook. Signal in the void. |
| 02 | 0:04–0:07.6 | 3.6s | Card | Title | **NO HUSTLE** / Sign up. Start a project. Link your agents. / Two minutes from first login to an agent that can see your project. | Promise. |
| 03 | 0:07.6–0:10.8 | 3.2s | Cine | Night desk, laptop glow | *none* | Human in the loop. |
| 04 | 0:10.8–0:15.0 | 4.2s | UI | Live `/login` | Librebase · Sign in · GitHub / Google / email · “Start a project. Link your agents. Two minutes.” | Proof the product exists. |
| 05 | 0:15.0–0:17.6 | 2.6s | Card | Beat 01 | **01 — SIGN IN** / You’re in. / GitHub, Google, or email. No operator console. No waitlist dead-end. | US-1. |
| 06 | 0:17.6–0:20.2 | 2.6s | Card | Beat 02 | **02 — PROJECT** / Name it. That’s the form. / We provision in the background. You do not pick a VM, a region, or a cluster. | US-2. |
| 07 | 0:20.2–0:24.2 | 4.0s | UI | New project | Name: `north-star` · Create project. Sidebar: Projects / New project / Settings. | The form is one field. |
| 08 | 0:24.2–0:27.4 | 3.2s | Cine | Teal fiber through glass | *none* | Connection coming alive. |
| 09 | 0:27.4–0:30.6 | 3.2s | Card | Beat 03 | **03 — AGENTS** / Paste a snippet. Ask “what’s in my project?” / Cursor, Claude, Grok — remote MCP URL, key already filled. | US-3. |
| 10 | 0:30.6–0:35.6 | 5.0s | UI | Connect an agent | Warming up — you can still link an agent. Cursor tab + JSON `{ url: https://app.librebase.xyz/mcp }`. Copy Cursor snippet. | The paste. Longest product hold. |
| 11 | 0:35.6–0:39.0 | 3.4s | Cine | Agent orbs into a core | *none* | Agents arriving. |
| 12 | 0:39.0–0:43.2 | 4.2s | Card | End | Libre**base** / The database your agents already know. / `app.librebase.xyz` | Close. |

Fades: 0.35s in / 0.35s out on every shot. Slow zoom `1.00 → ~1.10`.

---

## Suggested VO (not in v1 — add for v2)

Keep it under 90 words. Calm, present tense. Do not say “operator”, “Kubernetes”, or “MCP server”.

| Time | Line |
|------|------|
| 0:00 | *(silence, or a single low tone under the spark)* |
| 0:04 | “Sign up. Start a project. Link your agents.” |
| 0:11 | “GitHub, Google, or email. You’re in.” |
| 0:18 | “Name the project. That’s the form.” |
| 0:28 | “Paste the snippet into Cursor, Claude, or Grok.” |
| 0:31 | “Then ask: what’s in my project?” |
| 0:39 | “Librebase. The database your agents already know.” |

Alt close (more product, less poetry): “Two minutes. No hustle. app.librebase.xyz.”

---

## Locked copy (cards)

Do not paraphrase on a recut unless the product changed. These lines are the north star.

1. Sign up. Start a project. Link your agents.
2. Two minutes from first login to an agent that can see your project.
3. You’re in. — No operator console. No waitlist dead-end.
4. Name it. That’s the form. — You do not pick a VM, a region, or a cluster.
5. Paste a snippet. Ask “what’s in my project?”
6. The database your agents already know.

Wordmark: Libre + *base* in signal teal `#2FD4C2`. Ink `#071014`. Body Space Grotesk. Mark Orbitron.

---

## Sources (v1)

| Plate | How it was made |
|-------|-----------------|
| Cine 01, 03, 08, 11, 12-bg | Imagine stills, 16:9. No logos, no letters in the plate. |
| Cards 02, 05, 06, 09, 12 | `cards.html` — HTML/CSS so the type is exact. Screenshot at 1280×720. |
| UI 04 | Headless Chrome against local Studio `/login` (same copy as prod). |
| UI 07, 10 | `product-mocks.html` matching Studio chrome. Connect panel uses a masked key `lb_mcp_••••`. |

Compose: Ken Burns each still → concat. See `compose.sh` once restored next to this file.

---

## How to recut

1. Edit this script first. Lock times, on-screen, VO.
2. Change card copy in `cards.html`, screenshot `?id=card-open` (and the other ids).
3. For a real screencast: record `/login` → `/projects/new` → project home Connect panel at 1280×720, dark theme, no notifications. Replace shots 04, 07, 10.
4. Re-run `compose.sh` (durations in that file must match the table above).
5. If adding VO: record 48kHz mono, mix `-filter_complex "[0:v][1:a]concat"` or a separate narration bed. Hold shot 10 at ≥5s so “paste the snippet” can land.

Chrome stills:

```bash
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$CHROME" --headless=new --disable-gpu --hide-scrollbars --window-size=1280,720 \
  --virtual-time-budget=4000 --screenshot=stills/card-open.png \
  "file://$PWD/cards.html?id=card-open"
```

---

## v2 backlog (improve from here)

Priority order for the next cut:

1. **Live screencast of the happy path** — replace mocked 07/10 with a real session: type `north-star`, click Create, land on Connect, copy the Cursor snippet. Cursor in the shot if we can do it without leaking a live key.
2. **VO take** — table above. One voice, dry, no music bed until VO is locked.
3. **Real motion on cine plates** — Imagine `image_to_video` when the team has an `upload_url`. Keep stills as frame 1 so grade doesn’t drift.
4. **Tighten cards** — 05 and 06 at 2.6s are fast if VO is added; give them 3.2s each and steal from cine 08/11.
5. **Show the agent answering** — 4s after shot 10: a coding-agent pane saying the project name and `org_whoami`. That’s the proof shot v1 does not have.
6. **End card CTA** — keep `app.librebase.xyz`. Optional: “Continue with GitHub” as a still of the real button, not a fake pill.
7. **16:9 and 9:16** — this cut is 16:9 only. Social needs a 9:16 recrop of 01, 02, 10, 12.

Out of this film: VMs, clusters, on-prem, pricing, benchmarks. Those are other scripts.

---

## Honest gaps in v1

- No mouse, no typing, no cursor highlight.
- Shots 07 and 10 are product-accurate mocks, not a logged-in session.
- Silent — the title cards carry the story.
- Cine plates are stills with zoom, not generated video.
- No agent-response payoff.
