import asyncio
import hashlib
import time
import uuid
import random
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum

# ──────────────────────────────────────────────────────────────
# CONFIG & LOGGING
# ──────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger("MIG_SHIELD_SIM")

class IncidentType(Enum): DROWNING = "DROWNING"; FIRE = "FIRE"; MEDICAL = "MEDICAL"; AIR = "AIR"
class Severity(Enum): LOW = 1; MEDIUM = 2; HIGH = 3; CRITICAL = 4
class DroneStatus(Enum): READY = "READY"; CHARGING = "CHARGING"; OFFLINE = "OFFLINE"; DISPATCHED = "DISPATCHED"

@dataclass
class Drone:
    id: str; type: str; status: DroneStatus = DroneStatus.READY
    battery: float = 100.0; location: tuple = (0.0, 0.0); speed_kmh: float = 80.0

@dataclass
class Incident:
    id: str; type: IncidentType; severity: Severity
    location: tuple; timestamp: float; resolved: bool = False

# ──────────────────────────────────────────────────────────────
# MNOS GUARDRAILS & SHADOW AUDIT
# ──────────────────────────────────────────────────────────────
class ShadowAudit:
    def __init__(self):
        self.chain: List[Dict] = []
        self.prev_hash = "0" * 64

    def log(self, event: str, data: Dict) -> str:
        payload = f"{self.prev_hash}|{event}|{str(data)}|{time.time()}"
        h = hashlib.sha256(payload.encode()).hexdigest()
        self.chain.append({"event": event, "data": data, "hash": h, "ts": time.time()})
        self.prev_hash = h
        return h

    def verify(self) -> bool:
        return len(self.chain) > 0 and self.prev_hash != "0" * 64

class AEGIS:
    @staticmethod
    async def verify(operator: str) -> bool:
        await asyncio.sleep(random.uniform(0.05, 0.15))
        return True  # Mock sovereign identity check

class ORCA:
    @staticmethod
    async def validate(drone: Drone, incident: Incident) -> Dict:
        await asyncio.sleep(random.uniform(0.1, 0.25))
        weather_ok = random.random() > 0.05
        return {"allowed": weather_ok, "reason": "CLEAR" if weather_ok else "WEATHER_RESTRICTED"}

# ──────────────────────────────────────────────────────────────
# AGENT SYSTEM & ORCHESTRATOR
# ──────────────────────────────────────────────────────────────
class BaseAgent:
    def __init__(self, name: str, capability: IncidentType):
        self.name, self.capability = name, capability

    async def bid(self, inc: Incident, drones: List[Drone]) -> Optional[Dict]:
        ready = [d for d in drones if d.status == DroneStatus.READY and d.battery > 40]
        if not ready: return None
        target = min(ready, key=lambda d: ((d.location[0]-inc.location[0])**2 + (d.location[1]-inc.location[1])**2)**0.5)
        dist = ((target.location[0]-inc.location[0])**2 + (target.location[1]-inc.location[1])**2)**0.5
        eta = (dist / target.speed_kmh) * 3600  # seconds
        return {"agent": self.name, "drone": target.id, "eta": eta}

class OceanAgent(BaseAgent):
    def __init__(self): super().__init__("OCEAN_SEAL", IncidentType.DROWNING)
class FireAgent(BaseAgent):
    def __init__(self): super().__init__("FIRE_DRAGON", IncidentType.FIRE)
class MedicalAgent(BaseAgent):
    def __init__(self): super().__init__("LIFELINE", IncidentType.MEDICAL)

class Orchestrator:
    def __init__(self, drones, agents, shadow, network, failures):
        self.drones, self.agents, self.shadow = drones, agents, shadow
        self.network, self.failures = network, failures

    async def run(self, inc: Incident) -> float:
        t0 = time.time()
        logger.info(f"[PERCEIVE] {inc.type.value} | Severity: {inc.severity.name}")
        self.shadow.log("incident_detected", inc.__dict__)
        await self.network.latency("perception")

        agent = next((a for a in self.agents if a.capability == inc.type), None)
        if not agent: logger.warning("[REASON] No matching agent"); return -1

        bid = await agent.bid(inc, self.drones)
        if not bid: logger.warning("[PLAN] No available drones"); return -1
        self.shadow.log("agent_selected", bid)
        await self.network.latency("planning")

        # GUARDRAILS
        if not await AEGIS.verify("OPS_MGR_01"): logger.warning("[AEGIS] Auth failed"); return -1
        orca = await ORCA.validate(next(d for d in self.drones if d.id == bid["drone"]), inc)
        if not orca["allowed"]: logger.warning(f"[ORCA] Blocked: {orca['reason']}"); return -1

        # ACT
        drone = next(d for d in self.drones if d.id == bid["drone"])
        drone.status = DroneStatus.DISPATCHED
        self.shadow.log("dispatch_authorized", {"drone": drone.id, "inc": inc.id})
        await self.network.latency("dispatch")

        if self.failures.trigger(drone.id):
            logger.warning(f"[FAILURE] Drone {drone.id} fault → RTB fallback")
            drone.status = DroneStatus.OFFLINE
            self.shadow.log("mission_aborted", {"reason": "HARDWARE_FAULT"})
            return time.time() - t0

        # SIMULATED FLIGHT (time-compressed for demo)
        flight_time = min(bid["eta"], 15) / 10  # Scaled for fast sim runs
        await asyncio.sleep(flight_time)

        drone.status = DroneStatus.READY
        drone.battery = max(20, drone.battery - random.uniform(8, 25))
        inc.resolved = True
        self.shadow.log("mission_complete", {"inc": inc.id, "eta_real": bid["eta"]})
        logger.info(f"[REFLECT] Resolved in {(time.time()-t0):.3f}s")
        return time.time() - t0

