import hashlib
import json

class HashChain:
    def __init__(self, genesis_hash: str = "0" * 64):
        self.last_hash = genesis_hash

    def calculate_hash(self, block_data: dict) -> str:
        data_str = json.dumps(block_data, sort_keys=True)
        combined = f"{self.last_hash}{data_str}".encode()
        return hashlib.sha256(combined).hexdigest()

    def update(self, new_hash: str):
        self.last_hash = new_hash
