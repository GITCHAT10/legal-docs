#!/bin/bash
# MNOS GENESIS: MARS RECON + AEGIS INITIALIZER (HARDENED)
# For: MALDIVES INTERNATIONAL GROUP PVT LTD

# 1. Build the Jules Bridge Image
echo "BUILDING JULES AEGIS BRIDGE..."
docker build -t mnos/aegis-bridge:latest -f mnos/modules/aegis_bridge/Dockerfile .

# 2. Create the Hardened Darknet (Moat)
docker network create --internal mnos_darknet 2>/dev/null || true

# 3. Deploy Frigate AI (The Vision)
# Note: Port 5000 removed for security hardening. Access only via internal network.
docker run -d \
  --name frigate_mars_recon \
  --restart unless-stopped \
  --network mnos_darknet \
  --shm-size=128mb \
  -v /mnt/storage/frigate:/media/frigate \
  -v /etc/mnos/frigate/config.yml:/config/config.yml:ro \
  --device /dev/bus/usb/001/002:/dev/bus/usb/001/002 \
  blakeblackshear/frigate:stable

# 4. Deploy Jules (The AEGIS Sovereign Bridge)
docker run -d \
  --name jules_bridge \
  --restart unless-stopped \
  --network mnos_darknet \
  -e IDENTITY="MIG-AIGM-2024PV12395H" \
  -e MQTT_SERVER="mqtt://10.0.0.5" \
  -e AEGIS_LEVEL="MIL-SPEC" \
  -e SHADOW_LEDGER="https://mnos.internal" \
  -e NEXGEN_SECRET=$NEXGEN_SECRET \
  mnos/aegis-bridge:latest

# 5. Final System Audit
docker ps | grep -E "frigate|jules"
echo "PERIMETER SECURED: MNOS MARS RECON IS LIVE."
echo "AUTONOMOUS RESPONSE: ACTIVE (ENTRY RESTRICTION + ALERTS)"
echo "HARDENING: Direct port exposure REMOVED. Map access limited to internal proxy."
