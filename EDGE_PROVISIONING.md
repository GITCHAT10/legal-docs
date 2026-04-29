# 📦 MARS EDGE: Device Provisioning Checklist

## 1. Hardware Inspection
- [ ] Inspect for physical damage (screen, ports, chassis).
- [ ] Verify battery health and charging cycle.
- [ ] Label with unique Asset ID and QR code.

## 2. OS & Security Hardening
- [ ] Flash **MNOS-EDGE-Kiosk v1.2** image.
- [ ] Enable **Secure Boot** and hardware encryption (AES-256).
- [ ] Disable USB debugging and unauthorized wireless protocols.
- [ ] Configure **Mobile Device Management (MDM)** profile.

## 3. Software Deployment
- [ ] Install **AIRMOVIE Player Core**.
- [ ] Install **MARS Academy LMS** (Mini-App).
- [ ] Provision **AEGIS Device Binding** key.
- [ ] Configure local **IndexedDB** for offline queueing.

## 4. Content Pre-loading
- [ ] Load **L1 Foundation Pack** (Service, HACCP, FO, HK, Emergency).
- [ ] Verify SHA-256 checksums for all pre-loaded videos.
- [ ] Test multi-language playback (Dhivehi/English).

## 5. Network & Sync Test
- [ ] Perform speed test on resort IoT VLAN.
- [ ] Simulate 4h offline period and verify auto-sync.
- [ ] Confirm SHADOW ledger anchoring from EDGE.
