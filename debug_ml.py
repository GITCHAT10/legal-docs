from main import shadow_core
print(f"Events: {[b['event_type'] for b in shadow_core.chain]}")
