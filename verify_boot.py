import sys
import os
sys.path.append(os.getcwd())
try:
    from mnos.interfaces.prestige.main import app
    print("BOOT_SUCCESS")
    for route in app.routes:
        print(f"Path: {route.path}")
except Exception as e:
    print(f"BOOT_FAILURE: {e}")
    import traceback
    traceback.print_exc()
