# Librebase Cursor Automations

Recurring ops run as **[Cursor Automations](https://cursor.com/automations)** (cloud agents). Create each automation in the Cursor UI, attach this repo, and paste the prompt from the matching file.

| Automation | Trigger (suggested) | Prompt file |
|------------|---------------------|-------------|
| **Issue audit** | Mon + Thu 09:00 UTC | [issue-audit.md](./issue-audit.md) |
| **Security audit** | Weekly Mon 10:00 UTC | [security-audit.md](./security-audit.md) |
| **Li port audit** | Weekly Wed 09:00 UTC | [li-port-audit.md](./li-port-audit.md) |

**Do not** add GitHub Actions `schedule:` cron for these — keep Actions minutes for CI.
