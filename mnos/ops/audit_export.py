import json
import os
from datetime import datetime, timezone
from mnos.modules.shadow.service import shadow

def export_audit_package(output_dir: str = "AUDIT_EXPORTS"):
    """
    Generates a verifiable, regulator-ready audit package.
    Includes the full SHADOW hash chain, integrity proof, and metadata.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if not shadow.verify_integrity():
        print("!!! SHADOW INTEGRITY FAILURE. ABORTING EXPORT. !!!")
        return None

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    package_name = f"MIG_AUDIT_PACKAGE_{timestamp}"
    package_path = os.path.join(output_dir, f"{package_name}.json")

    # Generate External Anchor
    anchor_id = shadow.generate_external_anchor()

    export_data = {
        "version": "SKY-i Core v1.4",
        "identity": "MALDIVES INTERNATIONAL GROUP (UEI: 2024PV12395H)",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "integrity_status": "VERIFIED_SOVEREIGN",
        "external_anchor_id": anchor_id,
        "ledger_head_hash": shadow.chain[-1]["hash"],
        "chain_length": len(shadow.chain),
        "chain": shadow.chain
    }

    with open(package_path, "w") as f:
        json.dump(export_data, f, indent=2)

    # Generate human-readable manifest
    manifest_path = os.path.join(output_dir, f"{package_name}_MANIFEST.md")
    with open(manifest_path, "w") as f:
        f.write(f"# 🏛️ SOVEREIGN AUDIT MANIFEST\n\n")
        f.write(f"- **Package ID:** {package_name}\n")
        f.write(f"- **Authority:** CEO ASI / MIG-AIGM\n")
        f.write(f"- **Status:** LEGALLY DEFENSIBLE\n")
        f.write(f"- **External Anchor:** `{anchor_id}`\n")
        f.write(f"- **Chain Head:** `{export_data['ledger_head_hash']}`\n")
        f.write(f"\n## Verification Steps\n")
        f.write(f"1. Download the JSON payload.\n")
        f.write(f"2. Run `mnos.verify_integrity()` on the chain.\n")
        f.write(f"3. Match Head Hash against External Anchor Reference.\n")

    print(f"Audit Package Exported: {package_path}")
    return package_path

if __name__ == "__main__":
    export_audit_package()
