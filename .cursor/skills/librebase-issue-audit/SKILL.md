---
name: librebase-issue-audit
description: Audit Librebase open issues from Linear (LIB), GitHub, and HANDOFF. Use when triaging backlog, starting a Librebase agent run, or writing an issue digest.
---

# Librebase issue audit

## Sources

1. Linear MCP — team `LIB` / `Librebase`
2. `gh issue list -R librebase-official/librebase --state open`
3. `gh pr list -R librebase-official/librebase --state open`
4. `HANDOFF.md` open items (strip secrets)

## Output

Write `docs/audits/YYYY-MM-DD-issue-audit.md`:

```markdown
# Issue audit YYYY-MM-DD
## Summary
## Linear (open)
## GitHub (open)
## HANDOFF debt
## Top actions
## Done this run
```

## Rules

- Competitive `LIB-12x` watch items stay Backlog unless product asks.
- Prefer updating existing LIB-* over creating duplicates.
- Never paste live credentials into issues or commits.
