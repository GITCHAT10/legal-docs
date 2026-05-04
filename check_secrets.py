import os
import sys

def check_file(path, secret_env):
    with open(path, 'r') as f:
        content = f.read()

    has_raise = "raise RuntimeError" in content
    has_fallback = "os.getenv(" in content and "," in content.split("os.getenv(")[1].split(")")[0]

    print(f"File: {path}")
    print(f"  Strict Raise Implemented: {'YES' if has_raise else 'NO'}")
    print(f"  Fallback Found: {'YES' if has_fallback else 'NO'}")

check_file('mnos/security.py', 'MNOS_INTEGRATION_SECRET')
check_file('skyfarm/integration/service.py', 'SKYFARM_INTEGRATION_SECRET')
