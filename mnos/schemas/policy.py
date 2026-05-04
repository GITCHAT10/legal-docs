from pydantic import BaseModel
from typing import List

class PolicyMetadataSchema(BaseModel):
    policy_version: str
    active_rules: List[str]
    last_updated: str
