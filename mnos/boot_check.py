import os
import sys

def boot_check():
    """
    MNOS boot integrity check.
    Enforces fail-closed doctrine.
    """
    required_dirs = [
        "mnos/core",
        "mnos/modules/aegis",
        "mnos/modules/finance",
        "mnos/modules/shadow",
        "mnos/modules/events"
    ]

    for d in required_dirs:
        if not os.path.exists(d):
            print(f"CRITICAL ERROR: Missing directory {d}")
            sys.exit(1)

    if "NEXGEN_SECRET" not in os.environ:
        print("CRITICAL ERROR: NEXGEN_SECRET environment variable is missing.")
        sys.exit(1)

    print("MNOS BOOT INTEGRITY: OK")

if __name__ == "__main__":
    boot_check()


# --- eLEGAL EXTENSIONS ---
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
