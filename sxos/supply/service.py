from .alibaba_client import AlibabaMockClient
from typing import Dict, Any

def calculate_landed_cost(base_price: float, shipping_quote: float, duty_rate: float = 0.05):
    # Formula: (Product + Freight) * (1 + Duty) * (1 + TGST)
    landed_base = (base_price + shipping_quote) * (1 + duty_rate)
    landed_with_tgst = landed_base * 1.17

    return {
        "base_price": base_price,
        "shipping": shipping_quote,
        "duty": round(landed_base - base_price - shipping_quote, 2),
        "tgst_landed": round(landed_with_tgst - landed_base, 2),
        "total_landed": round(landed_with_tgst, 2)
    }

def fetch_and_compare_suppliers(query: str) -> Dict[str, Any]:
    ali = AlibabaMockClient()
    results = ali.search_products(query)

    # Simple logic: pick cheapest for demo
    best = min(results, key=lambda x: x["price"])

    return {
        "query": query,
        "best_supplier": "Alibaba",
        "product": best,
        "comparison_count": len(results)
    }
