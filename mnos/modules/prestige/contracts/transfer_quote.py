from pydantic import BaseModel
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional
from datetime import date, time, datetime, timedelta
from uuid import UUID
import uuid
from mnos.modules.prestige.contracts.transfer_schema import TransferContract, TransferMode
from mnos.modules.prestige.taxes.airport_fees_engine import AirportFeesEngine
from mnos.modules.prestige.taxes.airport_fees_schema import TravelClass, PassengerResidency

class UHNWIntake(BaseModel):
    guest_count_adult: int
    guest_count_child: int
    guest_count_infant: int
    estimated_baggage_kg: float
    oversized_items: List[str] = []
    arrival_airport: str
    arrival_date: date
    arrival_time: time
    international_flight_no: Optional[str] = None
    private_jet_tail_no: Optional[str] = None
    resort_id: str
    destination_atoll: str
    preferred_transfer_mode: str
    vip_cip_required: bool = False
    privacy_level: str
    must_avoid_notes: Optional[str] = None

    # Statutory Fee Inputs
    travel_class: TravelClass
    passenger_residency: PassengerResidency
    is_diplomat: bool = False
    is_transit: bool = False
    is_direct_transit: bool = False

class TransferQuotePreview(BaseModel):
    quote_id: str
    contract_id: UUID
    adult_total: Decimal
    child_total: Decimal
    infant_total: Decimal
    base_subtotal: Decimal
    fuel_supplement: Decimal
    night_surcharge: Decimal
    excess_baggage_cost: Decimal
    total_estimated_cost: Decimal
    currency: str
    warnings: List[str] = []
    tasks: List[Dict[str, Any]] = []
    fce_settlement_estimate: Dict[str, Any] = {}
    airport_fee_breakdown: Dict[str, Any] = {}
    requires_ut_validation: bool = True
    requires_mac_eos_validation: bool = True
    status: str = "PREVIEW_ONLY"

    # Doctrine: UHNW intake may NOT generate confirmed items
    confirmed_ticket: bool = False
    final_invoice_id: Optional[str] = None
    settlement_confirmed: bool = False

def generate_transfer_quote_preview(intake: UHNWIntake, contract: TransferContract) -> TransferQuotePreview:
    """
    PRESTIGE DOCTRINE:
    UHNW intake mapping to transfer quote previews only.
    Final confirmation must route through UT + MAC EOS + UPOS + FCE + SHADOW.
    """

    # 1. Base Costs
    # Use child discount if provided (common for shared speedboat)
    effective_child_rate = contract.child_rate
    if contract.child_discount_pct is not None:
        discount = (contract.adult_rate * contract.child_discount_pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        effective_child_rate = contract.adult_rate - discount

    adult_total = (intake.guest_count_adult * contract.adult_rate).quantize(Decimal("0.01"))
    child_total = (intake.guest_count_child * effective_child_rate).quantize(Decimal("0.01"))
    infant_total = (intake.guest_count_infant * contract.infant_rate).quantize(Decimal("0.01"))

    base_subtotal = adult_total + child_total + infant_total

    # 2. Surcharges (Fuel and Night)
    rules = contract.fuel_surcharge_rule
    fuel_supplement = Decimal("0.00")
    if "fuel_supplement_pct" in rules:
        pct = Decimal(str(rules["fuel_supplement_pct"]))
        fuel_supplement = (base_subtotal * pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    night_surcharge = Decimal("0.00")
    # Night surcharge if after 18:00 (Maldives standard sunset cutoff for some boat routes)
    if intake.arrival_time >= time(18, 0):
        night_surcharge = Decimal(str(rules.get("night_transfer_surcharge", 0.0))).quantize(Decimal("0.01"))

    # 3. Excess Baggage
    # Private charters often have no excess fee but still need capacity check
    is_private = contract.transfer_mode == TransferMode.PRIVATE_CHARTER
    total_allowance = (intake.guest_count_adult + intake.guest_count_child) * contract.baggage_allowance_kg
    excess_kg = max(0.0, intake.estimated_baggage_kg - float(total_allowance))

    excess_baggage_cost = Decimal("0.00")
    if not (is_private and contract.is_unlimited_for_private):
        excess_baggage_cost = (Decimal(str(excess_kg)) * contract.excess_baggage_rate).quantize(Decimal("0.01"))

    total_cost = base_subtotal + fuel_supplement + night_surcharge + excess_baggage_cost

    warnings = []
    if excess_kg > 0:
        warnings.append(f"SHADOW_LUGGAGE_WARNING: Estimated baggage ({intake.estimated_baggage_kg}kg) exceeds allowance ({total_allowance}kg).")
        if is_private:
             warnings.append("UT_FEASIBILITY_REQUIRED: Private charter weight must be verified against vessel capacity.")

    # 4. Tasks
    try:
        arrival_dt = datetime.combine(intake.arrival_date, intake.arrival_time)
        manifest_due = arrival_dt - timedelta(hours=contract.manifest_deadline_hours)
        manifest_due_str = manifest_due.isoformat()
    except Exception:
        manifest_due_str = "CALCULATION_ERROR"

    tasks = [{
        "task_type": "FINALIZE_TRANSFER_MANIFEST",
        "due_at": manifest_due_str,
        "deadline_hours": contract.manifest_deadline_hours
    }]

    # 5. FCE Settlement Impact
    cancel_rules = contract.cancellation_rule
    fce_impact = {
        "cancellation_policy": cancel_rules,
        "potential_loss_24h": float((total_cost * Decimal(str(cancel_rules.get("within_24h", 1.0)))).quantize(Decimal("0.01"))),
        "potential_loss_72h": float((total_cost * Decimal(str(cancel_rules.get("within_72h", 0.5)))).quantize(Decimal("0.01")))
    }

    # 6. Airport Taxes & Fees (Statutory Pass-through)
    fees_engine = AirportFeesEngine()
    airport_fees = fees_engine.calculate_airport_fees(
        travel_class=intake.travel_class,
        residency=intake.passenger_residency,
        departure_airport=intake.arrival_airport, # Assuming departure from arrival for quote
        is_infant=(intake.guest_count_infant > 0),
        is_diplomat=intake.is_diplomat,
        is_transit=intake.is_transit,
        is_direct_transit=intake.is_direct_transit
    )

    # Add to total cost (but keep breakdown separate for pass-through marking)
    # total_cost is carrier cost. Quote preview should show both.
    total_quote_amount = total_cost + Decimal(str(airport_fees["total_airport_fees_usd"]))

    return TransferQuotePreview(
        quote_id=f"TQ-{uuid.uuid4().hex[:8].upper()}",
        contract_id=contract.transfer_contract_id,
        adult_total=adult_total,
        child_total=child_total,
        infant_total=infant_total,
        base_subtotal=base_subtotal,
        fuel_supplement=fuel_supplement,
        night_surcharge=night_surcharge,
        excess_baggage_cost=excess_baggage_cost,
        total_estimated_cost=total_quote_amount,
        currency=contract.currency.value,
        warnings=warnings,
        tasks=tasks,
        fce_settlement_estimate=fce_impact,
        airport_fee_breakdown=airport_fees,
        requires_ut_validation=True,
        requires_mac_eos_validation=True,
        status="PREVIEW_ONLY"
    )
