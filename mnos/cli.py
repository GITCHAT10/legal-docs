import sys
import argparse
import os
import uuid
import json
import hmac
import hashlib
from datetime import datetime, timezone
from mnos.core.security.aegis import aegis
from mnos.modules.shadow.service import shadow
from mnos.config import config

class JulesCLI:
    """
    Jules CLI: The Sovereign Command Interface.
    Handles deployment, handshakes, and site initialization.
    """
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Jules CLI: Sovereign Command Interface")
        self.subparsers = self.parser.add_subparsers(dest="command")

        # Deploy command
        deploy_parser = self.subparsers.add_parser("deploy", help="Initialize a site deployment")
        deploy_parser.add_argument("--org", required=True, help="Organization ID (e.g., MIG-AIGM)")
        deploy_parser.add_argument("--site", required=True, help="Site ID (e.g., SALA-FUSHI)")
        deploy_parser.add_argument("--mode", default="SOVEREIGN-SECURE", help="Operation mode")
        deploy_parser.add_argument("--handshake-id", required=True, help="Genesis Handshake ID")
        deploy_parser.add_argument("--ai-core", default="FRIGATE-CORAL-V3", help="AI Core version")
        deploy_parser.add_argument("--auto-mask", choices=["ENABLED", "DISABLED"], default="ENABLED", help="Privacy auto-masking")

    def execute(self, args):
        if args.command == "deploy":
            self.handle_deploy(args)
        else:
            self.parser.print_help()

    def handle_deploy(self, args):
        print(f"--- 🛡️ INITIALIZING SOVEREIGN HANDSHAKE: {args.handshake_id} ---")

        # 1. Hardware-Bound ID Verification (Simulated)
        node_id = f"NODE-{args.site}-001"
        print(f"[Handshake] Verifying local node identity: {node_id}")

        if not aegis.registry.is_trusted(args.handshake_id):
            # In a real scenario, the handshake ID would be in the registry or verifiable
            # For this demo, we check if it matches our bridge ID or a set of known IDs
            if args.handshake_id != "MIG-2026-GENESIS-01":
                print(f"!!! HANDSHAKE FAILURE: UNTRUSTED ID {args.handshake_id} !!!")
                sys.exit(1)

        print(f"[Handshake] Identity Vetted. Activating {args.mode} mode.")

        # 2. Shadow Link: Commit Genesis Handshake to Ledger
        # We manually bypass guard for initial bootstrap if needed, but here we'll use a signed context
        session_payload = {"device_id": node_id, "role": "site_initialization"}
        sig = hmac.new(config.NEXGEN_SECRET.encode(), json.dumps(session_payload, sort_keys=True).encode(), hashlib.sha256).hexdigest()
        session_context = session_payload.copy()
        session_context["signature"] = sig

        print(f"[Shadow] Linking to Global Ledger...")
        try:
            from mnos.shared.execution_guard import guard

            guard.execute_sovereign_action(
                "nexus.security.handshake",
                {
                    "org": args.org,
                    "site": args.site,
                    "handshake_id": args.handshake_id,
                    "mode": args.mode,
                    "ai_core": args.ai_core,
                    "auto_mask": args.auto_mask,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                session_context,
                lambda p: "HANDSHAKE_COMPLETE"
            )

            print(f"[Shadow] Genesis entry sealed. HASH: {shadow.chain[-1]['hash']}")
        except Exception as e:
            print(f"!!! DEPLOYMENT ABORTED: {str(e)} !!!")
            sys.exit(1)

        print(f"\n--- ✅ DEPLOYMENT SUCCESSFUL: {args.site} IS LIVE ---")
        print(f"Privacy Auto-Masking: {args.auto_mask}")
        print(f"Rules of Engagement: SALA-FUSHI-V1 Loaded.")
        print(f"The Moat is Closed.")

if __name__ == "__main__":
    cli = JulesCLI()
    args = cli.parser.parse_args()
    cli.execute(args)
