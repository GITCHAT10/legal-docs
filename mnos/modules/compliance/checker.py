class ComplianceChecker:
    """
    AEGIS Compliance Checker
    Enforces Maldives regulatory-grade compliance rules.
    """
    def __init__(self):
        self.far_limit = 3.0
        self.ventilation_ratio = 0.10  # 10% of floor area

    def verify_compliance(self, total_floor_area: float, plot_area: float, floor_count: int, rooms_per_floor: int):
        far = total_floor_area / plot_area

        issues = []
        if far > self.far_limit:
            issues.append(f"FAR {far:.2f} exceeds limit {self.far_limit}")

        # 2nd fire exit rule: >3 floors or >6 rooms/floor
        needs_second_fire_exit = floor_count > 3 or rooms_per_floor > 6

        return {
            "compliant": len(issues) == 0,
            "far": far,
            "needs_second_fire_exit": needs_second_fire_exit,
            "issues": issues
        }

compliance = ComplianceChecker()
