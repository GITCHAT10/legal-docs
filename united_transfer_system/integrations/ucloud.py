import os
import logging
from typing import Optional

class UCloudStorage:
    """
    uCloud-backed storage for UT artifacts.
    Provides storage integration for manifests, proof artifacts, and records.
    """
    def __init__(self, root_dir: str = "/mnt/ucloud/united-transfer"):
        self.root_dir = root_dir
        if not os.path.exists(self.root_dir):
            try:
                os.makedirs(self.root_dir, exist_ok=True)
            except Exception as e:
                logging.warning(f"Could not create uCloud root: {e}. Falling back to local temp.")
                self.root_dir = "/tmp/ut_vault"
                os.makedirs(self.root_dir, exist_ok=True)

    def save_artifact(self, filename: str, content: bytes, category: str = "general") -> str:
        """Saves a file to uCloud and returns the path."""
        path = os.path.join(self.root_dir, category, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)
        logging.info(f"Artifact saved to uCloud: {path}")
        return path

ucloud = UCloudStorage()
