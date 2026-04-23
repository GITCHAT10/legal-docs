import sys
import os

# Ensure PYTHONPATH
sys.path.append(os.getcwd())

from mnos.interfaces.sala_os.prototype.entry import ui_entry
from mnos.interfaces.sala_os.api.bindings import sala_api
from mnos.interfaces.sala_os.security.guard import sala_guard
from mnos.interfaces.sala_os.deployment import ui_deployment
from mnos.core.security.aegis import aegis

def validate_sala_os_deployment():
    print("--- 🏛️ SALA-OS UI INTERFACE VALIDATION ---")

    # 1. Security Context
    ctx = {"device_id": "nexus-001"}
    ctx["signature"] = aegis.sign_session(ctx)

    # 2. Build & Serve
    ui_deployment.build_optimized_dashboard()
    res = ui_deployment.serve_interface(ctx)

    if res["status"] == "MOUNTED":
        print(f" -> UI successfully mounted at {res['path']}")
    else:
        raise RuntimeError("UI Mounting Failed")

    # 3. Component Rendering
    render_out = ui_entry.render()
    print(f" -> Dashboard State: {render_out['status']} | Layout: {render_out['layout']}")

    # 4. API Connectivity
    print("\n[BINDING CHECK]")
    sala_api.fetch_data("arrivals")
    sala_api.fetch_data("mail")

    # 5. Security Rejection (Spoof attempt)
    print("\n[SECURITY ATTACK SIMULATION]")
    try:
        bad_ctx = {"device_id": "spoof-001"}
        # No signature or bad signature
        sala_guard.validate_ui_session(bad_ctx)
        print("FAILED: Spoof accepted.")
    except Exception as e:
        print(f"SUCCESS: System blocked unauthorized access: {e}")

    print("\n--- ✅ SALA-OS UI VALIDATION COMPLETE ---")

if __name__ == "__main__":
    validate_sala_os_deployment()
