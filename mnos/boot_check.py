import os
import sys

def check_integrity():
    """Checks for MNOS CORE directory structure. Fails closed if missing."""
    critical_paths = [
        "mnos",
        "mnos/config.py",
        "mnos/modules/fce/service.py",
        "mnos/modules/shadow/service.py"
    ]

    missing = []
    for path in critical_paths:
        if not os.path.exists(path):
            missing.append(path)

    if missing:
        print(f"!!! SYSTEM HALT: Persistence Failure !!!")
        print(f"Missing critical components: {missing}")
        # Fail closed
        sys.exit(1)

    print("--- 🏛️ MNOS BOOT INTEGRITY: OK ---")
    return True

if __name__ == "__main__":
    check_integrity()
