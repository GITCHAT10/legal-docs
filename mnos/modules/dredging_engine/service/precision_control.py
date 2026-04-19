from ..models.telemetry import DredgepackData

class PrecisionMonitor:
    def __init__(self, precision_tolerance: float = 0.01): # 1cm tolerance
        self.precision_tolerance = precision_tolerance

    def verify_position(self, data: DredgepackData, target_x: float, target_y: float) -> dict:
        error_x = abs(data.precision_x - target_x)
        error_y = abs(data.precision_y - target_y)

        within_tolerance = error_x <= self.precision_tolerance and error_y <= self.precision_tolerance

        return {
            "within_tolerance": within_tolerance,
            "error_x": error_x,
            "error_y": error_y,
            "z_depth": data.z_depth
        }
