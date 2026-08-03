# Design System: Librebase
**Project ID:** af1f6d03-4b45-4cb5-8276-548cfacd71ee

## 1. Visual Theme & Atmosphere
Librebase expresses a professional personality with a Sage-led identity supported by Outlaw.

Narrative anchor: We help Developers, platform teams, and agent builders who need a Postgres-compatible backend with a small footprint, honest health status, and MCP/REST APIs — not fake-green SaaS dashboards. with Librebase — High-performance Postgres-compatible database written in Li — low memory, strong security defaults, Auth/REST/Realtime for teams and agents.. Edit this to reflect your brand story.

Positioning intent: No direct competitors were identified in this niche and the following establishes a first-mover position based on the brand profile. We build Librebase for developers platform teams and agent builders who require a Postgres-compatible backend with minimal memory usage. This solution delivers strong security defaults through built-in authentication rest APIs and real-time syncs without relying on fake-green SaaS dashboards.

Our focus remains on honest health status indicators that reflect true infrastructure costs rather than obscured metrics common in managed backends. We prioritize open standards including MCP integration to prevent vendor lockin while maintaining high performance for regulated industries where transparency matters most. The architecture runs entirely within the Li language to ensure a small footprint and robust security out of the box without requiring external plugins or heavy overhead.

Librebase positions itself as an agent-first data layer that simplifies SQL management while eliminating hidden costs associated with proprietary client libraries. This approach empowers teams to own their infrastructure fully instead of depending on ready-made templates created by other vendors. We deliver a secure scalable and transparent foundation for the next generation of autonomous agents and collaborative workspaces without compromise. The single takeaway for how this brand positions as first mover is its commitment to honest metrics low memory usage and full control over agent data flows.

## 2. Color Palette & Roles
- **Background (#ffffff)**: Base canvas and long-form reading areas.
- **Background Muted (#f4f4f5)**: Subtle section fills and low-emphasis surfaces.
- **Primary Text (#0a0a0a)**: Default text color for headings and body content.
- **Secondary Text (#52525b)**: Supportive labels, metadata, and helper copy.
- **Accent (#495d36)**: Primary actions, links, highlighted states, and key emphasis.
- **Accent On (#fafafa)**: Foreground text/icon color used on top of accent surfaces.
- **Accent Muted (#2e3a21)**: Hover, pressed, and secondary accent interactions.
- **Border (#e4e4e7)**: Strokes, dividers, and input outlines.

Dark-theme anchor colors include Background (#0a0a0a), Text (#fafafa), and Accent (#495d36).

## 3. Typography Rules
Headlines use **IBM Plex Sans** to create a recognizable top-level voice and strong hierarchy.
Body copy uses **IBM Plex Serif** for readability across long-form and UI microcopy.
Use heavier weight for section titles and medium/regular weights for supporting copy to preserve contrast.

## 4. Component Stylings
* **Buttons:** Primary buttons are accent-led (background #495d36, foreground #fafafa) with clearly readable contrast.
* **Cards/Containers:** Surfaces use #f4f4f5 with subtle border separation (#e4e4e7) to maintain structure without visual noise.
* **Inputs/Forms:** Inputs use quiet borders, clear focus states in accent tones, and high-legibility text treatment.

## 5. Layout Principles
Favor generous spacing between sections, keep core actions visually prominent, and maintain consistent alignment in multi-column and stacked layouts.
Use muted backgrounds for grouping and reserve accent intensity for actions, links, and high-priority information.

## 6. Spacing & Radius Scale
- **Spacing:** xs 4px, sm 8px, md 16px, lg 24px, xl 40px, 2xl 56px.
- **Radius:** sm 4px, md 8px, lg 12px, full 9999px.

## 7. Elevation & Motion
- **Elevation sm:** 0 1px 2px rgba(0,0,0,0.06)
- **Elevation md:** 0 4px 12px rgba(0,0,0,0.08)
- **Elevation lg:** 0 12px 32px rgba(0,0,0,0.12)
- **Duration micro:** `140ms`
- **Duration fast:** `200ms`
- **Duration normal:** `320ms`
- **Duration emphasis:** `600ms`
- **Duration choreography:** `2800ms`
- **Easing standard:** `cubic-bezier(0.22, 1, 0.36, 1)`
- **Easing expressive:** `cubic-bezier(0.16, 1, 0.3, 1)`
- **Stagger sibling:** `100ms`
- **Stagger stream:** `280ms`
- **Hold readable:** `1200ms`
