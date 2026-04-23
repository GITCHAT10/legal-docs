from typing import List, Dict, Any
import hashlib

class MerkleTree:
    """
    CHRONOS Merkle: Proof of Inclusion.
    Builds trees for event epochs to provide inclusion proofs.
    """
    def build_tree(self, leaves: List[str]) -> str:
        """Builds a simple Merkle tree and returns the root."""
        if not leaves:
            return ""
        if len(leaves) == 1:
            return leaves[0]

        new_level = []
        for i in range(0, len(leaves), 2):
            left = leaves[i]
            right = leaves[i+1] if i+1 < len(leaves) else left
            combined = hashlib.sha256((left + right).encode()).hexdigest()
            new_level.append(combined)

        return self.build_tree(new_level)

merkle_engine = MerkleTree()
