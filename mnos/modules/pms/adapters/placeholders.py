from mnos.modules.pms.adapters.base_adapter import BasePMSAdapter, CanonicalBooking
import uuid

class OperaAdapter(BasePMSAdapter):
    """Placeholder for Oracle OPERA Cloud/5 PMS."""
    def normalize(self, raw: dict) -> CanonicalBooking:
        return CanonicalBooking(
            source_system="OPERA",
            source_channel=raw.get("res_channel", "DIRECT"),
            external_reservation_id=raw["res_id"],
            property_id=raw["hotel_code"],
            establishment_id=raw.get("org_id", "MIG-MV"),
            guest_ref=raw.get("profile_id"),
            arrival_date=raw["arrival"],
            departure_date=raw["departure"],
            room_type=raw["room_type"],
            room_category=raw.get("room_class", "VILLA"),
            meal_plan=raw.get("rate_plan", "BB"),
            occupancy=raw.get("adults", 1) + raw.get("children", 0),
            base_rate=raw["rate_amount"],
            currency=raw.get("currency", "USD"),
            trace_id=str(uuid.uuid4().hex[:8]),
            booking_status="DRAFT"
        )

class MewsAdapter(BasePMSAdapter):
    """Placeholder for Mews PMS."""
    def normalize(self, raw: dict) -> CanonicalBooking:
         return CanonicalBooking(
            source_system="MEWS",
            source_channel="MEWS_API",
            external_reservation_id=raw["Id"],
            property_id=raw["EnterpriseId"],
            establishment_id="MIG-MV",
            arrival_date=raw["StartUtc"][:10],
            departure_date=raw["EndUtc"][:10],
            room_type=raw["SpaceType"],
            room_category="ROOM",
            meal_plan="RO",
            occupancy=1,
            base_rate=raw["Rate"],
            currency="USD",
            trace_id=str(uuid.uuid4().hex[:8])
        )

class CloudbedsAdapter(BasePMSAdapter):
    """Placeholder for Cloudbeds."""
    def normalize(self, raw: dict) -> CanonicalBooking:
         return CanonicalBooking(
            source_system="CLOUDBEDS",
            source_channel="WEB",
            external_reservation_id=raw["reservationID"],
            property_id=raw["propertyID"],
            establishment_id="MIG-MV",
            arrival_date=raw["checkin"],
            departure_date=raw["checkout"],
            room_type=raw["roomTypeName"],
            room_category="GENERIC",
            meal_plan="RO",
            occupancy=2,
            base_rate=raw["grandTotal"],
            currency="USD",
            trace_id=str(uuid.uuid4().hex[:8])
        )

class WebhookAdapter(BasePMSAdapter):
    """Generic Webhook Adapter for any HMS."""
    def normalize(self, raw: dict) -> CanonicalBooking:
        return CanonicalBooking(**raw)
