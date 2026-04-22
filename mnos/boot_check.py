import os
import sys

def check_integrity():
    critical_dirs = [
        "mnos/core",
        "mnos/modules/aegis",
        "mnos/modules/layout",
        "mnos/modules/finance",
        "mnos/modules/shadow",
        "mnos/modules/events"
    ]
    for d in critical_dirs:
        if not os.path.exists(d):
            print(f"CRITICAL ERROR: Missing directory {d}")
            sys.exit(1)

    if not os.getenv("NEXGEN_SECRET"):
        print("CRITICAL ERROR: NEXGEN_SECRET environment variable not set.")
        sys.exit(1)

    print("MNOS Boot Integrity Check: PASSED")

if __name__ == "__main__":
    check_integrity()
