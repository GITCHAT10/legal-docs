from enum import Enum

class CommandCenterStatus(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"
    BLACK = "BLACK"

class StatusEngine:
    def __init__(self, shadow):
        self.shadow = shadow
        self.statuses = {} # booking_id -> status

    def update_status(self, booking_id: str, status: CommandCenterStatus):
        self.statuses[booking_id] = status
        self.shadow.commit("prestige.command_center.status_updated", booking_id, {"status": status})

    def get_status(self, booking_id: str) -> CommandCenterStatus:
        return self.statuses.get(booking_id, CommandCenterStatus.GREEN)
