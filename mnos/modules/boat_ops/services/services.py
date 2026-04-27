from sqlalchemy.orm import Session
from mnos.modules.boat_ops.models import models
from datetime import datetime, UTC
import logging

class CrewService:
    def assign_shift(self, db: Session, crew_id: int, vessel_id: int, start: datetime, end: datetime):
        # Validate license
        crew = db.query(models.CrewMember).filter(models.CrewMember.id == crew_id).first()
        if not crew: return None
        if crew.license_expiry < end.date():
            raise ValueError("License expired or expiring during shift")

        shift = models.CrewShift(
            crew_id=crew_id,
            vessel_id=vessel_id,
            shift_start=start,
            shift_end=end
        )
        shift.ensure_trace_id()
        db.add(shift)
        db.commit()
        return shift

class FuelService:
    def log_fuel(self, db: Session, vessel_id: int, liters: float, atoll: str, logged_by: int):
        # AI Anomaly Detection Logic (Simplified)
        anomaly = False
        if liters > 1000: # Simple threshold for demo
            anomaly = True

        log = models.FuelLog(
            vessel_id=vessel_id,
            liters=liters,
            location_atoll=atoll,
            logged_by=logged_by,
            anomaly_flag=anomaly
        )
        log.ensure_trace_id()
        db.add(log)
        db.commit()

        if anomaly:
            print(f"ALARM: Unusual fuel consumption for vessel {vessel_id} detected.")
        return log

class MaintenanceService:
    def can_dispatch(self, db: Session, vessel_id: int):
        # Check for overdue maintenance
        now = datetime.now(UTC)
        overdue = db.query(models.MaintenanceSchedule).filter(
            models.MaintenanceSchedule.vessel_id == vessel_id,
            models.MaintenanceSchedule.next_due < now,
            models.MaintenanceSchedule.auto_block_dispatch == True
        ).first()

        if overdue:
            return False, f"Overdue maintenance: {overdue.maintenance_type}"
        return True, "Clear"

crew_service = CrewService()
fuel_service = FuelService()
maintenance_service = MaintenanceService()
