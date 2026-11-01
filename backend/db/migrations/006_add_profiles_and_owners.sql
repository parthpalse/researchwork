-- Accounts (Supabase Auth users) and who owns each child.
-- role: 'parent' sees own children; 'clinician' sees all children and can override.
CREATE TABLE IF NOT EXISTS profiles (
    user_id TEXT PRIMARY KEY,          -- Supabase auth user id (JWT 'sub')
    email TEXT,
    role TEXT NOT NULL CHECK (role IN ('parent', 'clinician')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- NULL for children created before accounts existed (visible to clinicians only)
ALTER TABLE children ADD COLUMN owner_id TEXT;
CREATE INDEX IF NOT EXISTS idx_children_owner ON children(owner_id);
