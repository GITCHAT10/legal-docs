import uuid
from typing import Dict, Any, List, Optional
from mnos.modules.prestige.models import TripMasterObject
from mnos.modules.prestige.channel.channel_config_loader import ChannelConfigLoader
from mnos.modules.prestige.channel.auth_gateway import AuthGateway
from mnos.modules.prestige.channel.inventory_mapper import InventoryMapper
from mnos.modules.prestige.channel.rate_sync_engine import RateSyncEngine
from mnos.modules.prestige.channel.availability_sync_engine import AvailabilitySyncEngine
from mnos.modules.prestige.channel.reservation_validator import ReservationValidator
from mnos.modules.prestige.channel.restriction_manager import RestrictionManager
from mnos.modules.prestige.channel.webhook_receiver import WebhookReceiver
from mnos.modules.prestige.channel.channel_audit import ChannelAuditService

class AgentRegistry:
    def __init__(self):
        self.agents = {}

    def register_agent(self, agent_id: str, agent_instance: Any, agent_type: str):
        self.agents[agent_id] = {
            "instance": agent_instance,
            "type": agent_type
        }

    def get_agent(self, agent_type: str):
        for agent in self.agents.values():
            if agent["type"] == agent_type:
                return agent["instance"]
        return None

class TripService:
    def __init__(self, core_system):
        self.core = core_system
        self.trips: Dict[str, TripMasterObject] = {}

    def build_provisional_trip(self, planner_id: str) -> TripMasterObject:
        trip_id = f"PRSTG-{uuid.uuid4().hex[:6].upper()}"
        trip = TripMasterObject(
            trip_id=trip_id,
            planner_id=planner_id
        )
        self.trips[trip_id] = trip
        return trip

    def get_trip(self, trip_id: str) -> Optional[TripMasterObject]:
        return self.trips.get(trip_id)

class PrestigeCore:
    def __init__(self, guard, shadow, events=None, orca=None):
        self.guard = guard
        self.shadow = shadow
        self.events = events
        self.orca = orca

        self.channel_config = ChannelConfigLoader()
        self.auth_gateway = AuthGateway(self)
        self.inventory_mapper = InventoryMapper(self)
        self.rate_sync = RateSyncEngine(self)
        self.availability_sync = AvailabilitySyncEngine(self)
        self.reservation_validator = ReservationValidator(self)
        self.restriction_manager = RestrictionManager(self)
        self.webhook_receiver = WebhookReceiver(self)
        self.channel_audit = ChannelAuditService(self)

        self.agent_registry = AgentRegistry()
        self.trip_service = TripService(self)
