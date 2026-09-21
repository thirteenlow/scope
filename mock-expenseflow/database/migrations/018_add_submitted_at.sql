ALTER TABLE expenses ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS idx_expenses_status ON expenses(status);

