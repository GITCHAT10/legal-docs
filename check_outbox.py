with open('skyfarm/integration/outbox_worker.py', 'r') as f:
    content = f.read()
print(f"Retry Strategy: {'Retry(' in content}")
print(f"Timeout: {'timeout=5' in content}")
