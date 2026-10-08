PRODUCT_FEATURES = [
    {
        "id": "monthly-budgets",
        "name": "Monthly category budgets",
        "summary": "Assign personal income to categories and track assigned, activity and available amounts each month.",
        "category": "Budgeting",
        "status": "Available",
        "capabilities": [
            "Category assignments",
            "Available-to-assign",
            "Overspending indicators",
        ],
        "evidence_paths": [
            "services/budget-api/app/routes/budgets.py",
            "apps/web/src/features/budget/BudgetMonth.tsx",
        ],
        "accent": "violet",
    },
    {
        "id": "accounts",
        "name": "Personal accounts",
        "summary": "Track cash, bank and credit-card accounts with balances isolated to each individual user.",
        "category": "Money",
        "status": "Available",
        "capabilities": [
            "Cash accounts",
            "Bank accounts",
            "Credit cards",
        ],
        "evidence_paths": [
            "database/schema.sql",
            "packages/domain/src/index.ts",
        ],
        "accent": "blue",
    },
    {
        "id": "transactions",
        "name": "Transaction tracking",
        "summary": "Import or enter purchases, assign categories and keep cleared and pending activity visible.",
        "category": "Transactions",
        "status": "Available",
        "capabilities": [
            "Bank imports",
            "Manual entries",
            "Merchant matching",
        ],
        "evidence_paths": [
            "services/transaction-service/app/import_rules.py",
            "database/schema.sql",
        ],
        "accent": "orange",
    },
    {
        "id": "savings-goals",
        "name": "Savings goals",
        "summary": "Set a personal target and receive a suggested monthly contribution based on the remaining time.",
        "category": "Goals",
        "status": "Available",
        "capabilities": [
            "Target amount",
            "Target date",
            "Suggested contribution",
        ],
        "evidence_paths": [
            "services/budget-api/app/services/allocation.py",
        ],
        "accent": "green",
    },
    {
        "id": "bill-reminders",
        "name": "Recurring bill reminders",
        "summary": "Receive a personal reminder before recurring bills are due and see upcoming commitments.",
        "category": "Planning",
        "status": "Available",
        "capabilities": [
            "Due-date reminders",
            "Recurring bills",
            "Personal notifications",
        ],
        "evidence_paths": [
            "services/notification-service/app/handlers.py",
        ],
        "accent": "pink",
    },
    {
        "id": "reports",
        "name": "Personal spending reports",
        "summary": "Review spending by category and understand changes in personal account balances over time.",
        "category": "Insights",
        "status": "Available",
        "capabilities": [
            "Category trends",
            "Monthly comparisons",
            "Net-worth history",
        ],
        "evidence_paths": [
            "docs/architecture.md",
            "database/schema.sql",
        ],
        "accent": "cyan",
    },
]