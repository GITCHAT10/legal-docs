import sys
import os

# Ensure PYTHONPATH includes /app
sys.path.append(os.getcwd())

from mnos.modules.telemetry.report_generator import report_generator
from mnos.modules.shadow.service import shadow

def generate_final_telemetry():
    print("--- 📊 MSOG FINAL TELEMETRY GENERATION ---")

    # Ensure there is some data in shadow
    if len(shadow.chain) == 0:
        print("Warning: Shadow chain is empty. Generating placeholder data...")
        # In a real scenario we'd run a simulation first

    case_id = "MSOG-GENESIS-FINAL"
    report = report_generator.generate_case_report(
        case_id=case_id,
        include_fields=["EVENT_TIMELINE", "METRICS", "FORENSIC_AUDIT"]
    )

    print(f"Report Generated for Case: {case_id}")
    print(f"Integrity Status: {report['forensic_audit']['integrity_status']}")
    print(f"Shadow Root: {report['forensic_audit']['shadow_merkle_root']}")
    print("--- ✅ TELEMETRY COMPLETE ---")

if __name__ == "__main__":
    generate_final_telemetry()
