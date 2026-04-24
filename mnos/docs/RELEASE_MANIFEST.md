# NEXUS ASI SKY-i OS — RELEASE MANIFEST (RC1)

## 📦 Core Modules
- `mnos/config.py`: System-wide sovereign configurations.
- `mnos/boot_check.py`: Startup integrity validation.
- `mnos/core/security/aegis.py`: Identity & session authority.
- `mnos/modules/fce/service.py`: Financial Control Engine (MIRA compliant).
- `mnos/modules/shadow/service.py`: Immutable Evidence Chain.
- `mnos/core/events/service.py`: Orchestration Hub.

## 🧠 Intelligence Layer
- `mnos/modules/knowledge/service.py`: SKY-i Knowledge Core.
- `mnos.core.asi.silvia.py`: Silvia Intelligence Engine.

## 📲 Interfaces & Workflows
- `mnos/interfaces/sky_i/comms/whatsapp.py`: WhatsApp Intelligence Loop.
- `mnos/modules/workflows/booking.py`: Booking -> Payment flow.
- `mnos/modules/workflows/guest_arrival.py`: Autonomous Arrival flow.
- `mnos/modules/workflows/emergency.py`: Emergency Response flow.

## 🛠️ Verification Tools
- `mnos/validate_system.py`: End-to-end simulation.
- `mnos/stress_test.py`: Hardening verification.
