from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..models.schemas import SensorEventRequest, CartResponse, CartItemSchema
from ..models.database import RetailSession, RetailSessionEvent, RetailSessionCartItem, get_db
from ..services.adapters import EVENTSAdapter, SHADOWAdapter
from ..services.security import verify_signed_credentials
from ..services.trust import get_hardware_trust_score, detect_anomalies
from ..events.contracts import EVENT_CART_UPDATED
from typing import List, Dict
from decimal import Decimal
import uuid
from datetime import datetime, timezone

router = APIRouter(dependencies=[Depends(verify_signed_credentials)])

@router.post("/sensor/event")
async def ingest_sensor_event(request: SensorEventRequest, db: Session = Depends(get_db)):
    events = EVENTSAdapter()
    shadow = SHADOWAdapter()

    # 1. Validate active session with row-level locking
    session_record = db.query(RetailSession).with_for_update().filter(RetailSession.id == request.session_id).first()
    if not session_record:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Hardware Trust & Anomaly Detection
    hardware_id = request.source # Simplified: using source as node identifier
    trust_score = await get_hardware_trust_score(db, hardware_id)
    anomaly_flags = await detect_anomalies(db, str(request.session_id), request.model_dump())

    if anomaly_flags:
        current_session_flags = session_record.anomaly_flags or []
        session_record.anomaly_flags = list(set(current_session_flags + anomaly_flags))

    # Degrade confidence based on trust and anomalies
    effective_confidence = request.confidence * trust_score
    if anomaly_flags:
        effective_confidence *= Decimal("0.7")

    # 3. Write session event
    new_event = RetailSessionEvent(
        session_id=request.session_id,
        tenant_id=session_record.tenant_id,
        event_type=request.event_type,
        source=request.source,
        hardware_id=hardware_id,
        product_id=request.product_id,
        qty=request.qty,
        confidence=effective_confidence,
        trust_score_at_event=trust_score,
        payload_json=request.model_dump(mode='json'),
        trace_id=session_record.trace_id
    )
    db.add(new_event)

    # 4. Update live cart
    cart_item = db.query(RetailSessionCartItem).filter(
        RetailSessionCartItem.session_id == request.session_id,
        RetailSessionCartItem.product_id == request.product_id
    ).first()

    if request.event_type == "PICK":
        if cart_item:
            cart_item.qty += request.qty
            cart_item.confidence_score = (cart_item.confidence_score + effective_confidence) / 2
            cart_item.subtotal = cart_item.qty * cart_item.unit_price
            if anomaly_flags:
                current_flags = cart_item.anomaly_flags or []
                cart_item.anomaly_flags = list(set(current_flags + anomaly_flags))
        else:
            unit_price = Decimal("5.00") # Mock price lookup
            cart_item = RetailSessionCartItem(
                session_id=request.session_id,
                product_id=request.product_id,
                qty=request.qty,
                unit_price=unit_price,
                subtotal=unit_price * request.qty,
                price_snapshot={
                    "base_price": float(unit_price),
                    "currency": "USD",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                confidence_score=effective_confidence,
                anomaly_flags=anomaly_flags,
                status="ACTIVE"
            )
            db.add(cart_item)
    elif request.event_type == "PUT":
        if cart_item:
            cart_item.qty -= request.qty
            if anomaly_flags:
                current_flags = cart_item.anomaly_flags or []
                cart_item.anomaly_flags = list(set(current_flags + anomaly_flags))
            if cart_item.qty <= 0:
                db.delete(cart_item)
            else:
                cart_item.subtotal = cart_item.qty * cart_item.unit_price

    db.commit()

    # Fetch full cart for event emission
    full_cart = db.query(RetailSessionCartItem).filter(RetailSessionCartItem.session_id == request.session_id).all()

    # 5. Emit EVENTS.retail.cart_updated
    await events.publish(EVENT_CART_UPDATED, {
        "session_id": str(request.session_id),
        "cart": [
            {
                "product_id": item.product_id,
                "qty": float(item.qty),
                "unit_price": float(item.unit_price),
                "subtotal": float(item.subtotal),
                "confidence_score": float(item.confidence_score),
                "anomaly_flags": item.anomaly_flags
            } for item in full_cart
        ]
    })

    # 6. Commit SHADOW entry
    await shadow.commit({
        "tenant_id": str(session_record.tenant_id),
        "trace_id": str(session_record.trace_id),
        "entity_type": "A_RETAIL_SESSION",
        "entity_id": str(request.session_id),
        "event_type": f"SENSOR_{request.event_type}",
        "payload": {
            "sensor_request": request.model_dump(mode='json'),
            "trust_score": float(trust_score),
            "anomaly_flags": anomaly_flags,
            "effective_confidence": float(effective_confidence)
        }
    })

    return {"status": "SUCCESS"}

@router.get("/session/{session_id}/cart", response_model=CartResponse)
async def get_cart(session_id: uuid.UUID, db: Session = Depends(get_db)):
    cart_items = db.query(RetailSessionCartItem).filter(RetailSessionCartItem.session_id == session_id).all()
    running_total = sum(item.subtotal for item in cart_items)

    items = [
        CartItemSchema(
            product_id=item.product_id,
            qty=float(item.qty),
            unit_price=float(item.unit_price),
            subtotal=float(item.subtotal),
            confidence_score=float(item.confidence_score)
        ) for item in cart_items
    ]

    return CartResponse(
        session_id=session_id,
        items=items,
        running_total=float(running_total)
    )
