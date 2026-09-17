# 🏗️ iMOXON Production Deployment Architecture (Maldives-Ready)

## 1. Multi-Tier Governance Stack
- **Edge Dome (Cloudflare/Akamai):** WAF, DDoS protection, and Maldives-region IP filtering.
- **API Gateway (Kong/Nginx):** JWT validation and request tracing.
- **Sovereign Mesh (Kubernetes):** Auto-scaling pods for individual iMOXON engines.
- **Authority Core:** Dedicated isolated cluster for MNOS (AEGIS, FCE, SHADOW).

## 2. Infrastructure Deployment
- **Primary Region:** NCIT Government Cloud (Male).
- **Secondary Region:** Private Cloud (Hulhumale Data Center).
- **Atoll Edge Nodes:** Lightweight cache/CDN nodes in Addu and Kulhudhuffushi for 5G low-latency Move/Food delivery flows.

## 3. Data Residency & Sovereignty
- **Primary Database:** PostgreSQL Cluster with Citus for multi-tenant scalability (Atoll-based sharding).
- **Audit Ledger:** SHADOW logs replicated to write-once-read-many (WORM) storage for immutable legal evidence.
- **PII Storage:** Encrypted using AES-256 with keys managed by NCIT-approved HSM.

## 4. Scaling Strategy
- **MOVE & FOOD:** Horizontal scaling based on geo-traffic spikes.
- **FINANCE & HOMES:** Vertical scaling with high-consistency transactional locks.
- **LOGS:** Async streaming to an elastic search cluster for real-time monitoring.

## 5. Security Boundaries
- **Zone 1 (Public):** UI and Onboarding endpoints.
- **Zone 2 (Internal):** Engines communicating via gRPC/mTLS.
- **Zone 3 (Restricted):** FCE and SHADOW database access (VPC Peering only).
