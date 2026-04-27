import sys
import os
sys.path.append(os.getcwd())
from main import shadow_core
import json

print(f"Chain length: {len(shadow_core.chain)}")
for b in shadow_core.chain:
    print(f"Event: {b['event_type']}")
