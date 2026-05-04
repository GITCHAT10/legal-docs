from sqlalchemy.orm import Session
from .models import RestaurantOrderModel
from skyfarm.integration.outbox_service import queue_event
import uuid
import json

def create_restaurant_order(db: Session, facility_id: str, items: list, total_amount: float, tenant_id: str):
    order = RestaurantOrderModel(
        id=f"res_{uuid.uuid4().hex[:8]}",
        facility_id=facility_id,
        items_json=items,
        total_amount=total_amount
    )
    db.add(order)

    # Queue event
    queue_event(db, tenant_id, "restaurant.order.created", {
        "order_id": order.id,
        "total_amount": total_amount,
        "items": items
    })

    db.commit()
    db.refresh(order)
    return order
