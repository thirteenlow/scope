CREATE TABLE expenses (
  id UUID PRIMARY KEY,
  employee_id UUID NOT NULL,
  description TEXT NOT NULL,
  category TEXT NOT NULL,
  amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
  currency CHAR(3) NOT NULL DEFAULT 'SGD',
  status TEXT NOT NULL,
  submitted_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE audit_events (
  id UUID PRIMARY KEY,
  entity_id UUID NOT NULL,
  action TEXT NOT NULL,
  actor_id UUID NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

