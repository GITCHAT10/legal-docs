# FCE Settlement Logic v1.1

## Rules
1. No settlement without schema v1.1 validation.
2. No settlement without namespace validation.
3. No tenant settlement without full context.
4. No final settlement without SHADOW proof.
5. Maldives tax waterfall enforcement.
6. Idempotency protection.

## Maldives Tax Rule
- Base Price
- + 10% Service Charge
- = Taxable Subtotal
- + 17% TGST on Taxable Subtotal
- = Customer Total
