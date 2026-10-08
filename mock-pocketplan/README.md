# PocketPlan

PocketPlan is a personal budgeting app for individuals. A user connects or creates financial accounts, imports transactions, assigns money to spending categories, tracks savings goals, and plans each month before spending.

## Core features

- Cash, bank and credit-card accounts
- Imported and manually entered transactions
- Monthly category budgets
- Spending and available-balance tracking
- Savings goals
- Recurring bills and reminders
- Personal reports and net-worth history

## Repository map

- `apps/web`: React budgeting dashboard
- `apps/mobile`: mobile client notes
- `services/budget-api`: monthly budgets, categories and allocations
- `services/transaction-service`: transaction importing and matching
- `services/notification-service`: personal reminders
- `packages/domain`: shared TypeScript contracts
- `database`: relational schema and migrations
- `docs`: product rules and architecture decisions

This is a deliberately compact but realistic existing product for Scope to inspect.

