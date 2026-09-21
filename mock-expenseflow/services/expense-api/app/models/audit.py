from dataclasses import dataclass
from datetime import datetime


@dataclass
class AuditEvent:
    entity_id: str
    action: str
    actor_id: str
    occurred_at: datetime

# Current events intentionally do not store field-level before/after values.

