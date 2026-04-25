# MNOS NEXTGEN + MARS EVENTS + TRANSPORT ENGINE

## Unified Schema Pack

### Status

Approved architecture pack for engineering handoff.

---

## 1. Canonical Scope

This pack defines the merged sovereign execution architecture for:

* **MARS EVENTS**
* **MARS EXPLORE**
* **MARS TRANSPORT ENGINE**
* **MARS NEXTGEN**
* **AEGIS**
* **ELEONE**
* **FCE**
* **SHADOW**
* **EVENTS bus**
* **MARS WALLET**

It formalizes the Maldives-specific doctrine:
**See it → Book it → Get there → Verify it → Return safely**

---

## 2. Primary Folder Layout

```text
platform/
  nextgen/
    ai_orchestrator/
    predictive_dispatch/
    biometric_gate/
    spatial_ar/
    ambient_identity/
    edge_sync/
    adapters/
    policies/

modules/
  experience/
    events/
  transport/
    engine/

interfaces/
  explore/
  events/
```

---

## 3. Core Doctrine

All state-changing operations must follow:

```text
PREDICT / VALIDATE
→ AEGIS AUTHZ
→ DOMAIN DECISION
→ HOLD RESOURCE
→ DB WRITE
→ FCE / TRANSPORT SIDE EFFECT
→ EVENTS EMIT
→ SHADOW COMMIT
→ EXECUTE
```

Fail closed if any of the following fail:

* AEGIS authorization
* transport hold or return-leg validation
* FCE settlement
* SHADOW commit
* policy threshold / confidence minimum

---

## 4. Unified Database Tables

### Organizers / Venues / Events

#### event_organizers

* id
* tenant_id
* name
* legal_name
* organizer_type
* aegis_subject_id
* kyb_status
* commission_profile_id
* payout_config_json
* status
* created_at
* updated_at

#### venues

* id
* tenant_id
* name
* venue_type
* island
* atoll
* latitude
* longitude
* capacity
* transport_required
* metadata_json

#### events

* id
* tenant_id
* organizer_id
* venue_id
* title
* slug
* description
* category
* start_at
* end_at
* timezone
* visibility
* publication_status
* base_capacity
* effective_capacity
* transport_mode
* transport_link_required
* currency
* tax_config_mira_json
* status
* trace_id
* version
* created_by
* created_at
* updated_at

#### ticket_tiers

* id
* tenant_id
* event_id
* name
* description
* base_price
* inventory_limit
* per_user_limit
* sale_start_at
* sale_end_at
* status

---

### Orders / Tickets / Wallet Passes

#### ticket_orders

* id
* tenant_id
* buyer_aegis_id
* event_id
* order_status
* currency
* subtotal
* service_charge_total
* tgst_total
* grand_total
* wallet_applied_amount
* payment_reference
* fce_invoice_id
* trace_id
* created_at

#### tickets

* id
* tenant_id
* order_id
* event_id
* ticket_tier_id
* holder_aegis_id
* wallet_asset_id
* qr_payload_hash
* ticket_status
* issued_at
* refunded_at
* checked_in_at
* transfer_locked
* trace_id

#### wallet_master_passes

* id
* tenant_id
* wallet_asset_id
* ticket_id
* outbound_boarding_ref
* return_boarding_ref
* qr_payload_hash
* pass_status
* issued_at
* updated_at

---

### Transport-linked Inventory

#### event_transport_bundles

* id
* tenant_id
* event_id
* route_id
* outbound_departure_id
* return_departure_id
* vessel_id
* reserved_capacity
* sold_capacity
* buffer_locked_capacity
* release_policy_json
* bundle_status
* trace_id
* created_at
* updated_at

#### transport_capacity_snapshots

* id
* tenant_id
* route_id
* departure_id
* vessel_id
* total_capacity
* available_capacity
* held_capacity
* sold_capacity
* emergency_buffer_capacity
* captured_at

#### transport_links

* id
* tenant_id
* ticket_id
* event_id
* route_id
* outbound_departure_id
* return_departure_id
* manifest_id
* seat_reference
* boarding_status
* transport_status
* linked_at
* trace_id

#### manifests

* id
* tenant_id
* route_id
* departure_id
* event_id
* vessel_id
* manifest_status
* departure_window
* generated_at
* updated_at

---

### Attendance / Offline / Audit Assist

#### attendance_scans

* id
* tenant_id
* ticket_id
* event_id
* scanner_aegis_id
* device_id
* scan_mode
* scan_result
* scanned_at
* offline_batch_id
* trace_id

#### offline_sync_batches

* id
* tenant_id
* device_id
* batch_status
* payload_hash
* received_at
* committed_at

#### edge_sync_conflicts

* id
* tenant_id
* resource_type
* resource_id
* device_id
* conflict_type
* resolution_status
* trace_id
* created_at

---

### NEXTGEN Intelligence Tables

#### predictive_dispatch_jobs

* id
* tenant_id
* user_id
* event_id
* route_id
* departure_window
* dispatch_type
* confidence_score
* policy_basis_json
* status
* trace_id
* created_at

