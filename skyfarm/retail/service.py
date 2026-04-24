from sqlalchemy.orm import Session
from .models import RetailSaleModel
from skyfarm.integration.outbox_service import queue_event
import uuid
import json

def record_retail_sale(db: Session, store_id: str, items: list, total_amount: float, tenant_id: str):
    sale = RetailSaleModel(
        id=f"ret_{uuid.uuid4().hex[:8]}",
        store_id=store_id,
        items_json=items,
        total_amount=total_amount
    )
    db.add(sale)

    # Queue event
    queue_event(db, tenant_id, "retail.sale.recorded", {
        "sale_id": sale.id,
        "total_amount": total_amount,
        "items": items
    })

    db.commit()
    db.refresh(sale)
    return sale
