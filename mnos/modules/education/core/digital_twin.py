from datetime import datetime, UTC, timedelta
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class SimulationResult(BaseModel):
    student_id: str
    simulation_id: str
    score: float
    competencies_demonstrated: List[str]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

class StudentDigitalTwin(BaseModel):
    student_id: str
    performance_capital: float = 0.0
    mastery_levels: Dict[str, float] = {}  # skill_id -> level (0.0 to 1.0)
    simulation_history: List[SimulationResult] = []
    last_updated: datetime = Field(default_factory=lambda: datetime.now(UTC))

class DigitalTwinEngine:
    """
    Core AI logic for MARS-GLOS Student Digital Twins.
    """

    def __init__(self):
        self.twins: Dict[str, StudentDigitalTwin] = {}

    def ingest_simulation(self, result: SimulationResult) -> StudentDigitalTwin:
        """
        Ingest simulation data and update the Digital Twin.
        """
        # Clamp score to production bounds [0.0, 1.0]
        clamped_score = max(0.0, min(1.0, result.score))

        if result.student_id not in self.twins:
            self.twins[result.student_id] = StudentDigitalTwin(student_id=result.student_id)

        twin = self.twins[result.student_id]
        twin.simulation_history.append(result)

        # Update mastery levels based on simulation result
        for skill in result.competencies_demonstrated:
            current_level = twin.mastery_levels.get(skill, 0.0)
            # Simple adaptive learning logic: weighted average update
            new_level = (current_level * 0.7) + (clamped_score * 0.3)
            # Ensure mastery values stay within [0.0, 1.0]
            twin.mastery_levels[skill] = round(max(0.0, min(new_level, 1.0)), 4)

        # Recalculate Performance Capital
        twin.performance_capital = self._calculate_performance_capital(twin)
        twin.last_updated = datetime.now(UTC)

        return twin

    def predict_pacing(self, student_id: str, target_skill: str) -> Dict[str, Any]:
        """
        Predict student's learning pace to reach mastery in a target skill.
        """
        twin = self.twins.get(student_id)
        if not twin:
            return {"error": "Student not found"}

        current_level = twin.mastery_levels.get(target_skill, 0.0)
        remaining = 1.0 - current_level

        # Predict days based on historical performance (mock logic)
        predicted_days = remaining * 30  # Assuming 30 days for full mastery from 0
        completion_date = datetime.now(UTC) + timedelta(days=predicted_days)

        return {
            "student_id": student_id,
            "target_skill": target_skill,
            "current_level": current_level,
            "predicted_completion": completion_date,
            "confidence_score": 0.85
        }

    def _calculate_performance_capital(self, twin: StudentDigitalTwin) -> float:
        """
        Calculates the aggregate performance capital of a student.
        """
        if not twin.mastery_levels:
            return 0.0
        aggregate = sum(twin.mastery_levels.values()) / len(twin.mastery_levels)
        # Protect performance capital bounds
        return round(max(0.0, min(1.0, aggregate)), 4)
