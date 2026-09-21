# Architecture

ExpenseFlow uses a React web client and a shared REST API. Expense API owns the expense aggregate and publishes domain events. Approval service owns approval steps. Notification service consumes events asynchronously. Finance reporting reads approved expenses from the reporting view.

## Ownership

| Area | Owner |
| --- | --- |
| Web expense flow | Product Engineering |
| Expense domain | Expense Platform |
| Approval policy | Workflow Team |
| Reimbursement | Finance Systems |

The expense service is the source of truth for status. Clients must not infer edit permissions independently.

