# Architecture

PocketPlan uses a React web client and a shared REST API. Budget API owns budget months, category assignments and calculated balances. Transaction service imports bank activity and publishes normalized transaction events. Notification service schedules personal bill and goal reminders.

## Ownership

| Area | Owner |
| --- | --- |
| Budget dashboard | Product Engineering |
| Monthly calculation engine | Budget Platform |
| Transaction import | Data Integrations |
| Personal notifications | Platform |

All financial amounts are stored as integer minor units. Budget API is the source of truth for available category balances; clients must not recalculate balances independently.

