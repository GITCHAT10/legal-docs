# Prestige Social Command: FCE Quote Bridge Module

## Doctrine
- **AI qualifies intent.** (Collects dates, guests, preferences, budget signal)
- **FCE verifies price.** (Calculates exact quote using Maldives 2026 rules)
- **Human closes trust.** (Human Sales Desk reviews and sends verified quote via WhatsApp)
- **SHADOW proves revenue.** (Every action is sealed in an immutable audit chain)

## Maldives 2026 Pricing Rules
- **Service Charge:** 10% (Mandatory)
- **TGST:** 17% (Locked, 16% is blocked)
- **Green Tax:**
  - USD 12/guest/night for resorts/vessels/hotels.
  - USD 6/guest/night for small inhabited-island guesthouses (<= 50 rooms).
  - Infants under 2 are exempt.

## Module Structure
- `quote_bridge/`: Core logic for pricing waterfall and FCE connection.
- `sales_desk/`: Human Sales Desk lead card models and actions.
- `api/`: REST endpoints for quote requests and lead management.
- `audit/`: SHADOW event generation and hashing.

## Key Guards
- AI cannot send exact prices or availability.
- Human cannot send unverified or failed quotes.
- 16% TGST results in `INVALID_TGST_RATE_2026` error.
- Manual price overrides require manager approval (logged in SHADOW).

## API Endpoints
- `POST /fce/quotes/request`: Request a new quote.
- `POST /fce/quotes/{id}/verify`: System verification of a quote.
- `POST /social/leads/{id}/send-quote`: Human action to send a verified quote.
- `GET /social/leads/{id}/shadow-chain`: Retrieve the full audit trail.

## Staging & MVP
This module uses mocked resort contract rates (`MOCK_RESORTS` in `quote_rules.py`) for staging verification.
