import os
import json
import time
import paho.mqtt.client as mqtt
from mnos.core.security.aegis import aegis
from mnos.modules.security.service import security_module
from mnos.config import config

IDENTITY = os.getenv("IDENTITY", "MIG-AIGM-2024PV12395H")
MQTT_SERVER = os.getenv("MQTT_SERVER", "mqtt://10.0.0.5")
AEGIS_LEVEL = os.getenv("AEGIS_LEVEL", "MIL-SPEC")

def get_signed_session_context():
    """Generates a signed session context for the bridge."""
    payload = {
        "device_id": IDENTITY,
        "role": "security_bridge"
    }
    # Securely sign the payload using AEGIS service
    signature = aegis.sign_session(payload)
    context = payload.copy()
    context["signature"] = signature
    return context

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"[Jules Bridge] Connected with result code {rc}")
    client.subscribe("frigate/events")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"[Jules Bridge] Received Frigate event: {payload.get('type')}")

        # 1. Prepare event data
        event_data = {
            "source": "frigate_mars_recon",
            "frigate_event": payload,
            "identity": IDENTITY,
            "aegis_level": AEGIS_LEVEL
        }

        # 2. Get fresh signed context for each submission
        session_context = get_signed_session_context()

        # 3. Hand over to Security Module for evaluation and action
        # This will route through ExecutionGuard -> AEGIS -> SHADOW
        security_module.process_security_event(event_data, session_context)

    except Exception as e:
        print(f"[Jules Bridge] Error processing message: {str(e)}")

def main():
    print(f"--- Jules AEGIS Sovereign Bridge Starting ---")
    print(f"Identity: {IDENTITY}")
    print(f"Server: {MQTT_SERVER}")

    # Parse MQTT Server
    host = MQTT_SERVER.replace("mqtt://", "").split(":")[0]
    port = 1883
    if ":" in MQTT_SERVER.replace("mqtt://", ""):
        port_str = MQTT_SERVER.split(":")[-1]
        if port_str.isdigit():
            port = int(port_str)

    # Use CallbackAPIVersion.VERSION2 for paho-mqtt 2.0+
    try:
        from paho.mqtt.enums import CallbackAPIVersion
        client = mqtt.Client(CallbackAPIVersion.VERSION2)
    except (ImportError, AttributeError):
        # Fallback for older paho-mqtt versions
        client = mqtt.Client()

    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            client.connect(host, port, 60)
            break
        except Exception as e:
            print(f"Connecting to MQTT failed ({e}), retrying in 5s...")
            time.sleep(5)

    client.loop_forever()

if __name__ == "__main__":
    main()
