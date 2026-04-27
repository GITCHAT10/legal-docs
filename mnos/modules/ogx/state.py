from mnos.modules.ogx.schemas import OGXState

class OGXStateMachine:
    def __init__(self, initial_state: OGXState = OGXState.OPTIMAL):
        self.current_state = initial_state

    def transition(self, new_state: OGXState):
        """
        Handles state transitions.
        In a real scenario, this would include validation logic
        (e.g., cannot go from FAIL-STOP to OPTIMAL without recovery).
        """
        self.current_state = new_state
        return self.current_state

    def is_optimal(self) -> bool:
        return self.current_state == OGXState.OPTIMAL

    def is_degraded(self) -> bool:
        return self.current_state == OGXState.DEGRADED

    def is_fail_stop(self) -> bool:
        return self.current_state == OGXState.FAIL_STOP
