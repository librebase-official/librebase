-- Login attempt tracking + account lockout (console auth)
CREATE TABLE IF NOT EXISTS login_attempts (
  email TEXT PRIMARY KEY,
  failed_count INTEGER NOT NULL DEFAULT 0,
  last_failed_at TEXT,
  locked_until TEXT
);
