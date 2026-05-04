from fastapi import APIRouter
from sxos.supply.service import fetch_and_compare_suppliers, calculate_landed_cost

router = APIRouter(prefix="/sxos/supply")

@router.get("/alibaba/search")
def ali_search(q: str):
    return fetch_and_compare_suppliers(q)

@router.get("/alibaba/product/{id}")
def ali_product(id: str):
    return {"id": id, "name": "Industrial Generator", "price": 1200.0}

@router.post("/alibaba/order")
def ali_order(product_id: str, quantity: int):
    return {"order_id": "ali_123", "status": "PLACED"}

@router.get("/alibaba/supplier_verify")
def ali_verify(supplier_id: str):
    return {"supplier_id": supplier_id, "status": "VERIFIED", "rating": 4.8}
