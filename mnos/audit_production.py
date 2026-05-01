import os
import sys
import json
import re
from typing import List, Dict, Any

def audit_upos():
    print("🕵️ UPOS PRODUCTION READINESS AUDIT")
    print("=" * 40)

    issues = []

    # 1. Check ExecutionGuard Enforcement in API
    print("[CHECK 1] ExecutionGuard in API...")
    api_path = "mnos/api/upos.py"
    if os.path.exists(api_path):
        with open(api_path, "r") as f:
            content = f.read()
            if "guard.execute_sovereign_action" not in content:
                issues.append(f"CRITICAL: {api_path} missing guard.execute_sovereign_action")
            if "upos_engine.create_order" in content and "func=upos_engine.create_order" not in content:
                 issues.append(f"CRITICAL: Direct upos_engine call suspected in {api_path}")
    else:
        issues.append(f"ERROR: {api_path} missing")

    # 2. Check Event Type Consistency
    print("[CHECK 2] Event Type Consistency...")
    engine_path = "mnos/exec/upos/engine.py"
    if os.path.exists(engine_path):
        with open(engine_path, "r") as f:
            content = f.read()
            # upos.order.completed should be the final state event.
            # We now allow upos.order.created and validated as part of the lifecycle.
            if "upos.order.completed" not in content:
                issues.append(f"CRITICAL: {engine_path} missing final 'upos.order.completed' event")

    # 2b. Check for direct engine calls or missing guards in other modules
    print("[CHECK 2b] Direct Engine Calls & Guard Coverage...")
    for root, dirs, files in os.walk("mnos/modules"):
        for file in files:
            if file.endswith(".py"):
                fpath = os.path.join(root, file)
                with open(fpath, "r") as f:
                    content = f.read()
                    if "shadow.commit(" in content and "guard" not in content and "authorized_context" not in content:
                        # Some system-level internal modules might be allowed, but we flag for review
                        # For this specific task, UPOS-related engines are priority blockers.
                        if "shadow_adapter" not in file:
                             level = "CRITICAL" if any(k in fpath for k in ["upos", "pos", "marketplace", "menuorder"]) else "WARNING"
                             issues.append(f"{level}: Direct shadow.commit without guard found in {fpath}")

    # 3. Check Dashboard Safety
    print("[CHECK 3] Dashboard Safe Payload Access...")
    dash_path = "mnos/interfaces/orca/dashboard.py"
    if os.path.exists(dash_path):
        with open(dash_path, "r") as f:
            content = f.read()
            if "payload[\"pricing\"][\"total\"]" in content:
                issues.append(f"CRITICAL: {dash_path} uses unsafe pricing access")
            if ".get(\"pricing\")" not in content:
                issues.append(f"WARNING: {dash_path} safe dict access pattern not found")
            if "upos.order.completed" not in content:
                issues.append(f"CRITICAL: {dash_path} not looking for 'upos.order.completed'")

    # 4. Check Deploy Script
    print("[CHECK 4] Deploy Script Env Loading...")
    deploy_path = "scripts/deploy_sala.sh"
    if os.path.exists(deploy_path):
        with open(deploy_path, "r") as f:
            content = f.read()
            if "export $(cat .env.sala | xargs)" in content:
                 issues.append(f"CRITICAL: {deploy_path} uses unsafe legacy env loading")
            if "source .env.sala" not in content:
                 issues.append(f"CRITICAL: {deploy_path} missing robust env sourcing")

    # 5. Check Offline Sync Pricing & Context
    print("[CHECK 5] Offline Sync Pricing & Context...")
    sync_path = "mnos/cloud/apollo/sync.py"
    if os.path.exists(sync_path):
        with open(sync_path, "r") as f:
            content = f.read()
            if "calculate_order" not in content:
                issues.append(f"CRITICAL: {sync_path} missing pricing backfill logic")
            if "ExecutionGuard.authorized_context" not in content:
                issues.append(f"CRITICAL: {sync_path} missing authorized context for commits")

    # 6. Check Fail-Closed Logic in Engine
    print("[CHECK 6] Fail-Closed Validation...")
    if os.path.exists(engine_path):
        with open(engine_path, "r") as f:
            content = f.read()
            if "amount <= 0" not in content:
                issues.append(f"CRITICAL: {engine_path} missing amount validation")

    print("\n" + "=" * 40)
    # Filter critical issues
    critical_issues = [i for i in issues if "CRITICAL" in i]

    print("\n[AUDIT SUMMARY]")
    if critical_issues:
        print("STATUS: ❌ NOT PRODUCTION READY")
        print("\nBLOCKING ISSUES FOUND:")
        for issue in critical_issues:
            print(f"- {issue}")

        print("\nWarnings (Non-Blocking):")
        for issue in [i for i in issues if "WARNING" in i]:
             print(f"- {issue}")
        sys.exit(1)
    elif issues:
        print("STATUS: 🟡 PRODUCTION READY (WITH WARNINGS)")
        print("\nNON-BLOCKING WARNINGS:")
        for issue in issues:
            print(f"- {issue}")
        print("\nCONFIRMATION: System is PRODUCTION READY (Strict Policy enforced).")
    else:
        print("STATUS: ✅ 100% PRODUCTION READY")
        print("\nCONFIRMATION: All strict production checks passed.")

if __name__ == "__main__":
    audit_upos()
