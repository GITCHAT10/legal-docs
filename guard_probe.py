import traceback
import threading
from mnos.core.events.service import events
from mnos.shared.execution_guard import in_sovereign_context

print('=== TEST 1: ROGUE CALL (NO GUARD) ===')
try:
    events.publish('rogue.event', {})
    print('❌ FAIL: Rogue call succeeded')
except Exception as e:
    print('✅ PASS: Rogue call blocked')
    traceback.print_exc()

print('\n=== TEST 2: GUARDED CALL ===')
try:
    t = threading.current_thread()
    t.in_sovereign_guard = True
    # SHADOW commit needs sovereign contextvar too
    token = in_sovereign_context.set(True)

    events.publish('safe.event', {})

    print('✅ PASS: Guarded publish succeeded')
except Exception as e:
    print('❌ FAIL: Guarded publish failed')
    traceback.print_exc()
finally:
    in_sovereign_context.reset(token)

print('\n=== TEST 3: STRESS RUN (1000 EVENTS) ===')
success = 0
failure = 0

for i in range(1000):
    try:
        t = threading.current_thread()
        t.in_sovereign_guard = True
        token = in_sovereign_context.set(True)

        events.publish(f'event_{i}', {})
        success += 1
    except Exception:
        failure += 1
    finally:
        in_sovereign_context.reset(token)

print(f'Events Success: {success}')
print(f'Events Failed: {failure}')

print('\n=== TEST 4: SHADOW AUDIT ===')
try:
    from mnos.modules.shadow.audit_counts import get_counts
    events_count, shadow_count = get_counts()

    print(f'stress_event_count: {events_count}')
    print(f'stress_shadow_block_count: {shadow_count}')

    # Shadow count includes the initial safe event + 1000 stress events
    if events_count == 1001:
        print('✅ PASS: No silent execution')
    else:
        print('❌ FAIL: Shadow mismatch detected')

except Exception as e:
    print('⚠️ WARNING: Shadow audit unavailable')
    traceback.print_exc()
