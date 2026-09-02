import pytest

from mnos.modules.finance.fce import FCEEngine
from mnos.modules.imoxon.procurement.engine import ProcurementEngine


class Guard:
    def __init__(self):
        self.actor = {"identity_id": "GROUP-CFO", "national_id_verified": True}

    def execute_sovereign_action(self, _action, _ctx, fn, *args):
        return fn(*args)

    def get_actor(self):
        return self.actor


class Events:
    def __init__(self):
        self.events = []

    def publish(self, event_type, payload):
        self.events.append((event_type, payload["id"]))


class Escrow:
    def lock_funds(self, *_args):
        return None

    def release_to_settlement(self, *_args):
        return None


def engine():
    return ProcurementEngine(Guard(), object(), Events(), FCEEngine(), Escrow())


def test_invoice_callable_and_requires_delivery():
    service = engine()
    actor = {"identity_id": "GROUP-CFO"}
    order = service.create_purchase_request(actor, [{"sku": "UT-1", "qty": 1}], 1000)
    with pytest.raises(ValueError, match="INVOICE_REQUIRES_DELIVERED_ORDER"):
        service.finalize_invoice(actor, order["id"])
    service.approve_order(actor, order["id"])
    service.mark_dispatched(actor, order["id"])
    service.mark_delivered(actor, order["id"])
    invoice = service.finalize_invoice(actor, order["id"])
    assert invoice["status"] == "INVOICED"
    assert invoice["pricing"]["tax_rate"] == 0.17
    assert invoice["pricing"]["total"] == 1287.0


def test_invalid_transport_order_transition_fails_closed():
    service = engine()
    actor = {"identity_id": "GROUP-CFO"}
    order = service.create_purchase_request(actor, [], 100)
    with pytest.raises(ValueError, match="INVALID_ORDER_TRANSITION"):
        service.mark_delivered(actor, order["id"])
