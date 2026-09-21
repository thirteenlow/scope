# Expense workflow

1. An employee creates a draft.
2. The employee may edit any draft field.
3. On submission, Expense API validates policy and changes the status to `SUBMITTED`.
4. Submission immediately requests the first manager approval step.
5. Manager approval moves the expense to `FINANCE_REVIEW`.
6. Finance approval moves it to `APPROVED` and makes it eligible for reimbursement.
7. A successful payment moves it to `PAID`.

## Alternate transitions

- Manager or Finance may reject to `REJECTED`.
- Finance may return an expense to a new draft only through an administrative action.
- Failed payments remain `APPROVED` and enter the retry queue.

Submitted records are immutable today. This protects the exact payload seen by an approver, but forces employees to ask Finance to correct minor mistakes.