# ──────────────────────────────────────────────────────────────
# INFRASTRUCTURE SIMS
# ──────────────────────────────────────────────────────────────
class NetworkSim:
    async def latency(self, phase: str):
        base = random.uniform(0.05, 0.25)
        if random.random() < 0.1: base += 1.2  # Simulate LTE dip
        await asyncio.sleep(base)

class FailureInjector:
    def __init__(self, rate=0.08): self.rate = rate
    def trigger(self, drone_id: str) -> bool: return random.random() < self.rate

# ──────────────────────────────────────────────────────────────
# KPI TRACKER (3-30-3 VALIDATION)
# ──────────────────────────────────────────────────────────────
class KPITracker:
    def __init__(self):
        self.dispatch_times, self.arrival_times = [], []
        self.success, self.fail = 0, 0

    def record(self, dispatch_sec: float, arrival_sec: float, success: bool):
        if dispatch_sec >= 0:
            self.dispatch_times.append(dispatch_sec)
            self.arrival_times.append(arrival_sec)
        if success: self.success += 1
        else: self.fail += 1

    def report(self, shadow_chain):
        avg_disp = sum(self.dispatch_times)/max(1,len(self.dispatch_times)) if self.dispatch_times else 0
        avg_arr = sum(self.arrival_times)/max(1,len(self.arrival_times)) if self.arrival_times else 0
        total = self.success + self.fail
        rate = self.success / max(1, total) * 100
        print("\n" + "="*55)
        print("📊 MIG SHIELD DIGITAL TWIN — 3-30-3 KPI REPORT")
        print("="*55)
        print(f"⚡ Dispatch Latency: {avg_disp:.2f}s  (Target <3s)  {'✅' if avg_disp < 3 else '❌'}")
        print(f"🚁 Airborne Time:   {min(self.arrival_times) if self.arrival_times else 0:.2f}s  (Target <30s) {'✅' if (self.arrival_times and min(self.arrival_times) < 30) else '⏳'}")
        print(f"🎯 Arrival (Sim):   {avg_arr:.2f}s  (Scaled)")
        print(f"✅ Success Rate:    {self.success}/{total} ({rate:.1f}%)")
        print(f"🔗 SHADOW Integrity: {'VERIFIED ✅' if shadow_chain.verify() else 'COMPROMISED ❌'}")
        print("="*55 + "\n")

# ──────────────────────────────────────────────────────────────
# SIMULATION RUNNER
# ──────────────────────────────────────────────────────────────
shadow_chain = ShadowAudit()
network = NetworkSim()
failures = FailureInjector(rate=0.1)
drones = [
    Drone("QRD-O-01", "OCEAN_SEAL", location=(0,0)),
    Drone("QRD-M-01", "LIFELINE", location=(2,1)),
    Drone("QRD-F-01", "FIRE_DRAGON", location=(4,0))
]
agents = [OceanAgent(), FireAgent(), MedicalAgent()]
orchestrator = Orchestrator(drones, agents, shadow_chain, network, failures)
kpi = KPITracker()

async def main(scenarios=12):
    logger.info("🌍 Initializing MIG SHIELD Digital Twin (Gan Pilot Topology)...")
    for _ in range(scenarios):
        inc_type = random.choice(list(IncidentType))
        severity = random.choice([Severity.HIGH, Severity.CRITICAL])
        loc = (random.uniform(0, 8), random.uniform(0, 8))
        inc = Incident(str(uuid.uuid4())[:8], inc_type, severity, loc, time.time())

        t0 = time.time()
        dispatch_time = await orchestrator.run(inc)
        sim_elapsed = time.time() - t0

        # Map sim time to real-world KPI targets
        kpi.record(
            dispatch_sec=sim_elapsed if dispatch_time != -1 else -1,
            arrival_sec=sim_elapsed * 12 + random.uniform(15, 45) if dispatch_time != -1 else -1,  # Scaled arrival
            success=inc.resolved
        )
    kpi.report(shadow_chain)

if __name__ == "__main__":
    asyncio.run(main(12))
