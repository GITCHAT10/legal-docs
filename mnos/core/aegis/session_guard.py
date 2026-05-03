import yaml
from pathlib import Path

class AegisSessionGuard:
    def __init__(self, matrix_path=None):
        if matrix_path is None:
            matrix_path = Path(__file__).resolve().parent / "role_matrix.yaml"
        else:
            matrix_path = Path(matrix_path)

        with matrix_path.open("r", encoding="utf-8") as f:
            self.matrix = yaml.safe_load(f)

    def validate_action(self, actor: dict, event_type: str) -> bool:
        role = actor.get("role", "GUEST")
        role_config = self.matrix["roles"].get(role)

        if not role_config:
            return False

        # 1. Check permissions (simple glob)
        permissions = role_config.get("permissions", [])
        authorized = False
        if "*" in permissions:
            authorized = True
        else:
            for perm in permissions:
                if perm.endswith(".*"):
                    prefix = perm[:-2]
                    if event_type.startswith(prefix):
                        authorized = True
                        break
                elif perm.startswith("*."):
                    suffix = perm[1:]
                    if event_type.endswith(suffix):
                        authorized = True
                        break
                elif perm == event_type:
                    authorized = True
                    break

        if not authorized:
            return False

        # 2. Check AI restrictions
        if role == "AI_AGENT":
            # AI can recommend, prepare, and request only.
            allowed_suffixes = [".RECOMMEND", ".PREPARE", ".REQUEST"]
            if not any(event_type.endswith(s) for s in allowed_suffixes):
                return False

        # 3. Check device requirement
        if role_config.get("requires_device") and not actor.get("device_id"):
            return False

        return True
