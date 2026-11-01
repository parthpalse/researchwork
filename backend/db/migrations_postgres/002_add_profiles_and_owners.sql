-- Accounts (Supabase Auth users) and who owns each child. Mirrors db/migrations/006.
CREATE TABLE IF NOT EXISTS profiles (
    user_id TEXT PRIMARY KEY,          -- Supabase auth user id (JWT 'sub')
    email TEXT,
    role TEXT NOT NULL CHECK (role IN ('parent', 'clinician')),
    created_at TEXT NOT NULL DEFAULT (now()::text)
);

-- NULL for children created before accounts existed (visible to clinicians only)
ALTER TABLE children ADD COLUMN IF NOT EXISTS owner_id TEXT;
CREATE INDEX IF NOT EXISTS idx_children_owner ON children(owner_id);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
