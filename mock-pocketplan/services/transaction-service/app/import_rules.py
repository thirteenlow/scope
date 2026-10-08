from dataclasses import dataclass


@dataclass
class ImportRule:
    merchant_contains: str
    category_id: str


def categorize(merchant: str, rules: list[ImportRule]) -> str | None:
    normalized = merchant.casefold()
    match = next((rule for rule in rules if rule.merchant_contains.casefold() in normalized), None)
    return match.category_id if match else None