#### ghost_booking_holds

* id
* tenant_id
* user_id
* event_id
* transport_reservation_id
* hold_reason
* confidence_score
* expires_at
* status
* trace_id

#### biometric_gate_events

* id
* tenant_id
* subject_id
* gate_id
* verification_mode
* device_id
* decision
* fallback_used
* trace_id
* created_at

#### spatial_pulses

* id
* tenant_id
* event_id
* venue_id
* lat
* lng
* pulse_strength
* occupancy_hint
* vibe_score
* reachability_score
* weather_hint
* boat_eta_hint
* updated_at

#### policy_buffer_locks

* id
* tenant_id
* event_id
* route_id
* locked_percentage
* locked_capacity
* release_at
* release_policy_json
* status

---

## 5. Inventory Rule

```text
sellable_inventory = min(
  event_capacity,
  outbound_transport_capacity,
  return_transport_capacity
) - active_buffer_lock
```

If no safe return leg exists, bundle purchase must fail.

---

## 6. API Contract Pack

### Explore / Discovery

* GET /v1/explore/events/live
* GET /v1/explore/events/{event_id}
* GET /v1/explore/events/{event_id}/logistics
* GET /v1/explore/ar/pulses
* GET /v1/explore/ar/reachability/{event_id}

### Availability / Handshake

* GET /v1/transport/sync/availability
* GET /v1/transport/event-logistics/{event_id}

### Bundle Execution

* POST /v1/events/book-bundle
* POST /v1/events/bundle/execute

### Ticket / Wallet

* GET /v1/tickets/{ticket_id}
* POST /v1/tickets/{ticket_id}/refund
* POST /v1/tickets/{ticket_id}/transfer
* GET /v1/wallet/master-pass/{ticket_id}

### Attendance / Gate

* POST /v1/attendance/scan
* POST /v1/attendance/offline-batch
* POST /v1/nextgen/gate/verify
* POST /v1/nextgen/gate/offline-verify
* POST /v1/nextgen/gate/override

### Predictive / Dispatch

* POST /v1/nextgen/predict/dispatch
* POST /v1/nextgen/dispatch/execute
* POST /v1/transport/predictive-hold
* POST /v1/transport/ghost-book
* POST /v1/transport/release-prediction
* GET /v1/transport/dispatch-groups/{event_id}

### Transport Ops

* GET /v1/events/{event_id}/manifests
* POST /v1/transport/manifests/{manifest_id}/confirm-boarding
* WEBHOOK /v1/transport/manifest/update

---

## 7. Required Headers

* X-MARS-AEGIS-AUTH
* X-FCE-BILLING-ID
* X-TRACE-ID
* X-TENANT-ID

---

## 8. Bundle Execute Payload

```json
{
  "event_id": "EVT-882",
  "transport": {
    "route_id": "RT-MAL-CROSS",
    "vessel_preference": "luxury_speed_ferry",
    "departure_window": "19:00-19:30",
    "return_required": true
  },
  "wallet_id": "WAL-9920",
  "insurance_opt_in": true,
  "trace_id": "TRACE-123"
}
```

---

## 9. NEXTGEN Service Responsibilities

### ai_orchestrator

* event schedule aggregation
* demand prediction
* route suggestion
* confidence scoring
* anomaly detection

### predictive_dispatch

* pre-hold transport
* build dispatch groups
* release unused holds
* manage policy buffer

### biometric_gate

* biometric verification
* device trust check
* wallet fallback
* offline gate validation
* override routing

### spatial_ar

* event pulse feeds
* reachability overlays
* occupancy / vibe overlays
* logistics hints

### edge_sync

* offline queue handling
* delayed SHADOW sync
* conflict resolution
* device state integrity

---

## 10. Maldives Finance Rule

```text
Base Price
+ 10% Service Charge
= Subtotal

TGST = 17% of Subtotal
Grand Total = Subtotal + TGST
```

All settlement must route through FCE.

---

## 11. Jules Build Command

```text
jules upgrade --platform MARS \
  --enable-nextgen-layer \
  --enable-predictive-sync \
  --enable-ghost-booking \
  --inject-spatial-engine \
  --apply-biometric-gate \
  --enable-edge-sync \
  --target maldives_archipelago_v2 \
  --paths platform/nextgen,modules/experience/events,interfaces/explore,modules/transport/engine
```

---

## 12. Engineering Acceptance Tests

* live explore pulse response valid
* availability check returns transport token
* successful bundle booking with outbound + return seat
* booking blocked when no return leg exists
* inventory throttled by transport capacity
* 15% buffer lock enforced
* biometric gate success with wallet fallback
* duplicate scan blocked
* offline scan sync committed
* unauthorized scanner rejected
* predictive hold released correctly
* SHADOW failure rolls back transaction
* tenant isolation preserved

---

## 13. Final Decision

This pack is the canonical handoff for the merged **NEXTGEN + EVENTS + TRANSPORT ENGINE** architecture.

It should be used as the base reference for:

* schema generation
* API implementation
* Jules build automation
* test planning
* integration doctrine
