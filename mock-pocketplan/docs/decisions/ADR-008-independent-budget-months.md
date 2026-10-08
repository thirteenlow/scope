# ADR-008: Budget months are independent

Status: Accepted

Each month stores its own assignments and activity. Creating a new month inserts zero-value category rows instead of copying available balances from the previous month. This keeps historical reports stable and makes month calculations easy to reproduce.

Any rollover feature must define treatment for positive balances, overspending, deleted categories and late-arriving transactions. Historical months must remain immutable after they are closed.

