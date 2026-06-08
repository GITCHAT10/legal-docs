import yaml
import os
from typing import Dict, Any, Optional, List

class ChannelConfigLoader:
    def __init__(self, config_path: str = "config/channels/prestige_channels.yaml"):
        self.config_path = config_path
        self.channels: Dict[str, Dict[str, Any]] = {}
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Channel configuration file not found at {self.config_path}")

        with open(self.config_path, "r") as f:
            data = yaml.safe_load(f)
            self.channels = data.get("channels", {})

    def get_channel_config(self, channel_id: str) -> Optional[Dict[str, Any]]:
        return self.channels.get(channel_id)

    def is_channel_enabled(self, channel_id: str) -> bool:
        config = self.get_channel_config(channel_id)
        if not config:
            return False
        return config.get("enabled", False)

    def get_enabled_channels(self) -> List[str]:
        return [cid for cid, cfg in self.channels.items() if cfg.get("enabled", False)]
