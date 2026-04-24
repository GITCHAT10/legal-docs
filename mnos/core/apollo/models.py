from dataclasses import dataclass
from typing import Optional

@dataclass
class DeploymentRecord:
    artifact: str
    env: str
    status: str
    attestation_id: Optional[str] = None
