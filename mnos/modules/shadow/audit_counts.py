from mnos.modules.shadow.service import shadow
from mnos.core.events.service import events

def get_counts():
    # shadow count
    s_count = len(shadow.chain) - 1 # exclude genesis

    # event count simulation (tracking stress events)
    e_count = 0
    for entry in shadow.chain:
        if entry["event_type"].startswith("event_") or entry["event_type"] == "safe.event":
            e_count += 1

    return e_count, s_count
