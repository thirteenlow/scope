CREATE TABLE accounts (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  balance_cents BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE budget_months (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  month DATE NOT NULL,
  status TEXT NOT NULL DEFAULT 'OPEN',
  UNIQUE(user_id, month)
);

CREATE TABLE category_assignments (
  id UUID PRIMARY KEY,
  budget_month_id UUID NOT NULL REFERENCES budget_months(id),
  category_id UUID NOT NULL,
  assigned_cents BIGINT NOT NULL DEFAULT 0,
  activity_cents BIGINT NOT NULL DEFAULT 0,
  available_cents BIGINT NOT NULL DEFAULT 0,
  UNIQUE(budget_month_id, category_id)
);

CREATE TABLE transactions (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  account_id UUID NOT NULL REFERENCES accounts(id),
  category_id UUID,
  merchant TEXT NOT NULL,
  amount_cents BIGINT NOT NULL,
  occurred_on DATE NOT NULL,
  cleared BOOLEAN NOT NULL DEFAULT false
);

