import csv
import io
import uuid
from typing import List, Optional
from datetime import datetime
from mnos.modules.prestige.flight_matrix.models import FlightConnectivityRecord

class FlightConnectivityLoader:
    def __init__(self, core_system):
        self.core = core_system
        self.records: List[FlightConnectivityRecord] = []
        self.version = "1.0.0"

    def load_from_csv(self, actor_ctx: dict, csv_content: str):
        """
        Loads flight connectivity data from a CSV string.
        Doctrine: No hardcoded live dependency, validate fields, normalize codes, seal to SHADOW.
        """
        f = io.StringIO(csv_content)
        reader = csv.DictReader(f)

        imported_records = []
        errors = []

        for row in reader:
            try:
                # Basic validation & normalization
                flight_num = row.get("flight_number", "").strip().upper()
                airline = row.get("airline_code", "").strip().upper()
                arrival_time = row.get("scheduled_arrival_time_mle", "").strip()

                if not flight_num or not airline or not arrival_time:
                     errors.append(f"Missing required fields in row: {row}")
                     continue

                record = FlightConnectivityRecord(
                    market_region=row.get("market_region", "GLOBAL"),
                    origin_country=row.get("origin_country", "UNKNOWN"),
                    origin_city=row.get("origin_city", "UNKNOWN"),
                    origin_airport=row.get("origin_airport", "UNKNOWN").upper(),
                    airline_code=airline,
                    flight_number=flight_num,
                    arrival_airport=row.get("arrival_airport", "MLE").upper(),
                    scheduled_arrival_time_mle=arrival_time,
                    estimated_arrival_time_mle=row.get("estimated_arrival_time_mle"),
                    average_delay_minutes=int(row.get("average_delay_minutes", 0)),
                    delay_risk_level=row.get("delay_risk_level", "LOW"),
                    baggage_risk=row.get("baggage_risk", "LOW"),
                    weather_risk=row.get("weather_risk", "LOW")
                )
                imported_records.append(record)
            except Exception as e:
                errors.append(f"Error parsing row {row}: {str(e)}")

        if imported_records:
            self.records = imported_records
            self.version = datetime.now().strftime("%Y%m%d.%H%M%S")

            # SHADOW Seal
            actor_id = actor_ctx.get("identity_id", "SYSTEM")
            self.core.shadow.commit("prestige.flight_matrix.dataset_imported", actor_id, {
                "version": self.version,
                "record_count": len(imported_records),
                "error_count": len(errors),
                "trace_id": uuid.uuid4().hex
            })

        return {"status": "success", "imported": len(imported_records), "errors": errors, "version": self.version}

    def get_record(self, flight_number: str) -> Optional[FlightConnectivityRecord]:
        for r in self.records:
            if r.flight_number == flight_number:
                return r
        return None
