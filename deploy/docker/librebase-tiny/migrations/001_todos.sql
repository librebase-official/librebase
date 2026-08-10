CREATE TABLE IF NOT EXISTS todos (
  id TEXT PRIMARY KEY,
  user_id TEXT,
  title TEXT,
  done TEXT DEFAULT 'false',
  created_at TEXT
);
