# Automation prompt: Librebase open-issue audit

You audit **open work** across Linear, GitHub, and in-repo handoff docs. You triage; you implement only when a finding is a clear one-PR fix (security leak, broken docs claim, missing placeholder).

**Schedule:** Mon + Thu 09:00 UTC · **Repo:** `librebase-official/librebase`

**Skill:** `.cursor/skills/librebase-issue-audit/SKILL.md`

---

## Read first

1. `AGENTS.md`
2. `soul.md`
3. `HANDOFF.md` (open items only — never copy secrets into commits)
4. `.cursor/rules/librebase-product.mdc`

---

## 1. Pull open work

```bash
# Linear (MCP): team LIB, states Backlog / Todo / In Progress / Triage
# GitHub
gh issue list -R librebase-official/librebase --state open --limit 50
gh pr list -R librebase-official/librebase --state open --limit 30
gh issue list -R librebase-official/librebase-saas --state open --limit 20
```

Also skim `docs/agent-onboarding-audit.md` and `docs/audits/` for stale claims vs live prod.

---

## 2. Classify (max one digest per run)

| Bucket | Action |
|--------|--------|
| Security / secret leak | Fix in this PR or open Urgent Linear issue |
| Broken agent/MCP claim | Update docs + file/fix Linear |
| Li-port blocker | Link to `admin-api/li/` progress + cloud-ga PLAN |
| Competitive backlog (LIB-12x) | Leave Backlog unless product asks |
| Done-but-still-open | Close or comment evidence |
| Duplicate | Mark duplicateOf |

Write `docs/audits/YYYY-MM-DD-issue-audit.md` with:

- Counts by source/state
- Top 5 actionable items (priority order)
- Suggested next PR (one sentence)

---

## 3. Linear hygiene

- Create issues only when no LIB-* covers the gap.
- Comment on existing issues with audit date + evidence links.
- Do not mass-close Competitive watch items.

---

## 4. Deliverable

- Audit markdown committed on a feature branch + PR, **or**
- Linear comment digest if no code change needed
