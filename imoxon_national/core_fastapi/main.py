from fastapi import FastAPI, HTTPException
import uuid

app = FastAPI(title="iMOXON National Core Engine")

# --- Cross-Role Marketplace Data ---
catalog = {} # id -> product
orders = {}  # id -> order

@app.post("/marketplace/list")
def list_product(item: dict):
    product_id = f"p_{uuid.uuid4().hex[:6]}"
    catalog[product_id] = {
        "id": product_id,
        "seller_role": item.get("role"), # FISHERMAN, FARMER
        "name": item.get("name"),
        "price": item.get("price"),
        "unit": item.get("unit")
    }
    return catalog[product_id]

@app.post("/marketplace/purchase")
def purchase_product(order: dict):
    # Cross-role flow: Farmer -> Hotel -> Export
    product_id = order.get("product_id")
    if product_id not in catalog:
        raise HTTPException(status_code=404, detail="Product not found")

    base = catalog[product_id]["price"] * order.get("quantity")
    tax = base * 0.17 # TGST
    service = base * 0.10 # SC
    total = base + tax + service

    order_id = str(uuid.uuid4())
    orders[order_id] = {
        "id": order_id,
        "product": catalog[product_id],
        "buyer_id": order.get("buyer_id"),
        "total": round(total, 2),
        "status": "SETTLED"
    }
    return orders[order_id]

@app.get("/health")
def health():
    return {"status": "online", "mode": "NATIONAL_DEOS"}
