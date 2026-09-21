# ExpenseFlow

ExpenseFlow is Acme's internal expense management product. Employees capture receipts and submit expenses, managers approve them, and Finance reimburses approved claims.

## Repository map

- `apps/web`: employee and manager React application
- `apps/mobile`: mobile client integration notes
- `services/expense-api`: expense domain and REST API
- `services/approval-service`: approval workflow rules
- `services/notification-service`: notification consumers and templates
- `packages/shared-types`: shared domain contracts
- `database`: schema and migrations
- `docs`: architecture, workflow, and decisions

This repository is intentionally small but structurally realistic. It exists as the “current product” Scope inspects during the demo.

