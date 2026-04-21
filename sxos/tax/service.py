from typing import Dict, Any

TGST_RATE = 0.17
GGST_RATE = 0.08

def classify_and_calculate_tax(items: list) -> Dict[str, Any]:
    results = []
    total_tax = 0.0

    for item in items:
        base = item.get("price", 0.0)
        category = item.get("category", "cargo")

        if category == "tourism":
            rate = TGST_RATE
            tax_type = "TGST"
        else:
            rate = GGST_RATE
            tax_type = "GGST"

        tax_amount = base * rate
        results.append({
            "name": item.get("name"),
            "base": base,
            "tax_type": tax_type,
            "rate": rate,
            "tax_amount": round(tax_amount, 2)
        })
        total_tax += tax_amount

    return {
        "items": results,
        "total_tax": round(total_tax, 2),
        "mira_reportable": True
    }
