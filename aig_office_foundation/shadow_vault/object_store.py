from typing import Dict, Any

class ObjectStore:
    """
    Simulated S3/MinIO Object Storage.
    """
    def __init__(self):
        self.storage = {} # object_id -> encrypted_data

    def put_object(self, object_id: str, data: bytes):
        self.storage[object_id] = data

    def get_object(self, object_id: str) -> bytes:
        if object_id not in self.storage:
            raise FileNotFoundError(f"Object {object_id} not found")
        return self.storage[object_id]

    def delete_object(self, object_id: str):
        if object_id in self.storage:
            del self.storage[object_id]
