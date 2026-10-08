ALTER TABLE budget_months ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'OPEN';
CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, occurred_on);

