# Librebase Studio — Product Design System

Source of truth for the console UI. Brand narrative lives in [BRAND.md](./BRAND.md).
Marketing stays cinematic and dark. Studio is a working tool.

We take Supabase’s **interaction principles**, not their identity.
Accent is forest teal, not mint. Wordmark is Orbitron. Body is Space Grotesk.

## Principles (from the competitive studio, remapped)

1. **Light chrome, dark optional.** The default console is a paper canvas with hairline rules. Dark is a first-class theme, not an inversion hack.
2. **Three-pane workbench.** 48px icon rail → 244px contextual sidebar → fluid canvas. The rail is *where you are*. The sidebar is *what you can do here*.
3. **Quiet accent.** `#1F7A6E` is for primary actions and the live mark. Never flood nav, cards, or status with neon. Running ≠ painted green.
4. **Title, then sentence, then work.** Every surface opens with a 28px title and one muted line of purpose. Controls sit in a toolbar or a settings card — not a pile of buttons.
5. **Active is a pill, not a color.** Selected nav is `surface-muted` with ink text. Color is reserved for the thing you are about to do.
6. **Honest empty.** Paused, missing, and “not built yet” are centered cards with an icon, a fact, and one next step. No skeleton theater.
7. **Hairlines over shadows.** Elevation is a 1px border. Shadows only on overlays (dialogs, menus, notices).
8. **Tokens are the contract.** No hex in components. If a value is not in this file, it does not ship.

## Color

| Token | Light | Dark | Role |
|---|---|---|---|
| `bg` | `#F7F8F7` | `#0C1211` | App canvas |
| `surface` | `#FFFFFF` | `#121A19` | Cards, sidebar, topbar |
| `surface-muted` | `#EEF1EF` | `#1A2322` | Active pills, table header, input fill |
| `text` | `#171C1A` | `#E7F2EC` | Titles, body |
| `text-secondary` | `#5C6662` | `#9BB0AA` | Subtitles, meta |
| `muted` | `#7A847F` | `#7E8E89` | Section labels, placeholders |
| `border` | `#E4E8E5` | `#24302E` | Hairlines |
| `border-strong` | `#C9D0CC` | `#33403D` | Inputs at rest |
| `accent` | `#1F7A6E` | `#2A9A8A` | Primary buttons, links |
| `accent-soft` | `#D8F0EB` | `#16352F` | Soft fill, row hover |
| `accent-on` | `#FFFFFF` | `#071014` | Text on accent |
| `signal` | `#2FD4C2` | `#2FD4C2` | Wordmark spark, live dot only |
| `warn` | `#B45309` | `#E8A838` | Degraded, starting |
| `danger` | `#B42318` | `#F07167` | Destructive |
| `success` | `#1F7A6E` | `#3D9B8A` | Reachable — same family as accent, never a second green |

Marketing tokens (`--lb-ink`, `--lb-paper`, `--lb-signal`) stay on the landing page only.

## Type

| Role | Face | Size / weight |
|---|---|---|
| Wordmark | Orbitron | 14px / 700 / 0.04em |
| Page title | Space Grotesk | 28px / 600 / -0.03em |
| Section title | Space Grotesk | 16px / 600 / -0.01em |
| Sidebar title | Space Grotesk | 16px / 600 |
| Body / control | Space Grotesk | 13–14px / 450 |
| Section label | Space Grotesk | 11px / 600 / 0.08em / uppercase |
| Code / IDs | IBM Plex Mono | 12–13px / 400–500 |

Do not use Orbitron for headings. Do not use a serif in the console.

## Space, radius, motion

- Space: 4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48
- Radius: 4 (badge), 6 (control), 8 (card), 12 (panel)
- Topbar 48 · Rail 48 · Sidebar 244 · Content pad 32×40
- Duration: 140ms micro, 180ms control. Ease: `cubic-bezier(0.22, 1, 0.36, 1)`
- Shadow overlay: `0 16px 48px rgba(23, 28, 26, 0.12)`

## Chrome

**Topbar** — logo, org ▸ project breadcrumbs, Connect, search (⌘K), theme, account.
**Rail** — icon-only, tooltip on hover, grouped, one active item.
**Sidebar** — section title, uppercase groups, text items, `BETA`/`NEW` as 10px pills.
**Canvas** — settings stay ~720px; tables and logs go full bleed.

## Components

- **Button primary** — accent fill, `accent-on` text, 6px radius, 32px tall. Hover darkens 6%.
- **Button default** — surface, 1px border. Hover `surface-muted`.
- **Button ghost** — no border, muted text.
- **Input** — surface-muted fill, strong border, 2px accent ring on focus.
- **Card** — surface, 1px border, 16–20px pad. No drop shadow.
- **Settings row** — title + helper left, control right, hairline between rows.
- **Table** — muted header labels, 40px rows, toolbar above (search, filters, primary right).
- **Badge** — 11px, 999px radius. Status uses border + text, not a filled lozenge.
- **Empty / paused** — max 440px, circular 40px icon, title, 2–4 facts, primary + secondary.

## Copy

Short, operational, no theater.

- Do: “Project is paused. Data is on disk. Start it to query.”
- Don’t: “Your project is taking a nap 💤”
- Do: “No tables in `public`.”
- Don’t: “Nothing to see here yet!”

## Do not

- Use Supabase mint `#3ECF8E` or their logo mark.
- Paint the whole nav in accent.
- Fake a healthy probe with a green badge.
- Put a marketing gradient in the console.
- Use Orbitron beyond the wordmark.
