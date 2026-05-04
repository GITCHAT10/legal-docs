import os
import sys

def boot_check():
    """
    MNOS boot integrity check.
    Enforces fail-closed doctrine.
    """
    required_dirs = [
        "mnos/core",
        "mnos/core/aegis",
        "mnos/core/shadow",
        "mnos/core/events",
        "mnos/core/fce",
        "mnos/modules/redcoral",
        "mnos/modules/buildx",
        "mnos/modules/atollx"
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
