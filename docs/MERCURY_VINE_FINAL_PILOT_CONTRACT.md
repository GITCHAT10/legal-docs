# MERCURY-VINE PILOT PILOT CONTRACT
**Status:** PILOT_SIGNABLE
**System:** MERCURY-VINE
**Mode:** PILOT_READY_CONTRACT

## 1. Scope and Scale
- **Deployment Atoll:** KAFAU_ATOLL_INITIAL_DEPLOYMENT
- **Participating Resorts:** LIMITED_PILOT_GROUP_5 (Exclusive Pilot Group)
- **Service Model:** GUARANTEED_AVAILABILITY_AS_A_SERVICE (GAaaS)

## 2. Phased Execution
- **PHASE 1:** PERISHABLES_ONLY (Initial supply chain stabilization)
- **PHASE 2:** FUEL_AND_CRITICAL_LOGISTICS (Energy and infrastructure support)
- **PHASE 3:** EXPANSION_OPTIONAL (Requires General Manager approval)

## 3. SKU Tiering and Coverage
- **TIER 1 (GUARANTEED_COVERAGE):** Essential items with mandatory airbridge backup.
- **TIER 2 (CONDITIONAL_COVERAGE):** Secondary items subject to asset availability.
- **TIER 3 (EXCLUDED_FROM_AIRBRIDGE):** Non-critical items restricted to standard logistics.

## 4. Airbridge Policy (Emergency Logistics)
- **Triggers:** WEATHER_RISK or PHANTOM_STOCKOUT (Deterministic AI detection).
- **Weight Limit:** MAX_WEIGHT_PER_EVENT: 500KG.
- **Funding:** 8_PERCENT_RESILIENCE_FEE_POOL.
- **Constraints:** NO_UNLIMITED_COVERAGE; usage capped by pool liquidity.

## 5. Service Level Agreement (SLA)
- **Stockout Prevention Target:** 95% Availability for Tier 1 SKUs.
- **Airbridge Delivery Window:** 24 HOURS from trigger confirmation.
- **Response Time:** 4 HOURS for system alerting and response planning.

## 6. Financial Model and Settlements
- **Resilience Fee:** 8% (Allocated to emergency logistics pool).
- **Standard Service Fee:** 2.5%.
- **Escrow Mechanism:** FCE-BASED_LOCK_AND_RELEASE (Atomic settlement).
- **Settlement Terms:** NET 30 TO 45 DAYS.

## 7. Tax and Compliance
- **TGST Rate:** 17% (Maldives Tourism Goods and Services Tax).
- **Calculation:** Automated real-time splitting via FCE.
- **Reporting:** Real-time integration with MIRA (Maldives Inland Revenue Authority).

## 8. Risk Controls and Safety
- **Fail-Safe:** FULL_ROLLBACK_ON_ERROR (No partial data state).
- **False Positive Limits:** AI threshold monitoring enabled.
- **Manual Override:** GM_APPROVAL_REQUIRED for all critical overrides.
- **Autonomy:** GRADUAL_ENABLEMENT_ONLY (System learns under supervision).

## 9. Legal and Audit
- **Jurisdiction:** ALIGNMENT WITH MALDIVES LAW.
- **Force Majeure:** WEATHER_EXCLUDED (Logistics pauses during extreme weather).
- **Audit Trail:** SHADOW_CHAIN_ENABLED (Immutable forensic evidence for every transaction).

---
**Permission Notice:** DENY_PRODUCTION deployment. This contract is for PILOT use cases only.
